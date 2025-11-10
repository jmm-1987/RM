from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from markupsafe import Markup
from models import (
    db,
    Zona,
    Cliente,
    MensajePlantilla,
    MensajeEnviado,
    Oferta,
    MensajeOferta,
    MensajeRecibido,
    RespuestaMensaje,
    ProgramacionMasiva,
    WhatsAppConversation,
    WhatsAppMessage,
)
from whatsapp_sender import enviar_whatsapp, configurar_green_api, green_api_sender
from datetime import datetime, date, timezone
import os
import threading
import time as _time
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración general (siempre SQLite por defecto)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///recambios.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('DEBUG', 'True').lower() == 'true'

# Configuración común
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crear directorio de uploads si no existe  
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Variable para controlar la inicialización
_sistema_inicializado = False
_scheduler_iniciado = False


def _chat_display(value: str) -> str:
    if not value:
        return ""
    if value.endswith("@c.us") or value.endswith("@s.whatsapp.net"):
        return value.split("@", 1)[0]
    return value


def _normalize_chat_id(raw_number: str) -> str:
    if not raw_number:
        raise ValueError("El número de WhatsApp no puede estar vacío")

    raw_number = raw_number.strip()
    if "@" in raw_number:
        return raw_number

    digits = "".join(filter(str.isdigit, raw_number))
    if not digits:
        raise ValueError("El número de WhatsApp debe contener al menos un dígito")

    if digits.startswith("6") and len(digits) == 9:
        digits = "34" + digits
    elif digits.startswith("600") and len(digits) == 12:
        digits = "34" + digits[1:]

    return f"{digits}@c.us"


def _green_api_credentials():
    api_url = getattr(green_api_sender, "api_url", None)
    api_token = getattr(green_api_sender, "api_token", None)
    instance_id = getattr(green_api_sender, "instance_id", None)

    if green_api_sender.simulate_mode or not all([api_url, api_token, instance_id]):
        raise RuntimeError("Green-API no está configurado para envíos reales")

    return api_url, api_token, instance_id


def _send_green_api_message(chat_id: str, message: str) -> str | None:
    api_url, api_token, instance_id = _green_api_credentials()
    normalized_chat_id = _normalize_chat_id(chat_id)
    url = f"{api_url}/waInstance{instance_id}/sendMessage/{api_token}"
    response = requests.post(
        url,
        json={"chatId": normalized_chat_id, "message": message},
        timeout=30,
    )
    response.raise_for_status()

    if response.headers.get("content-type", "").startswith("application/json"):
        data = response.json()
        return data.get("idMessage")
    return None


def _fetch_green_api_contacts() -> list[dict]:
    api_url, api_token, instance_id = _green_api_credentials()
    url = f"{api_url}/waInstance{instance_id}/getContacts/{api_token}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    contacts = data.get("contacts") if isinstance(data, dict) else None
    if contacts is None:
        raise ValueError("Respuesta inesperada al solicitar contactos en Green-API")
    return contacts


def _ensure_whatsapp_conversation(chat_id: str, contact_name: str | None = None, created_at: datetime | None = None) -> WhatsAppConversation:
    chat_id = _normalize_chat_id(chat_id)
    conversation = WhatsAppConversation.query.filter_by(contact_number=chat_id).first()
    timestamp = created_at or datetime.utcnow()

    if not conversation:
        conversation = WhatsAppConversation(
            contact_number=chat_id,
            contact_name=contact_name,
            created_at=timestamp,
            updated_at=timestamp,
        )
        db.session.add(conversation)
        db.session.flush()
    else:
        if contact_name and not conversation.contact_name:
            conversation.contact_name = contact_name

    conversation.updated_at = datetime.utcnow()
    return conversation


def _append_whatsapp_message(
    conversation: WhatsAppConversation,
    sender_type: str,
    message_text: str,
    sent_at: datetime | None = None,
    external_id: str | None = None,
    is_read: bool = True,
) -> WhatsAppMessage:
    message = WhatsAppMessage(
        conversation_id=conversation.id,
        sender_type=sender_type,
        message_text=message_text,
        sent_at=sent_at or datetime.utcnow(),
        external_id=external_id,
        is_read=is_read,
    )
    conversation.updated_at = datetime.utcnow()
    db.session.add(message)
    return message


def _register_incoming_whatsapp_message(
    chat_id: str,
    message_text: str,
    contact_name: str | None = None,
    sent_at: datetime | None = None,
    external_id: str | None = None,
):
    conversation = _ensure_whatsapp_conversation(chat_id, contact_name, sent_at)
    _append_whatsapp_message(
        conversation,
        sender_type="customer",
        message_text=message_text,
        sent_at=sent_at,
        external_id=external_id,
        is_read=False,
    )


def _register_outgoing_whatsapp_message(
    chat_id: str,
    message_text: str,
    sent_at: datetime | None = None,
    external_id: str | None = None,
):
    conversation = _ensure_whatsapp_conversation(chat_id)
    _append_whatsapp_message(
        conversation,
        sender_type="agent",
        message_text=message_text,
        sent_at=sent_at,
        external_id=external_id,
        is_read=True,
    )


def _conversation_to_dict(conversation: WhatsAppConversation) -> dict:
    last = conversation.last_message()
    return {
        "id": conversation.id,
        "display_name": conversation.contact_name or _chat_display(conversation.contact_number),
        "contact_number": conversation.contact_number,
        "last_message_text": last.message_text if last else "",
        "last_message_sender": last.sender_type if last else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "updated_at_human": conversation.updated_at.strftime("%d/%m/%Y %H:%M") if conversation.updated_at else "",
        "unread_count": conversation.unread_count(),
        "url": url_for("whatsapp_conversation_detail", conversation_id=conversation.id),
    }


def _message_to_dict(message: WhatsAppMessage) -> dict:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_type": message.sender_type,
        "message_text": message.message_text,
        "sent_at": message.sent_at.isoformat() if message.sent_at else None,
        "sent_at_human": message.sent_at.strftime("%d/%m/%Y %H:%M") if message.sent_at else "",
        "is_read": message.is_read,
    }


@app.template_filter("nl2br")
def nl2br_filter(value: str | None) -> Markup:
    if value is None:
        return Markup("")
    return Markup(str(value).replace("\n", "<br>"))


@app.template_filter("chat_display")
def chat_display_filter(value: str | None) -> str:
    return _chat_display(value)


def _ejecutor_programaciones():
    """Hilo en background que ejecuta envíos masivos programados por zona y hora."""
    with app.app_context():
        while True:
            ahora = datetime.now()
            dia_semana = ahora.weekday()  # 0=Lunes ... 6=Domingo
            hora_actual = ahora.strftime('%H:%M')

            try:
                programaciones = ProgramacionMasiva.query.filter_by(activo=True).all()
                for prog in programaciones:
                    # Verificar día
                    dias = {int(d) for d in prog.dias_semana.split(',') if d.strip()}
                    if dia_semana not in dias:
                        continue

                    # Verificar hora exacta (minuto)
                    if prog.hora != hora_actual:
                        continue

                    # Evitar ejecutar más de una vez por día
                    if prog.ultima_ejecucion == date.today():
                        continue

                    # Ejecutar envío para la zona
                    zona = Zona.query.get(prog.zona_id)
                    plantilla = MensajePlantilla.query.get(prog.plantilla_id)
                    if not zona or not plantilla:
                        continue

                    clientes = Cliente.query.filter(
                        Cliente.zona_id == prog.zona_id,
                        Cliente.activo == True
                    ).all()

                    for cliente in clientes:
                        enlace_web = generar_enlace_web()
                        mensaje_personalizado = plantilla.contenido.format(
                            nombre_cliente=cliente.nombre,
                            zona=zona.nombre,
                            enlace_web=enlace_web
                        )

                        success, error_msg = green_api_sender.send_message(cliente.telefono, mensaje_personalizado)

                        if success:
                            try:
                                _register_outgoing_whatsapp_message(
                                    cliente.telefono,
                                    mensaje_personalizado,
                                    sent_at=datetime.now(timezone.utc)
                                )
                            except Exception as exc:  # noqa: BLE001
                                print(f"⚠️ No se pudo registrar la conversación avanzada: {exc}")

                        registro = MensajeEnviado(
                            cliente_id=cliente.id,
                            plantilla_id=plantilla.id,
                            mensaje_final=mensaje_personalizado,
                            enviado=success,
                            fecha_envio=datetime.now(timezone.utc) if success else None,
                            error=error_msg if not success else None
                        )
                        db.session.add(registro)

                    # Marcar ejecución del día y confirmar
                    prog.ultima_ejecucion = date.today()
                    db.session.commit()

            except Exception as e:
                # Evitar que el hilo muera por excepciones
                print(f"❌ Error en ejecutor de programaciones: {e}")

            # Dormir hasta el siguiente minuto
            _time.sleep(30)


def _iniciar_hilo_programaciones():
    hilo = threading.Thread(target=_ejecutor_programaciones, name='ejecutor_programaciones', daemon=True)
    hilo.start()


@app.before_request
def _asegurar_scheduler():
    global _scheduler_iniciado
    if not _scheduler_iniciado:
        try:
            _iniciar_hilo_programaciones()
            _scheduler_iniciado = True
            print("⏰ Scheduler de programaciones iniciado")
        except Exception as e:
            print(f"❌ No se pudo iniciar el scheduler: {e}")

def migrar_sqlite_a_postgres():
    """Migrga datos de SQLite local a PostgreSQL en producción"""
    try:
        import sqlite3
        import psycopg2
        
        # Verificar si existe la base de datos SQLite local
        if not os.path.exists('recambios.db'):
            print("ℹ️ No hay base de fdatos SQLite local para migrar")
            return True
        
        # Conectar a SQLite local
        sqlite_conn = sqlite3.connect('recambios.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conectar a PostgreSQL
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        postgres_conn = psycopg2.connect(database_url)
        postgres_cursor = postgres_conn.cursor()
        
        print("📝 Migrando datos de SQLite a PostgreSQL...")
        
        # Migrar zonas
        sqlite_cursor.execute("SELECT id, nombre, descripcion FROM zona")
        zonas = sqlite_cursor.fetchall()
        for zona in zonas:
            postgres_cursor.execute(
                "INSERT INTO zona (id, nombre, descripcion) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                zona
            )
        
        # Migrar clientes
        sqlite_cursor.execute("SELECT id, nombre, telefono, zona_id, activo FROM cliente")
        clientes = sqlite_cursor.fetchall()
        for cliente in clientes:
            postgres_cursor.execute(
                "INSERT INTO cliente (id, nombre, telefono, zona_id, activo) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                cliente
            )
        
        # Migrar plantillas
        sqlite_cursor.execute("SELECT id, nombre, contenido FROM mensaje_plantilla")
        plantillas = sqlite_cursor.fetchall()
        for plantilla in plantillas:
            postgres_cursor.execute(
                "INSERT INTO mensaje_plantilla (id, nombre, contenido) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                plantilla
            )
        
        # Migrar ofertas
        sqlite_cursor.execute("SELECT id, titulo, descripcion, precio, imagen, activa, destacada, created_at, updated_at FROM oferta")
        ofertas = sqlite_cursor.fetchall()
        for oferta in ofertas:
            postgres_cursor.execute(
                "INSERT INTO oferta (id, titulo, descripcion, precio, imagen, activa, destacada, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                oferta
            )
        
        # Migrar mensajes enviados
        sqlite_cursor.execute("SELECT id, cliente_id, plantilla_id, mensaje_personalizado, mensaje_enviado, fecha_envio, error FROM mensaje_enviado")
        mensajes = sqlite_cursor.fetchall()
        for mensaje in mensajes:
            postgres_cursor.execute(
                "INSERT INTO mensaje_enviado (id, cliente_id, plantilla_id, mensaje_personalizado, mensaje_enviado, fecha_envio, error) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                mensaje
            )
        
        # Migrar mensajes de ofertas
        sqlite_cursor.execute("SELECT id, cliente_id, oferta_id, mensaje_personalizado, imagen_enviada, mensaje_enviado, fecha_envio, error FROM mensaje_oferta")
        mensajes_ofertas = sqlite_cursor.fetchall()
        for mensaje_oferta in mensajes_ofertas:
            postgres_cursor.execute(
                "INSERT INTO mensaje_oferta (id, cliente_id, oferta_id, mensaje_personalizado, imagen_enviada, mensaje_enviado, fecha_envio, error) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                mensaje_oferta
            )
        
        postgres_conn.commit()
        print("✅ Migración completada exitosamente!")
        print(f"- Zonas: {len(zonas)}, Clientes: {len(clientes)}, Plantillas: {len(plantillas)}")
        print(f"- Ofertas: {len(ofertas)}, Mensajes: {len(mensajes)}, Mensajes Ofertas: {len(mensajes_ofertas)}")
        
        sqlite_conn.close()
        postgres_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        return False

def inicializar_sistema():
    """Inicializa la base de datos y datos de ejemplo si es necesario"""
    global _sistema_inicializado
    
    if _sistema_inicializado:
        return
        
    try:
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya hay datos
        if not Zona.query.first():
            print("📝 Inicializando base de datos con datos de ejemplo...")
            
            # Crear zonas básicas
            zonas_data = [
                {'nombre': 'Centro', 'descripcion': 'Zona centro de la ciudad'},
                {'nombre': 'Norte', 'descripcion': 'Zona norte de la ciudad'},
                {'nombre': 'Sur', 'descripcion': 'Zona sur de la ciudad'},
                {'nombre': 'Este', 'descripcion': 'Zona este de la ciudad'},
                {'nombre': 'Oeste', 'descripcion': 'Zona oeste de la ciudad'}
            ]
            
            for zona_data in zonas_data:
                zona = Zona(**zona_data)
                db.session.add(zona)
            
            # Crear plantillas de mensajes
            plantillas_data = [
                {
                    'nombre': 'Visita Programada',
                    'contenido': 'Hola {nombre_cliente}, somos de Recambios RM. Vamos a pasar por la zona {zona} mañana por la mañana. ¿Necesitas algún recambio específico? Te podemos llevar lo que necesitas. ¡Gracias!'
                },
                {
                    'nombre': 'Recordatorio de Visita',
                    'contenido': 'Buenos días {nombre_cliente}, recordatorio: pasaremos por {zona} hoy por la tarde. Si necesitas algún recambio, avísanos antes de las 14:00. ¡Hasta pronto!'
                },
                {
                    'nombre': 'Promoción Especial',
                    'contenido': 'Hola {nombre_cliente}, tenemos una promoción especial esta semana. Pasaremos por {zona} con descuentos en recambios de motor. ¡No te lo pierdas!'
                }
            ]
            
            for plantilla_data in plantillas_data:
                plantilla = MensajePlantilla(**plantilla_data)
                db.session.add(plantilla)
            
            # Crear ofertas de ejemplo
            ofertas_data = [
                {
                    'titulo': 'Aceite de Motor Premium',
                    'descripcion': 'Aceite de motor de alta calidad para tu vehículo. Garantiza un rendimiento óptimo y protección del motor.',
                    'precio': 25.99,
                    'activa': True,
                    'destacada': True
                },
                {
                    'titulo': 'Filtro de Aire',
                    'descripcion': 'Filtro de aire original para mantener el motor limpio y eficiente.',
                    'precio': 12.50,
                    'activa': True,
                    'destacada': False
                },
                {
                    'titulo': 'Pastillas de Freno',
                    'descripcion': 'Pastillas de freno de alta calidad para una frenada segura y eficiente.',
                    'precio': 45.00,
                    'activa': True,
                    'destacada': True
                }
            ]
            
            for oferta_data in ofertas_data:
                oferta = Oferta(**oferta_data)
                db.session.add(oferta)
            
            db.session.commit()
            print("✅ Sistema inicializado exitosamente!")
            print(f"- {len(zonas_data)} zonas creadas")
            print(f"- {len(plantillas_data)} plantillas de mensajes creadas")
            print(f"- {len(ofertas_data)} ofertas de ejemplo creadas")
        else:
            print("✅ Sistema ya inicializado")
        
        _sistema_inicializado = True
            
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        db.session.rollback()

def check_database_initialized():
    """Verifica si la base de datos está inicializada"""
    try:
        # Intentar hacer una consulta simple
        Zona.query.first()
        return True
    except Exception:
        return False

@app.before_request
def before_request():
    """Middleware que inicializa automáticamente la base de datos"""
    global _sistema_inicializado
    
    # Solo inicializar una vez y solo en producción
    if not _sistema_inicializado and not app.config['DEBUG']:
        inicializar_sistema()

def generar_enlace_web():
    """Genera el enlace completo a la web pública de ofertas"""
    if os.environ.get('RENDER'):
        # En producción, usar la URL de Render
        dominio = os.environ.get('RENDER_EXTERNAL_URL', request.url_root.rstrip('/'))
    else:
        # En desarrollo local
        dominio = request.url_root.rstrip('/')
    
    return f"{dominio}{url_for('ofertas_publicas')}"

@app.route('/')
def index():
    ofertas_destacadas = Oferta.query.filter_by(activa=True, destacada=True).order_by(Oferta.created_at.desc()).limit(3).all()
    ofertas_normales = Oferta.query.filter_by(activa=True, destacada=False).order_by(Oferta.created_at.desc()).limit(6).all()
    return render_template('index.html', ofertas_destacadas=ofertas_destacadas, ofertas_normales=ofertas_normales)

@app.route('/clientes')
def clientes():
    zona_id = request.args.get('zona_id', type=int)
    if zona_id:
        clientes = Cliente.query.filter_by(zona_id=zona_id, activo=True).all()
    else:
        clientes = Cliente.query.filter_by(activo=True).all()
    
    zonas = Zona.query.all()
    return render_template('clientes.html', clientes=clientes, zonas=zonas, zona_seleccionada=zona_id)

@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    
    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.telefono = request.form.get('telefono')
        cliente.zona_id = request.form.get('zona_id', type=int)
        
        if not cliente.nombre or not cliente.telefono or not cliente.zona_id:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('editar_cliente', cliente_id=cliente_id))
        
        try:
            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando cliente: {str(e)}', 'error')
            return redirect(url_for('editar_cliente', cliente_id=cliente_id))
    
    zonas = Zona.query.all()
    return render_template('editar_cliente.html', cliente=cliente, zonas=zonas)

@app.route('/clientes/eliminar/<int:cliente_id>', methods=['POST'])
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    
    try:
        # En lugar de eliminar, marcar como inactivo
        cliente.activo = False
        db.session.commit()
        flash(f'Cliente {cliente.nombre} desactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error desactivando cliente: {str(e)}', 'error')
    
    return redirect(url_for('clientes'))

@app.route('/zonas')
def zonas():
    zonas = Zona.query.all()
    return render_template('zonas.html', zonas=zonas)

@app.route('/zonas/editar/<int:zona_id>', methods=['GET', 'POST'])
def editar_zona(zona_id):
    zona = Zona.query.get_or_404(zona_id)
    
    if request.method == 'POST':
        zona.nombre = request.form.get('nombre')
        zona.descripcion = request.form.get('descripcion')
        
        if not zona.nombre:
            flash('El nombre de la zona es obligatorio', 'error')
            return redirect(url_for('editar_zona', zona_id=zona_id))
        
        try:
            db.session.commit()
            flash('Zona actualizada exitosamente', 'success')
            return redirect(url_for('zonas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando zona: {str(e)}', 'error')
            return redirect(url_for('editar_zona', zona_id=zona_id))
    
    return render_template('editar_zona.html', zona=zona)

@app.route('/zonas/eliminar/<int:zona_id>', methods=['POST'])
def eliminar_zona(zona_id):
    zona = Zona.query.get_or_404(zona_id)
    
    # Verificar si hay clientes en esta zona
    clientes_en_zona = Cliente.query.filter_by(zona_id=zona_id, activo=True).count()
    
    if clientes_en_zona > 0:
        flash(f'No se puede eliminar la zona {zona.nombre} porque tiene {clientes_en_zona} cliente(s) activo(s)', 'error')
        return redirect(url_for('zonas'))
    
    try:
        db.session.delete(zona)
        db.session.commit()
        flash(f'Zona {zona.nombre} eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error eliminando zona: {str(e)}', 'error')
    
    return redirect(url_for('zonas'))

@app.route('/actualizar-plantillas-con-enlace')
def actualizar_plantillas_con_enlace():
    """Ruta temporal para actualizar las plantillas existentes con el enlace web"""
    try:
        plantillas = MensajePlantilla.query.all()
        actualizadas = 0
        
        for plantilla in plantillas:
            # Solo actualizar si no tiene el enlace web
            if '{enlace_web}' not in plantilla.contenido:
                if 'Visita Programada' in plantilla.nombre:
                    plantilla.contenido += '\n\n🌐 Consulta nuestras ofertas actuales: {enlace_web}'
                elif 'Recordatorio' in plantilla.nombre:
                    plantilla.contenido += '\n\n🌐 Ve nuestras ofertas: {enlace_web}'
                elif 'Promoción' in plantilla.nombre:
                    plantilla.contenido += '\n\n🌐 Descubre todas nuestras ofertas: {enlace_web}'
                else:
                    plantilla.contenido += '\n\n🌐 Consulta nuestras ofertas: {enlace_web}'
                
                actualizadas += 1
        
        db.session.commit()
        flash(f'Se actualizaron {actualizadas} plantillas con el enlace web', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error actualizando plantillas: {str(e)}', 'error')
    
    return redirect(url_for('mensajes'))

@app.route('/mensajes')
def mensajes():
    plantillas = MensajePlantilla.query.filter_by(activo=True).all()
    return render_template('mensajes.html', plantillas=plantillas)

@app.route('/enviar_masivo', methods=['GET', 'POST'])
def enviar_masivo():
    if request.method == 'POST':
        zona_id = request.form.get('zona_id')
        plantilla_id = request.form.get('plantilla_id')
        destinatarios_seleccionados = request.form.get('destinatarios_seleccionados', '')
        
        if not zona_id or not plantilla_id:
            flash('Debe seleccionar una zona y una plantilla de mensaje', 'error')
            return redirect(url_for('enviar_masivo'))

        if not destinatarios_seleccionados:
            flash('Debe seleccionar al menos un destinatario', 'error')
            return redirect(url_for('enviar_masivo'))
        
        zona = Zona.query.get(zona_id)
        plantilla = MensajePlantilla.query.get(plantilla_id)
        # Obtener solo los clientes seleccionados
        cliente_ids = [int(id) for id in destinatarios_seleccionados.split(',') if id.strip()]
        clientes = Cliente.query.filter(
            Cliente.id.in_(cliente_ids),
            Cliente.zona_id == zona_id,
            Cliente.activo == True
        ).all()
        
        resultados = []
        exitosos = 0
        fallidos = 0
        
        for cliente in clientes:
            # Generar enlace a la web pública de ofertas
            enlace_web = generar_enlace_web()
            
            # Personalizar mensaje con datos del cliente y enlace web
            mensaje_personalizado = plantilla.contenido.format(
                nombre_cliente=cliente.nombre,
                zona=zona.nombre,
                enlace_web=enlace_web
            )
            
            # Enviar mensaje usando Green-API
            success, error_msg = green_api_sender.send_message(cliente.telefono, mensaje_personalizado)
            
            # Registrar envío
            mensaje_enviado = MensajeEnviado(
                cliente_id=cliente.id,
                plantilla_id=plantilla.id,
                mensaje_final=mensaje_personalizado,
                enviado=success,
                fecha_envio=datetime.now(timezone.utc) if success else None,
                error=error_msg if not success else None
            )
            db.session.add(mensaje_enviado)
            
            if success:
                exitosos += 1
            else:
                fallidos += 1
            
            resultados.append({
                'cliente': cliente.nombre,
                'telefono': cliente.telefono,
                'exito': success,
                'error': error_msg if not success else None
            })
        
        db.session.commit()
        
        flash(f'Enviados: {exitosos}, Fallidos: {fallidos}', 'success')
        return render_template('resultado_envio.html', 
                             resultados=resultados, 
                             zona=zona, 
                             plantilla=plantilla,
                             exitosos=exitosos,
                             fallidos=fallidos)
    
    zonas = Zona.query.all()
    plantillas = MensajePlantilla.query.filter_by(activo=True).all()
    return render_template('enviar_masivo.html', zonas=zonas, plantillas=plantillas)

@app.route('/historial')
def historial():
    mensajes = MensajeEnviado.query.order_by(MensajeEnviado.created_at.desc()).limit(100).all()
    return render_template('historial.html', mensajes=mensajes)

@app.route('/api/clientes_zona/<int:zona_id>')
def api_clientes_zona(zona_id):
    clientes = Cliente.query.filter_by(zona_id=zona_id, activo=True).all()
    return jsonify([{
        'id': c.id,
        'nombre': c.nombre,
        'telefono': c.telefono
    } for c in clientes])

# Rutas para gestión de programaciones
@app.route('/programaciones')
def programaciones():
    programaciones_list = ProgramacionMasiva.query.order_by(ProgramacionMasiva.created_at.desc()).all()
    zonas = Zona.query.all()
    plantillas = MensajePlantilla.query.filter_by(activo=True).all()
    return render_template('programaciones.html', 
                         programaciones=programaciones_list,
                         zonas=zonas,
                         plantillas=plantillas)

@app.route('/programaciones/nueva', methods=['POST'])
def nueva_programacion():
    zona_id = request.form.get('zona_id')
    plantilla_id = request.form.get('plantilla_id')
    dias_semana = request.form.getlist('dias_semana')
    hora = request.form.get('hora')
    
    if not zona_id or not plantilla_id or not dias_semana or not hora:
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('programaciones'))
    
    try:
        dias_normalizados = sorted({str(int(d)) for d in dias_semana if d.strip()})
        programacion = ProgramacionMasiva(
            zona_id=int(zona_id),
            plantilla_id=int(plantilla_id),
            dias_semana=','.join(dias_normalizados),
            hora=hora,
            activo=True
        )
        db.session.add(programacion)
        db.session.commit()
        flash('Programación creada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creando la programación: {str(e)}', 'error')
    
    return redirect(url_for('programaciones'))

@app.route('/programaciones/<int:id>/editar', methods=['GET', 'POST'])
def editar_programacion(id):
    programacion = ProgramacionMasiva.query.get_or_404(id)
    
    if request.method == 'POST':
        zona_id = request.form.get('zona_id')
        plantilla_id = request.form.get('plantilla_id')
        dias_semana = request.form.getlist('dias_semana')
        hora = request.form.get('hora')
        
        if not zona_id or not plantilla_id or not dias_semana or not hora:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('editar_programacion', id=id))
        
        try:
            dias_normalizados = sorted({str(int(d)) for d in dias_semana if d.strip()})
            programacion.zona_id = int(zona_id)
            programacion.plantilla_id = int(plantilla_id)
            programacion.dias_semana = ','.join(dias_normalizados)
            programacion.hora = hora
            db.session.commit()
            flash('Programación actualizada correctamente', 'success')
            return redirect(url_for('programaciones'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando la programación: {str(e)}', 'error')
    
    zonas = Zona.query.all()
    plantillas = MensajePlantilla.query.filter_by(activo=True).all()
    dias_seleccionados = [int(d) for d in programacion.dias_semana.split(',') if d.strip()]
    
    return render_template('editar_programacion.html',
                         programacion=programacion,
                         zonas=zonas,
                         plantillas=plantillas,
                         dias_seleccionados=dias_seleccionados)

@app.route('/programaciones/<int:id>/eliminar', methods=['POST'])
def eliminar_programacion(id):
    programacion = ProgramacionMasiva.query.get_or_404(id)
    try:
        db.session.delete(programacion)
        db.session.commit()
        flash('Programación eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error eliminando la programación: {str(e)}', 'error')
    
    return redirect(url_for('programaciones'))

@app.route('/programaciones/<int:id>/toggle', methods=['POST'])
def toggle_programacion(id):
    programacion = ProgramacionMasiva.query.get_or_404(id)
    programacion.activo = not programacion.activo
    try:
        db.session.commit()
        estado = 'activada' if programacion.activo else 'desactivada'
        flash(f'Programación {estado} correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cambiando el estado: {str(e)}', 'error')
    
    return redirect(url_for('programaciones'))

# Rutas para gestión de ofertas
@app.route('/ofertas')
def ofertas():
    ofertas = Oferta.query.filter_by(activa=True).order_by(Oferta.created_at.desc()).all()
    return render_template('ofertas_admin.html', ofertas=ofertas)

@app.route('/ofertas/nueva', methods=['GET', 'POST'])
def nueva_oferta():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        destacada = 'destacada' in request.form
        
        if not titulo or not descripcion or not precio:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('nueva_oferta'))
        
        try:
            precio = float(precio)
        except ValueError:
            flash('El precio debe ser un número válido', 'error')
            return redirect(url_for('nueva_oferta'))
        
        # Manejar subida de imagen
        imagen_path = None
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo and archivo.filename:
                filename = secure_filename(archivo.filename)
                # Agregar timestamp para evitar conflictos
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagen_path = filename
        
        oferta = Oferta(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            imagen=imagen_path,
            destacada=destacada
        )
        
        db.session.add(oferta)
        db.session.commit()
        
        flash('Oferta creada exitosamente', 'success')
        return redirect(url_for('ofertas'))
    
    return render_template('nueva_oferta.html')

@app.route('/ofertas/<int:id>/editar', methods=['GET', 'POST'])
def editar_oferta(id):
    oferta = Oferta.query.get_or_404(id)
    
    if request.method == 'POST':
        oferta.titulo = request.form.get('titulo')
        oferta.descripcion = request.form.get('descripcion')
        oferta.precio = float(request.form.get('precio'))
        oferta.destacada = 'destacada' in request.form
        
        # Manejar nueva imagen
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo and archivo.filename:
                # Eliminar imagen anterior si existe
                if oferta.imagen:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], oferta.imagen))
                    except:
                        pass
                
                filename = secure_filename(archivo.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                oferta.imagen = filename
        
        oferta.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Oferta actualizada exitosamente', 'success')
        return redirect(url_for('ofertas'))
    
    return render_template('editar_oferta.html', oferta=oferta)

@app.route('/ofertas/<int:id>/eliminar', methods=['POST'])
def eliminar_oferta(id):
    oferta = Oferta.query.get_or_404(id)
    
    # Eliminar imagen si existe
    if oferta.imagen:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], oferta.imagen))
        except:
            pass
    
    db.session.delete(oferta)
    db.session.commit()
    
    flash('Oferta eliminada exitosamente', 'success')
    return redirect(url_for('ofertas'))

@app.route('/ofertas/<int:id>/toggle', methods=['POST'])
def toggle_oferta(id):
    oferta = Oferta.query.get_or_404(id)
    oferta.activa = not oferta.activa
    db.session.commit()
    
    estado = "activada" if oferta.activa else "desactivada"
    flash(f'Oferta {estado} exitosamente', 'success')
    return redirect(url_for('ofertas'))


# Rutas para la web pública
@app.route('/panel')
def panel():
    zonas = Zona.query.all()
    ofertas = Oferta.query.filter_by(activa=True).order_by(Oferta.created_at.desc()).limit(6).all()
    return render_template('panel.html', zonas=zonas, ofertas=ofertas)

@app.route('/publico/ofertas')
def ofertas_publicas():
    ofertas = Oferta.query.filter_by(activa=True).order_by(Oferta.created_at.desc()).all()
    return render_template('ofertas_publicas.html', ofertas=ofertas)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rutas para configuración de Green-API
@app.route('/configuracion')
def configuracion():
    # Verificar estado actual de Green-API
    conectado, mensaje = green_api_sender.check_instance_status()
    
    # Cargar datos de configuración
    try:
        from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
        config_data = {
            'url': GREEN_API_URL,
            'token': GREEN_API_TOKEN,
            'instance_id': GREEN_API_INSTANCE_ID,
            'phone': GREEN_API_PHONE
        }
    except ImportError:
        config_data = {
            'url': 'No configurado',
            'token': 'No configurado',
            'instance_id': 'No configurado',
            'phone': 'No configurado'
        }
    
    return render_template('configuracion.html', conectado=conectado, mensaje=mensaje, config=config_data)

@app.route('/configuracion/green-api', methods=['GET', 'POST'])
def configurar_green_api_route():
    config_data = {
        'url': '',
        'token': '',
        'instance_id': '',
        'phone': ''
    }

    try:
        if os.environ.get('RENDER'):
            from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
        else:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE

        config_data = {
            'url': GREEN_API_URL,
            'token': GREEN_API_TOKEN,
            'instance_id': GREEN_API_INSTANCE_ID,
            'phone': GREEN_API_PHONE
        }
    except ImportError:
        pass

    if request.method == 'POST':
        api_url = request.form.get('api_url')
        api_token = request.form.get('api_token')
        instance_id = request.form.get('instance_id')
        phone = request.form.get('phone')

        if not api_url or not api_token:
            flash('Debe proporcionar tanto la URL como el token de Green-API', 'error')
            return redirect(url_for('configurar_green_api_route'))

        instance_id = instance_id or config_data.get('instance_id')
        phone = phone or config_data.get('phone')

        if not instance_id:
            flash('Debe proporcionar el ID de instancia de Green-API', 'error')
            return redirect(url_for('configurar_green_api_route'))

        # Configurar Green-API
        conectado, mensaje = configurar_green_api(api_url, api_token, instance_id, phone)

        if conectado:
            flash(f'Green-API configurado exitosamente: {mensaje}', 'success')
        else:
            flash(f'Error configurando Green-API: {mensaje}', 'error')
        
        return redirect(url_for('configuracion'))
    
    return render_template('configurar_green_api.html', config=config_data)

@app.route('/configuracion/test', methods=['POST'])
def test_green_api():
    numero_test = request.form.get('numero_test')
    mensaje_test = request.form.get('mensaje_test', 'Mensaje de prueba desde Recambios RM')
    
    if not numero_test:
        flash('Debe proporcionar un número de teléfono para la prueba', 'error')
        return redirect(url_for('configuracion'))
    
    # Enviar mensaje de prueba
    success, error = green_api_sender.send_message(numero_test, mensaje_test)
    
    if success:
        flash(f'Mensaje de prueba enviado exitosamente a {numero_test}', 'success')
    else:
        flash(f'Error enviando mensaje de prueba: {error}', 'error')
    
    return redirect(url_for('configuracion'))

@app.route('/diagnostico-green-api')
def diagnostico_green_api():
    """Ruta de diagnóstico para verificar el estado de Green-API"""
    diagnostico = {
        'entorno': 'Producción' if os.environ.get('RENDER') else 'Desarrollo',
        'configuracion': {},
        'conexion': {},
        'estado': 'Desconocido'
    }
    
    try:
        # Verificar configuración
        if os.environ.get('RENDER'):
            from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
        else:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
        
        diagnostico['configuracion'] = {
            'url': GREEN_API_URL,
            'token': GREEN_API_TOKEN[:10] + '...' if GREEN_API_TOKEN else 'No configurado',
            'instance_id': GREEN_API_INSTANCE_ID,
            'phone': GREEN_API_PHONE
        }
        
        # Probar conexión
        conectado, mensaje = configurar_green_api(
            GREEN_API_URL,
            GREEN_API_TOKEN,
            GREEN_API_INSTANCE_ID,
            GREEN_API_PHONE,
        )
        
        diagnostico['conexion'] = {
            'conectado': conectado,
            'mensaje': mensaje
        }
        
        if conectado:
            diagnostico['estado'] = '✅ Conectado y funcionando'
        else:
            diagnostico['estado'] = f'❌ Error: {mensaje}'
            
    except Exception as e:
        diagnostico['estado'] = f'❌ Error de configuración: {str(e)}'
        diagnostico['error'] = str(e)
    
    return render_template('diagnostico_green_api.html', diagnostico=diagnostico)

@app.route('/setup')
def setup():
    """Página de configuración inicial del sistema"""
    return render_template('init_database.html')

@app.route('/init-db')
def init_database():
    """Ruta para inicializar la base de datos en producción"""
    try:
        with app.app_context():
            # Crear todas las tablas
            db.create_all()
            
            # Verificar si ya hay datos
            if not Zona.query.first():
                # Crear zonas básicas
                zonas_data = [
                    {'nombre': 'Centro', 'descripcion': 'Zona centro de la ciudad'},
                    {'nombre': 'Norte', 'descripcion': 'Zona norte de la ciudad'},
                    {'nombre': 'Sur', 'descripcion': 'Zona sur de la ciudad'},
                    {'nombre': 'Este', 'descripcion': 'Zona este de la ciudad'},
                    {'nombre': 'Oeste', 'descripcion': 'Zona oeste de la ciudad'}
                ]
                
                for zona_data in zonas_data:
                    zona = Zona(**zona_data)
                    db.session.add(zona)
                
                # Crear plantillas de mensajes
                plantillas_data = [
                    {
                        'nombre': 'Visita Programada',
                        'contenido': 'Hola {nombre_cliente}, somos de Recambios RM. Vamos a pasar por la zona {zona} mañana por la mañana. ¿Necesitas algún recambio específico? Te podemos llevar lo que necesites.\n\n🌐 Consulta nuestras ofertas actuales: {enlace_web}\n\n¡Gracias!'
                    },
                    {
                        'nombre': 'Recordatorio de Visita',
                        'contenido': 'Buenos días {nombre_cliente}, recordatorio: pasaremos por {zona} hoy por la tarde. Si necesitas algún recambio, avísanos antes de las 14:00.\n\n🌐 Ve nuestras ofertas: {enlace_web}\n\n¡Hasta pronto!'
                    },
                    {
                        'nombre': 'Promoción Especial',
                        'contenido': 'Hola {nombre_cliente}, tenemos una promoción especial esta semana. Pasaremos por {zona} con descuentos en recambios de motor.\n\n🌐 Descubre todas nuestras ofertas: {enlace_web}\n\n¡No te lo pierdas!'
                    }
                ]
                
                for plantilla_data in plantillas_data:
                    plantilla = MensajePlantilla(**plantilla_data)
                    db.session.add(plantilla)
                
                # Crear ofertas de ejemplo
                ofertas_data = [
                    {
                        'titulo': 'Aceite de Motor Premium',
                        'descripcion': 'Aceite de motor de alta calidad para tu vehículo. Garantiza un rendimiento óptimo y protección del motor.',
                        'precio': 25.99,
                        'activa': True,
                        'destacada': True
                    },
                    {
                        'titulo': 'Filtro de Aire',
                        'descripcion': 'Filtro de aire original para mantener el motor limpio y eficiente.',
                        'precio': 12.50,
                        'activa': True,
                        'destacada': False
                    },
                    {
                        'titulo': 'Pastillas de Freno',
                        'descripcion': 'Pastillas de freno de alta calidad para una frenada segura y eficiente.',
                        'precio': 45.00,
                        'activa': True,
                        'destacada': True
                    }
                ]
                
                for oferta_data in ofertas_data:
                    oferta = Oferta(**oferta_data)
                    db.session.add(oferta)
                
                db.session.commit()
                flash('Base de datos inicializada exitosamente con datos de ejemplo', 'success')
            else:
                flash('Base de datos ya inicializada', 'info')
                
    except Exception as e:
        flash(f'Error inicializando la base de datos: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('panel'))

@app.route('/eliminar_plantillas_temporales')
def eliminar_plantillas_temporales():
    """Ruta temporal para eliminar las plantillas 'Nuevos Productos' y 'Confirmación de Pedido'"""
    plantillas_a_eliminar = ['Nuevos Productos', 'Confirmación de Pedido']
    eliminadas = []
    
    for nombre in plantillas_a_eliminar:
        plantilla = MensajePlantilla.query.filter_by(nombre=nombre).first()
        if plantilla:
            db.session.delete(plantilla)
            eliminadas.append(nombre)
    
    db.session.commit()
    
    flash(f'Plantillas eliminadas: {", ".join(eliminadas)}', 'success')
    return redirect(url_for('mensajes'))

# Rutas para mensajes recibidos
@app.route('/webhook/whatsapp', methods=['POST'])
def webhook_whatsapp():
    """Webhook para recibir mensajes de Green-API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Procesar mensaje recibido
        mensaje_data = data.get('body', {})
        
        if mensaje_data.get('typeWebhook') == 'incomingMessageReceived':
            # Extraer información del mensaje
            message_data = mensaje_data.get('messageData', {})
            sender_data = mensaje_data.get('senderData', {})
            
            # Obtener número de teléfono del remitente
            telefono_remitente = sender_data.get('sender', '').replace('@c.us', '')
            
            # Obtener el mensaje
            mensaje_texto = ''
            tipo_mensaje = 'texto'
            archivo_url = None
            
            if 'textMessageData' in message_data:
                mensaje_texto = message_data['textMessageData'].get('textMessage', '')
                tipo_mensaje = 'texto'
            elif 'extendedTextMessageData' in message_data:
                mensaje_texto = message_data['extendedTextMessageData'].get('text', '')
                tipo_mensaje = 'texto'
            elif 'imageMessageData' in message_data:
                mensaje_texto = message_data['imageMessageData'].get('caption', '')
                tipo_mensaje = 'imagen'
                archivo_url = message_data['imageMessageData'].get('downloadUrl', '')
            elif 'documentMessageData' in message_data:
                mensaje_texto = message_data['documentMessageData'].get('caption', '')
                tipo_mensaje = 'documento'
                archivo_url = message_data['documentMessageData'].get('downloadUrl', '')
            elif 'audioMessageData' in message_data:
                mensaje_texto = '[Mensaje de audio]'
                tipo_mensaje = 'audio'
                archivo_url = message_data['audioMessageData'].get('downloadUrl', '')
            elif 'videoMessageData' in message_data:
                mensaje_texto = message_data['videoMessageData'].get('caption', '')
                tipo_mensaje = 'video'
                archivo_url = message_data['videoMessageData'].get('downloadUrl', '')
            
            # Buscar si el remitente es un cliente existente
            cliente_existente = Cliente.query.filter_by(telefono=telefono_remitente).first()
            
            # Crear registro del mensaje recibido
            mensaje_recibido = MensajeRecibido(
                telefono_remitente=telefono_remitente,
                nombre_remitente=sender_data.get('senderName', ''),
                mensaje=mensaje_texto,
                tipo_mensaje=tipo_mensaje,
                archivo_url=archivo_url,
                cliente_id=cliente_existente.id if cliente_existente else None,
                id_mensaje_whatsapp=mensaje_data.get('idMessage', '')
            )
            
            db.session.add(mensaje_recibido)

            # Registrar en conversaciones avanzadas
            chat_id_full = sender_data.get('sender') or sender_data.get('chatId') or ''
            if not chat_id_full and telefono_remitente:
                try:
                    chat_id_full = _normalize_chat_id(telefono_remitente)
                except ValueError:
                    chat_id_full = ''

            if chat_id_full:
                timestamp = mensaje_data.get('timestamp') or message_data.get('timestamp') or data.get('timestamp')
                if timestamp:
                    try:
                        sent_at = datetime.utcfromtimestamp(timestamp)
                    except Exception:
                        sent_at = datetime.utcnow()
                else:
                    sent_at = datetime.utcnow()
                try:
                    _register_incoming_whatsapp_message(
                        chat_id_full,
                        mensaje_texto,
                        contact_name=sender_data.get('senderName'),
                        sent_at=sent_at,
                        external_id=mensaje_data.get('idMessage', '')
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"⚠️ No se pudo registrar la conversación avanzada: {exc}")

            db.session.commit()
            
            print(f"✅ Mensaje recibido de {telefono_remitente}: {mensaje_texto[:50]}...")
            
            return jsonify({'status': 'success', 'message': 'Message processed'}), 200
        
        return jsonify({'status': 'ignored', 'message': 'Not an incoming message'}), 200
        
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/mensajes-recibidos')
def mensajes_recibidos():
    """Página para ver mensajes recibidos"""
    # Obtener mensajes no leídos primero, luego los leídos
    mensajes_no_leidos = MensajeRecibido.query.filter_by(leido=False).order_by(MensajeRecibido.fecha_recepcion.desc()).all()
    mensajes_leidos = MensajeRecibido.query.filter_by(leido=True).order_by(MensajeRecibido.fecha_recepcion.desc()).limit(50).all()
    
    return render_template('mensajes_recibidos.html', 
                         mensajes_no_leidos=mensajes_no_leidos,
                         mensajes_leidos=mensajes_leidos)

@app.route('/mensajes-recibidos/<int:mensaje_id>/marcar-leido', methods=['POST'])
def marcar_mensaje_leido(mensaje_id):
    """Marcar un mensaje como leído"""
    mensaje = MensajeRecibido.query.get_or_404(mensaje_id)
    mensaje.leido = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/mensajes-recibidos/<int:mensaje_id>/responder', methods=['POST'])
def responder_mensaje(mensaje_id):
    """Responder a un mensaje recibido"""
    mensaje = MensajeRecibido.query.get_or_404(mensaje_id)
    respuesta_texto = request.form.get('respuesta')
    
    if not respuesta_texto:
        flash('Debe escribir una respuesta', 'error')
        return redirect(url_for('mensajes_recibidos'))
    
    try:
        # Enviar respuesta usando Green-API
        success, error_msg = green_api_sender.send_message(mensaje.telefono_remitente, respuesta_texto)
        
        # Crear registro de la respuesta
        respuesta = RespuestaMensaje(
            mensaje_recibido_id=mensaje.id,
            respuesta=respuesta_texto,
            enviado=success,
            fecha_envio=datetime.now(timezone.utc) if success else None,
            error=error_msg if not success else None
        )
        
        db.session.add(respuesta)
        
        # Marcar mensaje original como respondido si se envió correctamente
        if success:
            mensaje.respondido = True
            try:
                _register_outgoing_whatsapp_message(
                    mensaje.telefono_remitente,
                    respuesta_texto,
                    sent_at=datetime.utcnow(),
                )
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ No se pudo registrar la respuesta en conversaciones avanzadas: {exc}")
        
        db.session.commit()
        
        if success:
            flash('Respuesta enviada exitosamente', 'success')
        else:
            flash(f'Error enviando respuesta: {error_msg}', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error procesando respuesta: {str(e)}', 'error')
    
    return redirect(url_for('mensajes_recibidos'))

@app.route('/mensajes-recibidos/<int:mensaje_id>/ver-conversacion')
def ver_conversacion(mensaje_id):
    """Ver la conversación completa con un cliente"""
    mensaje = MensajeRecibido.query.get_or_404(mensaje_id)
    
    # Obtener todos los mensajes recibidos de este número
    mensajes_recibidos = MensajeRecibido.query.filter_by(telefono_remitente=mensaje.telefono_remitente).order_by(MensajeRecibido.fecha_recepcion.asc()).all()
    
    # Obtener todas las respuestas enviadas a este número
    respuestas_enviadas = []
    for msg in mensajes_recibidos:
        respuestas = RespuestaMensaje.query.filter_by(mensaje_recibido_id=msg.id).all()
        respuestas_enviadas.extend(respuestas)
    
    # Combinar y ordenar cronológicamente
    conversacion = []
    
    # Agregar mensajes recibidos
    for msg in mensajes_recibidos:
        conversacion.append({
            'tipo': 'recibido',
            'fecha': msg.fecha_recepcion,
            'mensaje': msg.mensaje,
            'tipo_mensaje': msg.tipo_mensaje,
            'archivo_url': msg.archivo_url
        })
    
    # Agregar respuestas enviadas
    for resp in respuestas_enviadas:
        conversacion.append({
            'tipo': 'enviado',
            'fecha': resp.fecha_envio,
            'mensaje': resp.respuesta,
            'tipo_mensaje': 'texto'
        })
    
    # Ordenar por fecha
    conversacion.sort(key=lambda x: x['fecha'])
    
    return render_template('conversacion.html', 
                         conversacion=conversacion,
                         telefono=mensaje.telefono_remitente,
                         nombre=mensaje.nombre_remitente)

# Interfaces de WhatsApp avanzadas
@app.route('/whatsapp')
def whatsapp_dashboard():
    conversaciones = WhatsAppConversation.query.order_by(WhatsAppConversation.updated_at.desc()).all()
    return render_template('whatsapp/index.html', conversaciones=conversaciones)


@app.route('/whatsapp/conversaciones/nueva', methods=['GET', 'POST'])
def whatsapp_new_conversation():
    if request.method == 'POST':
        raw_number = (request.form.get('contact_number') or '').strip()
        contact_name = (request.form.get('contact_name') or '').strip() or None
        initial_message = (request.form.get('initial_message') or '').strip()

        if not raw_number:
            flash('Debes indicar un número de WhatsApp', 'error')
            return render_template('whatsapp/new_conversation.html')

        try:
            chat_id = _normalize_chat_id(raw_number)
        except ValueError as exc:
            flash(str(exc), 'error')
            return render_template('whatsapp/new_conversation.html')

        existing = WhatsAppConversation.query.filter_by(contact_number=chat_id).first()
        if existing:
            flash('Ya existe una conversación con ese número.', 'info')
            return redirect(url_for('whatsapp_conversation_detail', conversation_id=existing.id))

        conversation = _ensure_whatsapp_conversation(chat_id, contact_name, datetime.utcnow())

        if initial_message:
            try:
                external_id = _send_green_api_message(chat_id, initial_message)
            except Exception as exc:  # noqa: BLE001
                db.session.rollback()
                flash(f'No fue posible enviar el mensaje inicial: {exc}', 'error')
                return render_template('whatsapp/new_conversation.html')

            _append_whatsapp_message(
                conversation,
                sender_type='agent',
                message_text=initial_message,
                sent_at=datetime.utcnow(),
                external_id=external_id,
                is_read=True,
            )

        db.session.commit()
        flash('Conversación creada correctamente.', 'success')
        return redirect(url_for('whatsapp_conversation_detail', conversation_id=conversation.id))

    return render_template('whatsapp/new_conversation.html')


@app.route('/whatsapp/conversaciones/<int:conversation_id>', methods=['GET', 'POST'])
def whatsapp_conversation_detail(conversation_id):
    conversation = WhatsAppConversation.query.get_or_404(conversation_id)

    if request.method == 'POST':
        message_text = (request.form.get('message') or '').strip()

        if not message_text:
            flash('El mensaje no puede estar vacío', 'error')
            return redirect(url_for('whatsapp_conversation_detail', conversation_id=conversation.id))

        try:
            external_id = _send_green_api_message(conversation.contact_number, message_text)
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            flash(f'Error enviando mensaje: {exc}', 'error')
            return redirect(url_for('whatsapp_conversation_detail', conversation_id=conversation.id))

        _append_whatsapp_message(
            conversation,
            sender_type='agent',
            message_text=message_text,
            sent_at=datetime.utcnow(),
            external_id=external_id,
            is_read=True,
        )
        db.session.commit()
        flash('Mensaje enviado correctamente', 'success')
        return redirect(url_for('whatsapp_conversation_detail', conversation_id=conversation.id))

    unread_messages = conversation.messages.filter_by(sender_type='customer', is_read=False).all()
    if unread_messages:
        for msg in unread_messages:
            msg.is_read = True
        db.session.commit()
        conversation = WhatsAppConversation.query.get_or_404(conversation_id)

    messages = conversation.messages.order_by(WhatsAppMessage.sent_at.asc(), WhatsAppMessage.id.asc()).all()
    return render_template('whatsapp/conversation.html', conversation=conversation, messages=messages)


@app.get('/whatsapp/api/conversaciones')
def whatsapp_api_conversations():
    conversaciones = WhatsAppConversation.query.order_by(WhatsAppConversation.updated_at.desc()).all()
    data = [_conversation_to_dict(c) for c in conversaciones]
    return jsonify({'conversations': data})


@app.get('/whatsapp/api/conversaciones/<int:conversation_id>/mensajes')
def whatsapp_api_conversation_messages(conversation_id):
    conversation = WhatsAppConversation.query.get_or_404(conversation_id)
    after_id = request.args.get('after_id', default=0, type=int)
    mark_read = request.args.get('mark_read', default='0').lower() in {'1', 'true', 'yes'}

    query = WhatsAppMessage.query.filter(
        WhatsAppMessage.conversation_id == conversation.id,
        WhatsAppMessage.id > after_id,
    ).order_by(WhatsAppMessage.id.asc())

    messages = query.all()
    changed = False
    last_id = after_id
    serialized = []

    for message in messages:
        serialized.append(_message_to_dict(message))
        last_id = max(last_id, message.id)
        if mark_read and message.sender_type == 'customer' and not message.is_read:
            message.is_read = True
            changed = True

    if changed:
        db.session.commit()

    return jsonify({
        'messages': serialized,
        'last_id': last_id,
        'unread_count': conversation.unread_count(),
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
        'updated_at_human': conversation.updated_at.strftime("%d/%m/%Y %H:%M") if conversation.updated_at else '',
    })


@app.get('/whatsapp/api/contactos')
def whatsapp_api_contacts():
    try:
        contacts = _fetch_green_api_contacts()
    except Exception as exc:  # noqa: BLE001
        return jsonify({'error': f'No fue posible obtener los contactos: {exc}'}), 502

    normalized = []
    for contact in contacts:
        normalized.append({
            'id': contact.get('id'),
            'name': contact.get('name'),
            'type': contact.get('type'),
            'category': contact.get('category'),
            'chat_id': contact.get('id'),
        })

    return jsonify({'contacts': normalized})


@app.route('/whatsapp/health')
def whatsapp_health_check():
    return jsonify({'status': 'ok'}), 200

# Ruta para polling de mensajes (respaldo al webhook)
@app.route('/polling-mensajes')
def polling_mensajes():
    """Obtener mensajes usando polling como respaldo al webhook"""
    try:
        import requests
        
        # Configuración de Green-API
        if os.environ.get('RENDER'):
            from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
        else:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
        
        # URL para obtener mensajes
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/receiveNotification/{GREEN_API_TOKEN}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'body' in data:
                mensaje_data = data['body']
                
                if mensaje_data.get('typeWebhook') == 'incomingMessageReceived':
                    # Procesar el mensaje igual que en el webhook
                    message_data = mensaje_data.get('messageData', {})
                    sender_data = mensaje_data.get('senderData', {})
                    
                    # Obtener número de teléfono del remitente
                    telefono_remitente = sender_data.get('sender', '').replace('@c.us', '')
                    
                    # Obtener el mensaje
                    mensaje_texto = ''
                    tipo_mensaje = 'texto'
                    archivo_url = None
                    
                    if 'textMessageData' in message_data:
                        mensaje_texto = message_data['textMessageData'].get('textMessage', '')
                        tipo_mensaje = 'texto'
                    elif 'extendedTextMessageData' in message_data:
                        mensaje_texto = message_data['extendedTextMessageData'].get('text', '')
                        tipo_mensaje = 'texto'
                    elif 'imageMessageData' in message_data:
                        mensaje_texto = message_data['imageMessageData'].get('caption', '')
                        tipo_mensaje = 'imagen'
                        archivo_url = message_data['imageMessageData'].get('downloadUrl', '')
                    elif 'documentMessageData' in message_data:
                        mensaje_texto = message_data['documentMessageData'].get('caption', '')
                        tipo_mensaje = 'documento'
                        archivo_url = message_data['documentMessageData'].get('downloadUrl', '')
                    elif 'audioMessageData' in message_data:
                        mensaje_texto = '[Mensaje de audio]'
                        tipo_mensaje = 'audio'
                        archivo_url = message_data['audioMessageData'].get('downloadUrl', '')
                    elif 'videoMessageData' in message_data:
                        mensaje_texto = message_data['videoMessageData'].get('caption', '')
                        tipo_mensaje = 'video'
                        archivo_url = message_data['videoMessageData'].get('downloadUrl', '')
                    
                    # Buscar si el remitente es un cliente existente
                    cliente_existente = Cliente.query.filter_by(telefono=telefono_remitente).first()
                    
                    # Crear registro del mensaje recibido
                    mensaje_recibido = MensajeRecibido(
                        telefono_remitente=telefono_remitente,
                        nombre_remitente=sender_data.get('senderName', ''),
                        mensaje=mensaje_texto,
                        tipo_mensaje=tipo_mensaje,
                        archivo_url=archivo_url,
                        cliente_id=cliente_existente.id if cliente_existente else None,
                        id_mensaje_whatsapp=mensaje_data.get('idMessage', '')
                    )
                    
                    db.session.add(mensaje_recibido)
                    db.session.commit()
                    
                    print(f"✅ Mensaje recibido por polling de {telefono_remitente}: {mensaje_texto[:50]}...")
                    
                    return jsonify({'status': 'success', 'message': 'Message processed via polling'})
                else:
                    return jsonify({'status': 'ignored', 'message': f'Not an incoming message: {mensaje_data.get("typeWebhook")}'})
            else:
                return jsonify({'status': 'no_messages', 'message': 'No messages in queue'})
                
        elif response.status_code == 404:
            return jsonify({'status': 'no_messages', 'message': 'No messages in queue'})
        else:
            return jsonify({'status': 'error', 'message': f'HTTP {response.status_code}'})
            
    except Exception as e:
        print(f"❌ Error en polling: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

# Ruta para activar polling automático
@app.route('/activar-polling')
def activar_polling():
    """Página para activar el polling automático"""
    return render_template('activar_polling.html')

def inicializar_sistema():
    """Inicializa la base de datos y datos de ejemplo si es necesario"""
    try:
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya hay datos
        if not Zona.query.first():
            print("📝 Inicializando base de datos con datos de ejemplo...")
            
            # Crear zonas básicas
            zonas_data = [
                {'nombre': 'Centro', 'descripcion': 'Zona centro de la ciudad'},
                {'nombre': 'Norte', 'descripcion': 'Zona norte de la ciudad'},
                {'nombre': 'Sur', 'descripcion': 'Zona sur de la ciudad'},
                {'nombre': 'Este', 'descripcion': 'Zona este de la ciudad'},
                {'nombre': 'Oeste', 'descripcion': 'Zona oeste de la ciudad'}
            ]
            
            for zona_data in zonas_data:
                zona = Zona(**zona_data)
                db.session.add(zona)
            
            # Crear plantillas de mensajes
            plantillas_data = [
                {
                    'nombre': 'Visita Programada',
                    'contenido': 'Hola {nombre_cliente}, somos de Recambios RM. Vamos a pasar por la zona {zona} mañana por la mañana. ¿Necesitas algún recambio específico? Te podemos llevar lo que necesites. ¡Gracias!'
                },
                {
                    'nombre': 'Recordatorio de Visita',
                    'contenido': 'Buenos días {nombre_cliente}, recordatorio: pasaremos por {zona} hoy por la tarde. Si necesitas algún recambio, avísanos antes de las 14:00. ¡Hasta pronto!'
                },
                {
                    'nombre': 'Promoción Especial',
                    'contenido': 'Hola {nombre_cliente}, tenemos una promoción especial esta semana. Pasaremos por {zona} con descuentos en recambios de motor. ¡No te lo pierdas!'
                }
            ]
            
            for plantilla_data in plantillas_data:
                plantilla = MensajePlantilla(**plantilla_data)
                db.session.add(plantilla)
            
            # Crear ofertas de ejemplo
            ofertas_data = [
                {
                    'titulo': 'Aceite de Motor Premium',
                    'descripcion': 'Aceite de motor de alta calidad para tu vehículo. Garantiza un rendimiento óptimo y protección del motor.',
                    'precio': 25.99,
                    'activa': True,
                    'destacada': True
                },
                {
                    'titulo': 'Filtro de Aire',
                    'descripcion': 'Filtro de aire original para mantener el motor limpio y eficiente.',
                    'precio': 12.50,
                    'activa': True,
                    'destacada': False
                },
                {
                    'titulo': 'Pastillas de Freno',
                    'descripcion': 'Pastillas de freno de alta calidad para una frenada segura y eficiente.',
                    'precio': 45.00,
                    'activa': True,
                    'destacada': True
                }
            ]
            
            for oferta_data in ofertas_data:
                oferta = Oferta(**oferta_data)
                db.session.add(oferta)
            
            db.session.commit()
            print("✅ Sistema inicializado exitosamente!")
            print(f"- {len(zonas_data)} zonas creadas")
            print(f"- {len(plantillas_data)} plantillas de mensajes creadas")
            print(f"- {len(ofertas_data)} ofertas de ejemplo creadas")
        else:
            print("✅ Sistema ya inicializado")
            
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        # Inicializar sistema automáticamente
        inicializar_sistema()
        
        # Configurar Green-API automáticamente al iniciar
        try:
            if os.environ.get('RENDER'):
                from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
            else:
                from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
            
            if GREEN_API_TOKEN != 'TU_TOKEN_AQUI':
                conectado, mensaje = configurar_green_api(
                    GREEN_API_URL,
                    GREEN_API_TOKEN,
                    GREEN_API_INSTANCE_ID,
                    GREEN_API_PHONE,
                )
                if conectado:
                    print("✅ Green-API configurado automáticamente - ENVÍOS REALES ACTIVADOS")
                else:
                    print(f"⚠️ Green-API configurado pero no conectado: {mensaje}")
            else:
                print("⚠️ Green-API no configurado - usando modo simulación")
        except ImportError:
            print("⚠️ Archivo de configuración no encontrado - usando modo simulación")
    
    # Usar puerto correcto según el entorno
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
