from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response, abort, has_request_context
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
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
    Usuario,
)
from whatsapp_sender import enviar_whatsapp, configurar_green_api, green_api_sender
from datetime import datetime, date, timezone
import os
import threading
import time as _time
import requests
from sqlalchemy import text, inspect, func, select, and_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import base64
import io
from zoneinfo import ZoneInfo
from collections import UserDict, defaultdict

app = Flask(__name__)

# Rate limiting para webhooks - Protección contra spam
# Estructura: {ip: [(timestamp1, timestamp2, ...)]}
_webhook_rate_limit = defaultdict(list)
_rate_limit_lock = threading.Lock()
_RATE_LIMIT_WINDOW = 60  # Ventana de tiempo en segundos (1 minuto)
_RATE_LIMIT_MAX_REQUESTS = 100  # Máximo de requests por ventana de tiempo

def _check_rate_limit(ip_address: str) -> bool:
    """
    Verifica si una IP ha excedido el límite de rate.
    Retorna True si está permitido, False si excedió el límite.
    """
    current_time = _time.time()
    
    with _rate_limit_lock:
        # Limpiar timestamps antiguos (fuera de la ventana)
        _webhook_rate_limit[ip_address] = [
            ts for ts in _webhook_rate_limit[ip_address]
            if current_time - ts < _RATE_LIMIT_WINDOW
        ]
        
        # Verificar si excedió el límite
        if len(_webhook_rate_limit[ip_address]) >= _RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # Registrar esta solicitud
        _webhook_rate_limit[ip_address].append(current_time)
        return True

def _get_client_ip() -> str:
    """Obtiene la IP del cliente, considerando proxies"""
    if request.headers.get('X-Forwarded-For'):
        # Si hay X-Forwarded-For, tomar la primera IP (cliente real)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr or 'unknown'

# Configuración general
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')

# URL de base de datos PostgreSQL por defecto (para desarrollo local)
# Formato: postgresql://usuario:contraseña@host:5432/nombre_bd
# IMPORTANTE: Para desarrollo local, usa la URL EXTERNA de Render (con el dominio completo)
# La URL interna (sin dominio) solo funciona desde dentro de Render
# Ejemplo URL externa: 'postgresql://usuario:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/nombre_bd'
# IMPORTANTE: Añade el dominio completo .oregon-postgres.render.com (o el que corresponda) al host
DEFAULT_DATABASE_URL = 'postgresql://rm_aunv_user:Rh5sYRf0UnFAVSggD5OU8d6FTCRm1FIl@dpg-d4c6vu6r433s73dbo2lg-a.oregon-postgres.render.com/rm_aunv'

# Obtener DATABASE_URL - Primero intenta variable de entorno, luego usa la URL por defecto
database_url = os.environ.get('DATABASE_URL') or DEFAULT_DATABASE_URL

# Si es la URL por defecto sin modificar, advertir pero permitir continuar
if database_url == DEFAULT_DATABASE_URL:
    print("⚠️ ADVERTENCIA: Usando URL de base de datos por defecto.")
    print("   Configura DATABASE_URL en variables de entorno o actualiza DEFAULT_DATABASE_URL en app.py")
    print("   Para producción en Render, configura DATABASE_URL en las variables de entorno del servicio")

# Validar que sea PostgreSQL
if not database_url.startswith(('postgresql://', 'postgres://')):
    raise ValueError(
        f"❌ ERROR: DATABASE_URL debe ser una URL de PostgreSQL. "
        f"URL recibida: {database_url[:50]}... "
        "Esta aplicación solo soporta PostgreSQL."
    )

# Convertir postgres:// a postgresql:// (compatibilidad con Render)
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# En producción, usar la URL interna de Render si está disponible
if os.environ.get('RENDER'):
    # Render proporciona DATABASE_URL automáticamente
    # Si hay una URL interna específica, se puede usar aquí
    internal_db_url = os.environ.get('INTERNAL_DATABASE_URL')
    if internal_db_url:
        database_url = internal_db_url
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración del engine para PostgreSQL (siempre PostgreSQL)
# SSL solo requerido en producción (Render), en local puede no ser necesario
ssl_mode = 'require' if os.environ.get('RENDER') else 'prefer'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verificar conexiones antes de usarlas
    'pool_recycle': 300,    # Reciclar conexiones cada 5 minutos
    'pool_size': 10,        # Conexiones base en el pool
    'max_overflow': 20,     # Conexiones adicionales permitidas en picos
    'pool_timeout': 30,     # Segundos de espera para obtener conexión
    'connect_args': {
        'sslmode': ssl_mode,
        'connect_timeout': 10  # Timeout de conexión inicial
    }
}

app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# Configuración común
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crear directorio de uploads si no existe  
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Asegurar que las tablas existen (incluye las de WhatsApp)
with app.app_context():
    try:
        db_host = database_url.split('@')[-1].split('/')[0] if '@' in database_url else 'PostgreSQL'
        print(f"🔌 Conectando a PostgreSQL: {db_host}")
        db.create_all()
        print("✅ Tablas creadas/verificadas correctamente")
        
        # Verificar y crear tabla de usuario si no existe
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"📊 Tablas existentes: {', '.join(existing_tables)}")
            
            if 'usuario' not in existing_tables:
                print("⚠️ Tabla 'usuario' no encontrada, creándola...")
                db.create_all()
        except Exception as e:
            print(f"⚠️ Error verificando tablas: {e}")
            db.create_all()
        
        inspector = inspect(db.engine)
        try:
            # Añadir columna color a la tabla usuario si no existe
            if 'usuario' in inspector.get_table_names():
                usuario_columns = {col['name'] for col in inspector.get_columns('usuario')}
                if 'color' not in usuario_columns:
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE usuario ADD COLUMN color VARCHAR(7) DEFAULT '#007bff'"))
                        print("✅ Columna 'color' añadida a la tabla 'usuario'")
            
            # Migraciones para whatsapp_message
            if 'whatsapp_message' in inspector.get_table_names():
                whatsapp_columns = {col['name'] for col in inspector.get_columns('whatsapp_message')}
                with db.engine.begin() as conn:
                    if 'media_type' not in whatsapp_columns:
                        conn.execute(text("ALTER TABLE whatsapp_message ADD COLUMN media_type VARCHAR(32)"))
                        print("✅ Columna 'media_type' añadida a la tabla 'whatsapp_message'")
                    if 'media_url' not in whatsapp_columns:
                        conn.execute(text("ALTER TABLE whatsapp_message ADD COLUMN media_url VARCHAR(500)"))
                        print("✅ Columna 'media_url' añadida a la tabla 'whatsapp_message'")
                    if 'usuario_id' not in whatsapp_columns:
                        # Para PostgreSQL, necesitamos manejar la foreign key correctamente
                        try:
                            conn.execute(text("ALTER TABLE whatsapp_message ADD COLUMN usuario_id INTEGER"))
                            # Intentar añadir la foreign key (puede fallar si ya existe)
                            try:
                                conn.execute(text("ALTER TABLE whatsapp_message ADD CONSTRAINT fk_whatsapp_message_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id)"))
                            except Exception:
                                pass  # La constraint puede ya existir
                        except Exception:
                            # Si falla, al menos intentar añadir la columna sin foreign key
                            try:
                                conn.execute(text("ALTER TABLE whatsapp_message ADD COLUMN usuario_id INTEGER"))
                            except Exception:
                                pass
                        print("✅ Columna 'usuario_id' añadida a la tabla 'whatsapp_message'")
        except Exception as e:
            print(f"⚠️ Error en migraciones de columnas: {e}")
            import traceback
            print(traceback.format_exc())
        
        try:
            if 'cliente' in inspector.get_table_names():
                cliente_columns = {col['name'] for col in inspector.get_columns('cliente')}
                if 'codigo' not in cliente_columns:
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE cliente ADD COLUMN codigo VARCHAR(50)"))
                        print("✅ Columna 'codigo' añadida a la tabla 'cliente'")
        except Exception as e:
            print(f"⚠️ Error añadiendo columna codigo a cliente: {e}")
            
        print("✅ Base de datos inicializada correctamente")
        
        # Nota: inicializar_sistema() se ejecutará automáticamente en before_request
        # No se llama aquí porque aún no está definida en este punto del código
    except Exception as e:
        print(f"❌ Error crítico inicializando base de datos: {e}")
        import traceback
        print(traceback.format_exc())
        # No hacer raise para que la app pueda iniciar aunque haya errores menores
        print("⚠️ Continuando con el inicio de la aplicación...")

# Variable para controlar la inicialización
_sistema_inicializado = False
_scheduler_iniciado = False
_scheduler_tz_name = os.environ.get('SCHEDULER_TZ', 'Europe/Madrid')
try:
    _scheduler_tz = ZoneInfo(_scheduler_tz_name)
except Exception:
    print(f"⚠️ Zona horaria '{_scheduler_tz_name}' no válida. Se usará UTC.")
    _scheduler_tz_name = 'UTC'
    _scheduler_tz = ZoneInfo('UTC')


def _now():
    return datetime.now(_scheduler_tz)

def _to_local_time(utc_dt: datetime | None) -> datetime | None:
    """Convierte una fecha UTC a la zona horaria del scheduler (Europe/Madrid por defecto)"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        # Si no tiene timezone, asumir que es UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    elif utc_dt.tzinfo != timezone.utc:
        # Si tiene otro timezone, convertir a UTC primero
        utc_dt = utc_dt.astimezone(timezone.utc)
    return utc_dt.astimezone(_scheduler_tz)


class _FormatoSeguro(UserDict):
    """Permite usar str.format_map sin lanzar KeyError cuando faltan llaves."""

    def __missing__(self, key):
        return ""


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
    if isinstance(data, dict):
        contacts = data.get("contacts") or data.get("result")
    elif isinstance(data, list):
        contacts = data
    else:
        contacts = None

    if contacts is None:
        raise ValueError(f"Respuesta inesperada al solicitar contactos en Green-API: {data}")
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
        if contact_name:
            cleaned_name = contact_name.strip()
            if cleaned_name and cleaned_name != conversation.contact_name:
                conversation.contact_name = cleaned_name

    conversation.updated_at = datetime.now(timezone.utc)
    return conversation


def _append_whatsapp_message(
    conversation: WhatsAppConversation,
    sender_type: str,
    message_text: str,
    sent_at: datetime | None = None,
    external_id: str | None = None,
    is_read: bool = True,
    media_type: str | None = None,
    media_url: str | None = None,
    usuario_id: int | None = None,
) -> WhatsAppMessage:
    message = WhatsAppMessage(
        conversation_id=conversation.id,
        sender_type=sender_type,
        message_text=message_text,
        sent_at=(sent_at.replace(tzinfo=timezone.utc) if sent_at and sent_at.tzinfo is None else sent_at) or datetime.now(timezone.utc),
        external_id=external_id,
        is_read=is_read,
        media_type=media_type,
        media_url=media_url,
        usuario_id=usuario_id if sender_type == 'agent' else None,
    )
    conversation.updated_at = datetime.now(timezone.utc)
    db.session.add(message)
    return message


def _register_incoming_whatsapp_message(
    chat_id: str,
    message_text: str,
    contact_name: str | None = None,
    sent_at: datetime | None = None,
    external_id: str | None = None,
    media_type: str | None = None,
    media_url: str | None = None,
):
    conversation = _ensure_whatsapp_conversation(chat_id, contact_name, sent_at)
    _append_whatsapp_message(
        conversation,
        sender_type="customer",
        message_text=message_text,
        sent_at=sent_at,
        external_id=external_id,
        is_read=False,
        media_type=media_type,
        media_url=media_url,
    )


def _register_outgoing_whatsapp_message(
    chat_id: str,
    message_text: str,
    sent_at: datetime | None = None,
    external_id: str | None = None,
    media_type: str | None = None,
    media_url: str | None = None,
    usuario_id: int | None = None,
):
    conversation = _ensure_whatsapp_conversation(chat_id)
    # Si no se proporciona usuario_id, intentar obtener el usuario actual
    if usuario_id is None:
        try:
            from flask_login import current_user
            if hasattr(current_user, 'id') and current_user.is_authenticated:
                usuario_id = current_user.id
        except:
            pass
    _append_whatsapp_message(
        conversation,
        sender_type="agent",
        message_text=message_text,
        sent_at=sent_at,
        external_id=external_id,
        is_read=True,
        media_type=media_type,
        media_url=media_url,
        usuario_id=usuario_id,
    )


def _conversation_to_dict(conversation: WhatsAppConversation) -> dict:
    last = conversation.last_message()
    # Buscar el último mensaje de un agente (siempre mostrar el último agente que escribió)
    last_agent = conversation.last_agent_message()
    last_usuario = None
    # Siempre incluir el último usuario agente que escribió, incluso si el último mensaje es del cliente
    if last_agent and last_agent.usuario:
        last_usuario = {
            "id": last_agent.usuario.id,
            "username": last_agent.usuario.username,
            "color": last_agent.usuario.color or "#007bff",  # Fallback solo si es None
        }
    return {
        "id": conversation.id,
        "display_name": conversation.contact_name or _chat_display(conversation.contact_number),
        "contact_number": conversation.contact_number,
        "last_message_text": last.message_text if last else "",
        "last_message_sender": last.sender_type if last else None,
        "last_media_type": last.media_type if last else None,
        "last_usuario": last_usuario,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "updated_at_human": _to_local_time(conversation.updated_at).strftime("%d/%m/%Y %H:%M") if conversation.updated_at else "",
        "unread_count": conversation.unread_count(),
        "url": url_for("whatsapp_conversation_detail", conversation_id=conversation.id),
    }


def _message_to_dict(message: WhatsAppMessage) -> dict:
    usuario_data = None
    if message.usuario:
        usuario_data = {
            "id": message.usuario.id,
            "username": message.usuario.username,
            "color": message.usuario.color or "#007bff",
        }
    # Generar media_route si hay media_type y (media_url o external_id)
    media_route = None
    if message.media_type and (message.media_url or message.external_id):
        media_route = url_for('whatsapp_media', message_id=message.id)
    
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_type": message.sender_type,
        "message_text": message.message_text,
        "sent_at": message.sent_at.isoformat() if message.sent_at else None,
        "sent_at_human": _to_local_time(message.sent_at).strftime("%d/%m/%Y %H:%M") if message.sent_at else "",
        "is_read": message.is_read,
        "media_type": message.media_type,
        "media_url": message.media_url,
        "external_id": message.external_id,  # Incluir external_id para debugging
        "media_route": media_route,
        "usuario": usuario_data,
    }


@app.template_filter("nl2br")
def nl2br_filter(value: str | None) -> Markup:
    if value is None:
        return Markup("")
    return Markup(str(value).replace("\n", "<br>"))


@app.template_filter("chat_display")
def chat_display_filter(value: str | None) -> str:
    return _chat_display(value)

@app.template_filter("local_time")
def local_time_filter(utc_dt: datetime | None) -> datetime | None:
    """Filtro de template para convertir fechas UTC a la zona horaria local"""
    return _to_local_time(utc_dt)


def _ejecutor_programaciones():
    """Hilo en background que ejecuta envíos masivos programados por zona y hora."""
    with app.app_context():
        while True:
            ahora = _now()
            dia_semana = ahora.weekday()  # 0=Lunes ... 6=Domingo
            hora_actual = ahora.strftime('%H:%M')
            hoy = ahora.date()
            # Debug: muestra el pulso del scheduler
            print(f"⏱️ {_scheduler_tz_name} -> {ahora.strftime('%Y-%m-%d %H:%M:%S')} (weekday={dia_semana})")

            try:
                programaciones = ProgramacionMasiva.query.filter_by(activo=True).all()
                for prog in programaciones:
                    # Verificar día
                    dias = {int(d) for d in prog.dias_semana.split(',') if d.strip()}
                    if dia_semana not in dias:
                        if prog.ultima_ejecucion != hoy:
                            print(
                                f"↷ Programación {prog.id} omitida: hoy es {dia_semana}, "
                                f"válida para {sorted(dias)}"
                            )
                        continue

                    # Verificar hora exacta (minuto)
                    if prog.hora != hora_actual:
                        if prog.ultima_ejecucion != hoy:
                            print(
                                f"⌛ Programación {prog.id} aún no es su hora: "
                                f"objetivo {prog.hora}, ahora {hora_actual}"
                            )
                        continue

                    # Evitar ejecutar más de una vez por día
                    if prog.ultima_ejecucion == hoy:
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
                        contexto_mensaje = _FormatoSeguro({
                            "nombre_cliente": cliente.nombre,
                            "cliente_nombre": cliente.nombre,
                            "zona": zona.nombre,
                            "zona_nombre": zona.nombre,
                            "enlace_web": "",
                            "link_ofertas": "",
                            "telefono_cliente": cliente.telefono,
                            "cliente_telefono": cliente.telefono,
                        })
                        mensaje_personalizado = plantilla.contenido.format_map(contexto_mensaje)

                        success, error_msg = green_api_sender.send_message(cliente.telefono, mensaje_personalizado)

                        if success:
                            try:
                                _register_outgoing_whatsapp_message(
                                    cliente.telefono,
                                    mensaje_personalizado,
                                    sent_at=_now().astimezone(timezone.utc)
                                )
                            except Exception as exc:  # noqa: BLE001
                                print(f"⚠️ No se pudo registrar la conversación avanzada: {exc}")

                        registro = MensajeEnviado(
                            cliente_id=cliente.id,
                            plantilla_id=plantilla.id,
                            mensaje_final=mensaje_personalizado,
                            enviado=success,
                            fecha_envio=_now().astimezone(timezone.utc) if success else None,
                            error=error_msg if not success else None
                        )
                        db.session.add(registro)

                    # Marcar ejecución del día y confirmar
                    prog.ultima_ejecucion = hoy
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

# Función de migración de SQLite eliminada - esta aplicación solo usa PostgreSQL
# Si necesitas migrar datos desde SQLite, usa el script migrar_bd.py manualmente

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
        
        # Asegurar que todos los clientes tengan incluir=True (campo reservado para futuro)
        try:
            clientes_sin_incluir = Cliente.query.filter_by(incluir=False).all()
            if clientes_sin_incluir:
                for cliente in clientes_sin_incluir:
                    cliente.incluir = True
                db.session.commit()
                print(f"✅ Actualizados {len(clientes_sin_incluir)} clientes para tener incluir=True")
        except Exception:
            pass  # Puede que la tabla cliente no exista aún
        
        # Crear o actualizar usuario inicial (siempre se ejecuta)
        try:
            usuario_admin = Usuario.query.filter_by(username='jmurillo').first()
            if not usuario_admin:
                usuario_admin = Usuario(username='jmurillo', activo=True)
                usuario_admin.set_password('TxMb-7-0')
                db.session.add(usuario_admin)
                db.session.commit()
                print("✅ Usuario administrador 'jmurillo' creado")
            else:
                # Actualizar contraseña si el usuario ya existe
                usuario_admin.set_password('TxMb-7-0')
                usuario_admin.activo = True
                db.session.commit()
                print("✅ Contraseña del usuario 'jmurillo' actualizada")
        except Exception as e:
            print(f"⚠️ Error creando usuario admin: {e}")
        
        _sistema_inicializado = True
            
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        import traceback
        print(traceback.format_exc())
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
    
    # Solo inicializar una vez (tanto en desarrollo como producción)
    if not _sistema_inicializado:
        try:
            inicializar_sistema()
        except Exception as e:
            print(f"⚠️ Error en before_request inicializando sistema: {e}")
    
    # Asegurar que el usuario admin existe siempre (se ejecuta en cada request hasta que se cree)
    try:
        usuario_admin = Usuario.query.filter_by(username='jmurillo').first()
        if not usuario_admin:
            usuario_admin = Usuario(username='jmurillo', activo=True)
            usuario_admin.set_password('TxMb-7-0')
            db.session.add(usuario_admin)
            db.session.commit()
            print("✅ Usuario administrador 'jmurillo' creado")
    except Exception as e:
        # Si hay error, no hacer nada (probablemente la tabla no existe aún)
        pass

def generar_enlace_web():
    """Genera el enlace completo a la web pública de ofertas"""
    base_url = (
        os.environ.get('PUBLIC_BASE_URL')
        or os.environ.get('RENDER_EXTERNAL_URL')
        or os.environ.get('EXTERNAL_URL')
    )

    if not base_url and has_request_context():
        base_url = request.url_root.rstrip('/')

    if not base_url:
        # Fallback genérico para ejecución fuera de contexto de request
        base_url = app.config.get('SERVER_NAME')
        if base_url:
            scheme = 'https' if app.config.get('PREFERRED_URL_SCHEME') == 'https' else 'http'
            base_url = f"{scheme}://{base_url}"
        else:
            base_url = 'http://localhost:5000'

    base_url = base_url.rstrip('/')
    
    return f"{base_url}{url_for('ofertas_publicas')}"

@app.route('/')
def index():
    # Redirigir a login si el usuario no está autenticado
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    # Si está autenticado, redirigir al panel
    return redirect(url_for('panel'))

@app.route('/clientes')
@login_required
def clientes():
    zona_id = request.args.get('zona_id', type=int)
    filtro_estado = request.args.get('filtro_estado', 'activos')  # 'activos', 'todos', 'inactivos'
    # Mantener compatibilidad con el parámetro antiguo
    mostrar_inactivos = request.args.get('mostrar_inactivos', '').lower() in {'1', 'true', 'on'}
    if mostrar_inactivos and filtro_estado == 'activos':
        filtro_estado = 'todos'
    
    filtro_codigo = (request.args.get('codigo') or '').strip()
    filtro_nombre = (request.args.get('nombre') or '').strip()

    query = Cliente.query
    if zona_id:
        query = query.filter_by(zona_id=zona_id)
    
    # Aplicar filtro de estado
    if filtro_estado == 'activos':
        query = query.filter_by(activo=True)
    elif filtro_estado == 'inactivos':
        query = query.filter_by(activo=False)
    # Si es 'todos', no aplicamos filtro de activo

    if filtro_codigo:
        query = query.filter(Cliente.codigo.ilike(f"%{filtro_codigo}%"))

    if filtro_nombre:
        query = query.filter(Cliente.nombre.ilike(f"%{filtro_nombre}%"))

    clientes = query.order_by(Cliente.nombre.asc()).all()
    
    zonas = Zona.query.all()
    return render_template(
        'clientes.html',
        clientes=clientes,
        zonas=zonas,
        zona_seleccionada=zona_id,
        filtro_estado=filtro_estado,
        filtro_codigo=filtro_codigo,
        filtro_nombre=filtro_nombre
    )


@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    zonas = Zona.query.all()

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip() or None
        nombre = (request.form.get('nombre') or '').strip()
        telefono = (request.form.get('telefono') or '').strip()
        zona_id = request.form.get('zona_id', type=int)
        email = (request.form.get('email') or '').strip() or None
        direccion = (request.form.get('direccion') or '').strip() or None
        poblacion = (request.form.get('poblacion') or '').strip() or None

        telefono = ''.join(filter(str.isdigit, telefono)) if telefono else None

        if not nombre or not telefono or not zona_id:
            flash('Nombre, teléfono y zona son obligatorios.', 'error')
            return redirect(url_for('nuevo_cliente'))

        cliente = Cliente(
            codigo=codigo,
            nombre=nombre,
            telefono=telefono,
            zona_id=zona_id,
            email=email,
            direccion=direccion,
            poblacion=poblacion,
            activo=True,
            incluir=True
        )

        try:
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente creado correctamente.', 'success')
            return redirect(url_for('clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creando cliente: {str(e)}', 'error')
            return redirect(url_for('nuevo_cliente'))

    return render_template('nuevo_cliente.html', zonas=zonas)


@app.route('/clientes/importar', methods=['POST'])
@login_required
def importar_clientes():
    file = request.files.get('archivo_clientes')
    if not file or file.filename == '':
        flash('Debe seleccionar un archivo Excel para importar', 'error')
        return redirect(url_for('clientes'))

    try:
        try:
            import pandas as pd
        except ImportError:
            flash('Pandas no está instalado en el entorno. Solicita al administrador que añada pandas al proyecto.', 'error')
            return redirect(url_for('clientes'))

        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()

        excel_data = file.read()

        read_kwargs = {'dtype': str, 'engine': 'openpyxl'} if ext == '.xlsx' else {'dtype': str}

        if ext == '.xlsx':
            df = pd.read_excel(io.BytesIO(excel_data), **read_kwargs)
        elif ext == '.xls':
            try:
                df = pd.read_excel(io.BytesIO(excel_data), dtype=str, engine='xlrd')
            except ImportError:
                df = pd.read_excel(io.BytesIO(excel_data), dtype=str)
        else:
            flash('Formato de archivo no soportado. Usa .xlsx o .xls', 'error')
            return redirect(url_for('clientes'))

        def normalize(text: str) -> str:
            replacements = {
                'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u',
            }
            clean = ''.join(replacements.get(ch, ch) for ch in text)
            clean = ''.join(ch for ch in clean if ch.isalnum())
            return clean.lower()

        header_map = {
            'codigo': 'Codigo',
            'codigocliente': 'Codigo',
            'codigoid': 'Codigo',
            'código': 'Codigo',
            'códigocliente': 'Codigo',
            'denominacion': 'Nombre',
            'nombre': 'Nombre',
            'nombrefiscal': 'Nombre',
            'telefono': 'Teléfono',
            'teléfono': 'Teléfono',
            'telefonocontacto': 'Teléfono',
            'email': 'Email',
            'correo': 'Email',
            'correoelectronico': 'Email',
            'direccion': 'Dirección',
            'dirección': 'Dirección',
            'domicilio': 'Dirección',
            'poblacion': 'Población',
            'población': 'Población',
            'localidad': 'Población',
            'zona': 'Zona',
        }

        columnas_objetivo = ["Codigo", "Nombre", "Teléfono", "Email", "Dirección", "Población", "Zona"]
        renombradas = {}
        for col in df.columns:
            key = normalize(str(col))
            destino = header_map.get(key)
            if destino:
                renombradas[col] = destino

        df = df.rename(columns=renombradas)

        if not all(col in df.columns for col in columnas_objetivo):
            flash('Las columnas del Excel no coinciden con el formato esperado.', 'error')
            return redirect(url_for('clientes'))

        registros = []
        filas_invalidas = []
        zonas_cache = {zona.nombre.strip().lower(): zona for zona in Zona.query.all()}

        def clean(value):
            if value is None:
                return None
            text = str(value).strip()
            if not text or text.lower() in {'nan', 'none'}:
                return None
            return text

        for _, row in df.iterrows():
            codigo = clean(row.get("Codigo"))
            nombre = clean(row.get("Nombre"))
            telefono_raw = clean(row.get("Teléfono"))
            if not codigo and not nombre and not telefono_raw:
                continue
            telefono = ''.join(filter(str.isdigit, telefono_raw)) if telefono_raw else None

            if not codigo or not nombre or not telefono:
                filas_invalidas.append({
                    'fila_excel': row.name + 2,
                    'codigo': codigo or '',
                    'nombre': nombre or '',
                    'telefono': telefono_raw or ''
                })
                continue

            email = clean(row.get("Email"))
            direccion = clean(row.get("Dirección"))
            poblacion = clean(row.get("Población"))
            zona_nombre = clean(row.get("Zona"))

            zona_id = None
            if zona_nombre:
                key = zona_nombre.lower()
                zona = zonas_cache.get(key)
                if not zona:
                    zona = Zona(nombre=zona_nombre)
                    db.session.add(zona)
                    db.session.flush()
                    zonas_cache[key] = zona
                zona_id = zona.id
            else:
                zona = Zona.query.first()
                if not zona:
                    zona = Zona(nombre='General')
                    db.session.add(zona)
                    db.session.flush()
                zona_id = zona.id

            registros.append({
                'codigo': codigo,
                'nombre': nombre,
                'telefono': telefono,
                'email': email,
                'direccion': direccion,
                'poblacion': poblacion,
                'zona_id': zona_id
            })

        Cliente.query.delete()
        db.session.flush()

        for data in registros:
            cliente = Cliente(
                codigo=data['codigo'],
                nombre=data['nombre'],
                telefono=data['telefono'],
                email=data['email'],
                direccion=data['direccion'],
                poblacion=data['poblacion'],
                zona_id=data['zona_id'],
                activo=True,
                incluir=True
            )
            db.session.add(cliente)

        db.session.commit()
        if filas_invalidas:
            detalles = '; '.join(
                f"fila {item['fila_excel']} (Código: {item['codigo']}, Nombre: {item['nombre']}, Teléfono original: {item['telefono']})"
                for item in filas_invalidas[:5]
            )
            if len(filas_invalidas) > 5:
                detalles += f"; … y {len(filas_invalidas) - 5} fila(s) más"
            flash(
                f'Se importaron {len(registros)} clientes. Se omitieron {len(filas_invalidas)} fila(s) sin datos obligatorios: {detalles}',
                'warning'
            )
        else:
            flash(f'Se importaron {len(registros)} clientes correctamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error importando clientes: {str(e)}', 'error')

    return redirect(url_for('clientes'))

@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    
    if request.method == 'POST':
        cliente.codigo = request.form.get('codigo', '').strip() or None
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


@app.post('/clientes/<int:cliente_id>/toggle')
@login_required
def toggle_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    field = request.form.get('field')
    next_url = request.form.get('next') or request.referrer or url_for('clientes')

    if field == 'activo':
        cliente.activo = not cliente.activo
        # Asegurar que incluir siempre sea True (campo reservado para futuro)
        cliente.incluir = True
        if not cliente.activo:
            mensaje = f"Cliente {cliente.nombre} marcado como inactivo."
            categoria = 'warning'
        else:
            mensaje = f"Cliente {cliente.nombre} marcado como activo."
            categoria = 'success'
    else:
        flash('Acción no válida.', 'error')
        return redirect(next_url)

    try:
        db.session.commit()
        flash(mensaje, categoria)
    except Exception as e:
        db.session.rollback()
        flash(f'Error actualizando cliente: {str(e)}', 'error')

    return redirect(next_url)

@app.route('/clientes/eliminar/<int:cliente_id>', methods=['POST'])
@login_required
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
@login_required
def zonas():
    zonas = Zona.query.order_by(Zona.nombre.asc()).all()
    zonas_data = [{'id': zona.id, 'nombre': zona.nombre} for zona in zonas]
    return render_template('zonas.html', zonas=zonas, zonas_data=zonas_data)


@app.route('/zonas/nueva', methods=['POST'])
@login_required
def crear_zona():
    nombre = (request.form.get('nombre') or '').strip()
    descripcion = (request.form.get('descripcion') or '').strip() or None

    if not nombre:
        flash('El nombre de la zona es obligatorio', 'error')
        return redirect(url_for('zonas'))

    try:
        if Zona.query.filter(db.func.lower(Zona.nombre) == nombre.lower()).first():
            flash('Ya existe una zona con ese nombre', 'error')
            return redirect(url_for('zonas'))

        zona = Zona(nombre=nombre, descripcion=descripcion)
        db.session.add(zona)
        db.session.commit()
        flash(f'Zona "{nombre}" creada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creando zona: {str(e)}', 'error')

    return redirect(url_for('zonas'))

@app.route('/zonas/editar/<int:zona_id>', methods=['GET', 'POST'])
@login_required
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
@login_required
def eliminar_zona(zona_id):
    zona = Zona.query.get_or_404(zona_id)

    zona_destino_id = request.form.get('zona_destino', type=int)

    try:
        clientes_en_zona = Cliente.query.filter_by(zona_id=zona_id).count()

        if clientes_en_zona > 0:
            if not zona_destino_id:
                flash('La zona tiene clientes asignados. Debe seleccionar una zona destino para reasignarlos.', 'error')
                return redirect(url_for('zonas'))

            if zona_destino_id == zona_id:
                flash('La zona destino no puede ser la misma que se desea eliminar.', 'error')
                return redirect(url_for('zonas'))

            zona_destino = Zona.query.get(zona_destino_id)
            if not zona_destino:
                flash('La zona destino seleccionada no existe.', 'error')
                return redirect(url_for('zonas'))

            Cliente.query.filter_by(zona_id=zona_id).update({'zona_id': zona_destino_id})

        db.session.delete(zona)
        db.session.commit()

        if clientes_en_zona > 0:
            flash(f'Zona {zona.nombre} eliminada y {clientes_en_zona} cliente(s) reasignado(s).', 'success')
        else:
            flash(f'Zona {zona.nombre} eliminada exitosamente.', 'success')
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
@login_required
def mensajes():
    plantillas = MensajePlantilla.query.filter_by(activo=True).all()
    return render_template('mensajes.html', plantillas=plantillas)


@app.route('/mensajes/nuevo', methods=['GET', 'POST'])
@login_required
def nueva_plantilla():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        contenido = (request.form.get('contenido') or '').strip()

        if not nombre or not contenido:
            flash('El nombre y el contenido de la plantilla son obligatorios.', 'error')
            return redirect(url_for('nueva_plantilla'))

        plantilla = MensajePlantilla(nombre=nombre, contenido=contenido, activo=True)

        try:
            db.session.add(plantilla)
            db.session.commit()
            flash('Plantilla creada correctamente.', 'success')
            return redirect(url_for('mensajes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creando plantilla: {str(e)}', 'error')
            return redirect(url_for('nueva_plantilla'))

    return render_template('nueva_plantilla.html')

@app.route('/enviar_masivo', methods=['GET', 'POST'])
@login_required
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
            contexto_mensaje = _FormatoSeguro({
                "nombre_cliente": cliente.nombre,
                "cliente_nombre": cliente.nombre,
                "zona": zona.nombre,
                "zona_nombre": zona.nombre,
                "enlace_web": "",
                "link_ofertas": "",
                "telefono_cliente": cliente.telefono,
                "cliente_telefono": cliente.telefono,
            })

            # Personalizar mensaje con datos del cliente
            mensaje_personalizado = plantilla.contenido.format_map(contexto_mensaje)
            
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
@login_required
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
@login_required
def programaciones():
    programaciones_list = ProgramacionMasiva.query.order_by(ProgramacionMasiva.created_at.desc()).all()
    zonas = Zona.query.all()
    plantillas = MensajePlantilla.query.filter_by(activo=True).all()
    return render_template('programaciones.html', 
                         programaciones=programaciones_list,
                         zonas=zonas,
                         plantillas=plantillas)

@app.route('/programaciones/nueva', methods=['POST'])
@login_required
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
            activo=True,
            ultima_ejecucion=None
        )
        db.session.add(programacion)
        db.session.commit()
        flash('Programación creada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creando la programación: {str(e)}', 'error')
    
    return redirect(url_for('programaciones'))

@app.route('/programaciones/<int:id>/editar', methods=['GET', 'POST'])
@login_required
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
            if programacion.hora != hora:
                programacion.ultima_ejecucion = None
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
@login_required
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
@login_required
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
@login_required
def ofertas():
    ofertas = Oferta.query.filter_by(activa=True).order_by(Oferta.created_at.desc()).all()
    return render_template('ofertas_admin.html', ofertas=ofertas)

@app.route('/ofertas/nueva', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
def toggle_oferta(id):
    oferta = Oferta.query.get_or_404(id)
    oferta.activa = not oferta.activa
    db.session.commit()
    
    estado = "activada" if oferta.activa else "desactivada"
    flash(f'Oferta {estado} exitosamente', 'success')
    return redirect(url_for('ofertas'))


# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('panel'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Por favor, completa todos los campos.', 'error')
            return render_template('login.html')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if not usuario:
            flash('Usuario o contraseña incorrectos.', 'error')
        elif not usuario.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
        elif usuario.check_password(password):
            login_user(usuario)
            next_page = request.args.get('next')
            flash(f'¡Bienvenido, {usuario.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('panel'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/reset-password-admin')
def reset_password_admin():
    """Ruta temporal para resetear la contraseña del administrador"""
    try:
        # Asegurar que la tabla existe
        db.create_all()
        
        usuario = Usuario.query.filter_by(username='jmurillo').first()
        if usuario:
            usuario.set_password('TxMb-7-0')
            usuario.activo = True
            db.session.commit()
            
            # Verificar que se guardó
            usuario_verificado = Usuario.query.filter_by(username='jmurillo').first()
            return jsonify({
                'status': 'success',
                'message': f'Contraseña del usuario jmurillo actualizada correctamente. Nueva contraseña: TxMb-7-0. Usuario activo: {usuario_verificado.activo if usuario_verificado else "No encontrado"}',
                'usuario_id': usuario_verificado.id if usuario_verificado else None
            })
        else:
            # Crear el usuario si no existe
            usuario = Usuario(username='jmurillo', activo=True)
            usuario.set_password('TxMb-7-0')
            db.session.add(usuario)
            db.session.flush()  # Para obtener el ID
            db.session.commit()
            
            # Verificar que se creó
            usuario_verificado = Usuario.query.filter_by(username='jmurillo').first()
            if usuario_verificado:
                return jsonify({
                    'status': 'success',
                    'message': f'Usuario jmurillo creado correctamente. Contraseña: TxMb-7-0. ID: {usuario_verificado.id}',
                    'usuario_id': usuario_verificado.id
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'El usuario se intentó crear pero no se encontró después del commit.'
                }), 500
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

# Rutas para la web pública
@app.route('/panel')
@login_required
def panel():
    total_conversaciones = WhatsAppConversation.query.count()
    total_clientes = Cliente.query.filter_by(activo=True).count()
    total_ofertas = Oferta.query.filter_by(activa=True).count()
    return render_template(
        'panel.html',
        total_conversaciones=total_conversaciones,
        total_clientes=total_clientes,
        total_ofertas=total_ofertas,
    )


@app.route('/panel/envios-masivos')
@login_required
def panel_envios_masivos():
    total_clientes = Cliente.query.filter_by(activo=True).count()
    total_zonas = Zona.query.count()
    total_plantillas = MensajePlantilla.query.count()
    total_historial = MensajeEnviado.query.count()
    total_programaciones = ProgramacionMasiva.query.count()
    return render_template(
        'panel_envios.html',
        total_clientes=total_clientes,
        total_zonas=total_zonas,
        total_plantillas=total_plantillas,
        total_historial=total_historial,
        total_programaciones=total_programaciones,
    )

@app.route('/publico/ofertas')
def ofertas_publicas():
    ofertas = Oferta.query.filter_by(activa=True).order_by(Oferta.created_at.desc()).all()
    return render_template('ofertas_publicas.html', ofertas=ofertas)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rutas para configuración de Green-API
@app.route('/configuracion')
@login_required
def configuracion():
    # Solo jmurillo puede acceder a configuración
    if current_user.username != 'jmurillo':
        flash('No tienes permisos para acceder a esta sección.', 'error')
        return redirect(url_for('panel'))
    
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
    
    # Obtener lista de usuarios
    usuarios = Usuario.query.order_by(Usuario.username.asc()).all()
    
    return render_template('configuracion.html', conectado=conectado, mensaje=mensaje, config=config_data, usuarios=usuarios)

@app.route('/configuracion/green-api', methods=['GET', 'POST'])
@login_required
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
@login_required
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

# Rutas para gestión de usuarios (solo jmurillo)
@app.route('/configuracion/usuarios')
@login_required
def gestion_usuarios():
    """Lista de usuarios - solo accesible para jmurillo"""
    if current_user.username != 'jmurillo':
        flash('No tienes permisos para acceder a esta sección.', 'error')
        return redirect(url_for('panel'))
    
    usuarios = Usuario.query.order_by(Usuario.username.asc()).all()
    return render_template('gestion_usuarios.html', usuarios=usuarios)

@app.route('/configuracion/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_usuario():
    """Crear nuevo usuario - solo accesible para jmurillo"""
    if current_user.username != 'jmurillo':
        flash('No tienes permisos para acceder a esta sección.', 'error')
        return redirect(url_for('panel'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        color = request.form.get('color', '#007bff')
        activo = request.form.get('activo') == 'on'
        
        if not username or not password:
            flash('El usuario y la contraseña son obligatorios.', 'error')
            return render_template('nuevo_usuario.html')
        
        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(username=username).first():
            flash('El usuario ya existe.', 'error')
            return render_template('nuevo_usuario.html')
        
        try:
            usuario = Usuario(username=username, activo=activo, color=color)
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            flash(f'Usuario {username} creado correctamente.', 'success')
            return redirect(url_for('gestion_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creando usuario: {str(e)}', 'error')
    
    return render_template('nuevo_usuario.html')

@app.route('/configuracion/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    """Editar usuario - solo accesible para jmurillo"""
    if current_user.username != 'jmurillo':
        flash('No tienes permisos para acceder a esta sección.', 'error')
        return redirect(url_for('panel'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        color = request.form.get('color', '#007bff')
        activo = request.form.get('activo') == 'on'
        
        if not username:
            flash('El usuario es obligatorio.', 'error')
            return render_template('editar_usuario.html', usuario=usuario)
        
        # Verificar si el username ya existe en otro usuario
        otro_usuario = Usuario.query.filter_by(username=username).first()
        if otro_usuario and otro_usuario.id != usuario.id:
            flash('El usuario ya existe.', 'error')
            return render_template('editar_usuario.html', usuario=usuario)
        
        try:
            usuario.username = username
            usuario.color = color
            usuario.activo = activo
            
            # Solo actualizar contraseña si se proporcionó una nueva
            if password:
                usuario.set_password(password)
            
            db.session.commit()
            flash(f'Usuario {username} actualizado correctamente.', 'success')
            return redirect(url_for('gestion_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando usuario: {str(e)}', 'error')
    
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/configuracion/usuarios/<int:usuario_id>/toggle', methods=['POST'])
@login_required
def toggle_usuario(usuario_id):
    """Activar/desactivar usuario - solo accesible para jmurillo"""
    if current_user.username != 'jmurillo':
        flash('No tienes permisos para acceder a esta sección.', 'error')
        return redirect(url_for('panel'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # No permitir desactivarse a sí mismo
    if usuario.id == current_user.id:
        flash('No puedes desactivar tu propio usuario.', 'error')
        return redirect(url_for('gestion_usuarios'))
    
    try:
        usuario.activo = not usuario.activo
        db.session.commit()
        estado = 'activado' if usuario.activo else 'desactivado'
        flash(f'Usuario {usuario.username} {estado} correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error actualizando usuario: {str(e)}', 'error')
    
    return redirect(url_for('gestion_usuarios'))

@app.route('/configuracion/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
@login_required
def eliminar_usuario(usuario_id):
    """Eliminar usuario - solo accesible para jmurillo"""
    if current_user.username != 'jmurillo':
        flash('No tienes permisos para acceder a esta sección.', 'error')
        return redirect(url_for('panel'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # No permitir eliminarse a sí mismo
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propio usuario.', 'error')
        return redirect(url_for('gestion_usuarios'))
    
    try:
        username = usuario.username
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuario {username} eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error eliminando usuario: {str(e)}', 'error')
    
    return redirect(url_for('gestion_usuarios'))

@app.route('/diagnostico-green-api')
@login_required
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
    # Rate limiting: Protección contra spam
    client_ip = _get_client_ip()
    if not _check_rate_limit(client_ip):
        print(f"⚠️ Rate limit excedido para IP: {client_ip}")
        return jsonify({
            'status': 'error',
            'message': 'Rate limit exceeded. Too many requests.'
        }), 429  # HTTP 429: Too Many Requests
    
    try:
        data = request.get_json(silent=True) or {}
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Log del payload completo para debugging
        print(f"🔍 Webhook recibido - keys: {list(data.keys())}")
        if 'body' in data:
            print(f"🔍 Body keys: {list(data.get('body', {}).keys())}")
        
        # Procesar mensaje recibido (admite payloads antiguos y nuevos)
        mensaje_data = data.get('body') or data
        
        if mensaje_data.get('typeWebhook') == 'incomingMessageReceived':
            print(f"📥 Mensaje entrante detectado")
            # Extraer información del mensaje
            message_data = mensaje_data.get('messageData', {})
            sender_data = mensaje_data.get('senderData', {})
            
            # Obtener número de teléfono del remitente
            telefono_remitente = sender_data.get('sender', '').replace('@c.us', '')
            
            # Obtener el mensaje
            mensaje_texto = ''
            tipo_mensaje = 'texto'
            archivo_url = None
            
            print(f"🔍 message_data keys: {list(message_data.keys())}")
            type_message = message_data.get('typeMessage', '').lower()  # Convertir a minúsculas para comparación
            print(f"🔍 typeMessage: '{message_data.get('typeMessage', '')}' (normalizado: '{type_message}')")
            
            if 'textMessageData' in message_data:
                mensaje_texto = message_data['textMessageData'].get('textMessage', '')
                tipo_mensaje = 'texto'
            elif 'extendedTextMessageData' in message_data:
                mensaje_texto = message_data['extendedTextMessageData'].get('text', '')
                tipo_mensaje = 'texto'
            elif 'imageMessageData' in message_data:
                mensaje_texto = message_data['imageMessageData'].get('caption', '') or ''
                tipo_mensaje = 'imagen'
                # Intentar obtener downloadUrl
                archivo_url = message_data['imageMessageData'].get('downloadUrl', '')
                # Obtener idMessage desde diferentes ubicaciones posibles
                id_message = mensaje_data.get('idMessage') or data.get('idMessage') or ''
                print(f"📷 Imagen recibida (imageMessageData) - downloadUrl: {archivo_url[:50] if archivo_url else 'No disponible'}, idMessage: {id_message}, caption: '{mensaje_texto}'")
                # Si no hay caption, usar texto vacío (la imagen se mostrará por media_type)
                if not mensaje_texto:
                    mensaje_texto = '[Imagen]'
                # Si no hay downloadUrl, el external_id se usará para descargar después
            elif 'fileMessageData' in message_data:
                # Green-API puede enviar diferentes tipos de media como fileMessageData
                file_data = message_data.get('fileMessageData', {})
                # Verificar el tipo de mensaje según typeMessage
                if type_message == 'image':
                    mensaje_texto = file_data.get('caption', '') or ''
                    tipo_mensaje = 'imagen'
                    print(f"📷 Imagen recibida (fileMessageData) - typeMessage: 'image'")
                    if not mensaje_texto:
                        mensaje_texto = '[Imagen]'
                elif type_message == 'video':
                    mensaje_texto = file_data.get('caption', '') or ''
                    tipo_mensaje = 'video'
                    print(f"🎥 Video recibido (fileMessageData) - typeMessage: 'video'")
                    if not mensaje_texto:
                        mensaje_texto = '[Video]'
                elif type_message == 'audio' or type_message == 'ptt':  # ptt = push-to-talk (nota de voz)
                    mensaje_texto = ''
                    tipo_mensaje = 'audio'
                    print(f"🎵 Audio recibido (fileMessageData) - typeMessage: '{type_message}'")
                    mensaje_texto = '[Audio]'
                else:
                    mensaje_texto = file_data.get('caption', '') or ''
                    tipo_mensaje = 'documento'  # Por defecto, tratar como documento
                    print(f"📎 Archivo recibido (fileMessageData) - typeMessage: '{type_message}'")
                    if not mensaje_texto:
                        mensaje_texto = '[Archivo]'
                
                # Intentar obtener downloadUrl
                archivo_url = file_data.get('downloadUrl', '')
                # Obtener idMessage desde diferentes ubicaciones posibles
                id_message = mensaje_data.get('idMessage') or data.get('idMessage') or ''
                print(f"📎 fileMessageData - downloadUrl: {archivo_url[:50] if archivo_url else 'No disponible'}, idMessage: {id_message}, caption: '{mensaje_texto}'")
            elif 'documentMessageData' in message_data:
                mensaje_texto = message_data['documentMessageData'].get('caption', '')
                tipo_mensaje = 'documento'
                archivo_url = message_data['documentMessageData'].get('downloadUrl', '')
            elif 'audioMessageData' in message_data:
                mensaje_texto = '[Audio]'
                tipo_mensaje = 'audio'
                archivo_url = message_data['audioMessageData'].get('downloadUrl', '')
            elif 'videoMessageData' in message_data:
                mensaje_texto = message_data['videoMessageData'].get('caption', '') or ''
                tipo_mensaje = 'video'
                archivo_url = message_data['videoMessageData'].get('downloadUrl', '')
                if not mensaje_texto:
                    mensaje_texto = '[Video]'
            
            # Buscar si el remitente es un cliente existente
            cliente_existente = Cliente.query.filter_by(telefono=telefono_remitente).first()
            
            # Obtener chat_id_full antes de usarlo
            chat_id_full = sender_data.get('chatId') or sender_data.get('sender')
            if not chat_id_full and telefono_remitente:
                try:
                    chat_id_full = _normalize_chat_id(telefono_remitente)
                except ValueError:
                    chat_id_full = ''
            
            # Crear registro del mensaje recibido
            chat_display_name = sender_data.get('chatName') or sender_data.get('senderName') or chat_id_full or telefono_remitente

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

            if chat_id_full:
                timestamp = mensaje_data.get('timestamp') or message_data.get('timestamp') or data.get('timestamp')
                if timestamp:
                    try:
                        sent_at = datetime.utcfromtimestamp(timestamp)
                    except Exception:
                        sent_at = datetime.utcnow()
                else:
                    sent_at = datetime.now(timezone.utc)
                try:
                    # Obtener idMessage desde diferentes ubicaciones posibles (puede estar en mensaje_data o data)
                    id_message = mensaje_data.get('idMessage') or data.get('idMessage') or ''
                    # Si es una imagen y no tenemos idMessage, intentar obtenerlo del imageMessageData o fileMessageData
                    if tipo_mensaje == 'imagen' and not id_message:
                        image_data = message_data.get('imageMessageData') or message_data.get('fileMessageData', {})
                        id_message = image_data.get('idMessage') or ''
                    
                    print(f"🔍 Antes de registrar - tipo_mensaje: {tipo_mensaje}, id_message: {id_message}, archivo_url: {archivo_url[:50] if archivo_url else 'N/A'}")
                    
                    _register_incoming_whatsapp_message(
                        chat_id_full,
                        mensaje_texto,
                        contact_name=chat_display_name,
                        sent_at=sent_at,
                        external_id=id_message if id_message else None,
                        media_type=tipo_mensaje if tipo_mensaje != 'texto' else None,
                        media_url=archivo_url if archivo_url else None,
                    )
                    if tipo_mensaje != 'texto':
                        print(f"📎 Media registrado - tipo: {tipo_mensaje}, external_id: {id_message or 'N/A'}, media_url: {archivo_url[:50] if archivo_url else 'N/A'}...")
                    else:
                        print(f"✅ Mensaje de texto registrado correctamente")
                except Exception as exc:  # noqa: BLE001
                    print(f"⚠️ No se pudo registrar la conversación avanzada: {exc}")
                    import traceback
                    print(f"⚠️ Traceback: {traceback.format_exc()}")

            db.session.commit()
            
            # Log mejorado con información del tipo de mensaje
            tipo_info = f" ({tipo_mensaje})" if tipo_mensaje != 'texto' else ""
            archivo_info = f" - URL: {archivo_url[:50]}..." if archivo_url else ""
            print(f"✅ Mensaje recibido de {telefono_remitente}{tipo_info}: {mensaje_texto[:50]}...{archivo_info}")
            
            return jsonify({'status': 'success', 'message': 'Message processed'}), 200
        
        return jsonify({'status': 'ignored', 'message': 'Not an incoming message'}), 200
        
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/mensajes-recibidos')
@login_required
def mensajes_recibidos():
    """Página para ver mensajes recibidos"""
    # Obtener mensajes no leídos primero, luego los leídos
    mensajes_no_leidos = MensajeRecibido.query.filter_by(leido=False).order_by(MensajeRecibido.fecha_recepcion.desc()).all()
    mensajes_leidos = MensajeRecibido.query.filter_by(leido=True).order_by(MensajeRecibido.fecha_recepcion.desc()).limit(50).all()
    
    return render_template('mensajes_recibidos.html', 
                         mensajes_no_leidos=mensajes_no_leidos,
                         mensajes_leidos=mensajes_leidos)

@app.route('/mensajes-recibidos/<int:mensaje_id>/marcar-leido', methods=['POST'])
@login_required
def marcar_mensaje_leido(mensaje_id):
    """Marcar un mensaje como leído"""
    mensaje = MensajeRecibido.query.get_or_404(mensaje_id)
    mensaje.leido = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/mensajes-recibidos/<int:mensaje_id>/responder', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def whatsapp_dashboard():
    # Ordenar por el último mensaje (sent_at) en lugar de updated_at
    # Usar subconsulta para obtener el último sent_at de cada conversación
    last_message_subquery = db.session.query(
        WhatsAppMessage.conversation_id,
        func.max(WhatsAppMessage.sent_at).label('last_sent_at')
    ).group_by(WhatsAppMessage.conversation_id).subquery()
    
    conversaciones = db.session.query(WhatsAppConversation)\
        .outerjoin(
            last_message_subquery,
            WhatsAppConversation.id == last_message_subquery.c.conversation_id
        )\
        .order_by(
            func.coalesce(last_message_subquery.c.last_sent_at, WhatsAppConversation.updated_at).desc(),
            WhatsAppConversation.id.desc()
        )\
        .all()
    return render_template('whatsapp/index.html', conversaciones=conversaciones)


@app.route('/whatsapp/conversaciones/nueva', methods=['GET', 'POST'])
@login_required
def whatsapp_new_conversation():
    # Obtener todos los clientes activos para mostrar en el selector
    clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre.asc()).all()
    
    if request.method == 'POST':
        raw_number = (request.form.get('contact_number') or '').strip()
        contact_name = (request.form.get('contact_name') or '').strip() or None
        initial_message = (request.form.get('initial_message') or '').strip()
        
        # Si se seleccionó un cliente del selector
        selected_cliente_id = request.form.get('selected_cliente_id', type=int)
        if selected_cliente_id:
            cliente = Cliente.query.get(selected_cliente_id)
            if cliente:
                raw_number = cliente.telefono
                if not contact_name:
                    contact_name = cliente.nombre

        if not raw_number:
            flash('Debes indicar un número de WhatsApp', 'error')
            return render_template('whatsapp/new_conversation.html', clientes=clientes)

        try:
            chat_id = _normalize_chat_id(raw_number)
        except ValueError as exc:
            flash(str(exc), 'error')
            return render_template('whatsapp/new_conversation.html', clientes=clientes)

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
                return render_template('whatsapp/new_conversation.html', clientes=clientes)

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

    return render_template('whatsapp/new_conversation.html', clientes=clientes)


@app.route('/whatsapp/conversaciones/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
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
            usuario_id=current_user.id if current_user.is_authenticated else None,
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
    # Optimización: Usar subconsulta para obtener el último mensaje de cada conversación
    # y ordenar por el sent_at del último mensaje (no por updated_at)
    
    # Subconsulta para obtener el último sent_at de cada conversación
    last_message_subquery = db.session.query(
        WhatsAppMessage.conversation_id,
        func.max(WhatsAppMessage.sent_at).label('last_sent_at')
    ).group_by(WhatsAppMessage.conversation_id).subquery()
    
    # Obtener conversaciones ordenadas por el último mensaje (sent_at)
    conversations = db.session.query(WhatsAppConversation)\
        .outerjoin(
            last_message_subquery,
            WhatsAppConversation.id == last_message_subquery.c.conversation_id
        )\
        .order_by(
            func.coalesce(last_message_subquery.c.last_sent_at, WhatsAppConversation.updated_at).desc(),
            WhatsAppConversation.id.desc()
        )\
        .all()
    
    # Pre-cargar unread counts con una sola query para todas las conversaciones
    conversation_ids = [c.id for c in conversations]
    unread_counts = {}
    if conversation_ids:
        unread_results = db.session.query(
            WhatsAppMessage.conversation_id,
            func.count(WhatsAppMessage.id).label('unread')
        ).filter(
            WhatsAppMessage.conversation_id.in_(conversation_ids),
            WhatsAppMessage.sender_type == 'customer',
            WhatsAppMessage.is_read == False
        ).group_by(WhatsAppMessage.conversation_id).all()
        
        unread_counts = {conv_id: count for conv_id, count in unread_results}
    
    # Pre-cargar últimos mensajes con una sola query
    last_messages = {}
    if conversation_ids:
        # Obtener el último mensaje de cada conversación
        last_msg_subquery = db.session.query(
            WhatsAppMessage.conversation_id,
            func.max(WhatsAppMessage.sent_at).label('max_sent_at'),
            func.max(WhatsAppMessage.id).label('max_id')
        ).filter(
            WhatsAppMessage.conversation_id.in_(conversation_ids)
        ).group_by(WhatsAppMessage.conversation_id).subquery()
        
        last_msgs = db.session.query(WhatsAppMessage)\
            .join(
                last_msg_subquery,
                and_(
                    WhatsAppMessage.conversation_id == last_msg_subquery.c.conversation_id,
                    WhatsAppMessage.sent_at == last_msg_subquery.c.max_sent_at,
                    WhatsAppMessage.id == last_msg_subquery.c.max_id
                )
            )\
            .all()
        
        last_messages = {msg.conversation_id: msg for msg in last_msgs}
    
    # Pre-cargar últimos mensajes de agentes
    last_agent_messages = {}
    if conversation_ids:
        last_agent_subquery = db.session.query(
            WhatsAppMessage.conversation_id,
            func.max(WhatsAppMessage.sent_at).label('max_sent_at'),
            func.max(WhatsAppMessage.id).label('max_id')
        ).filter(
            WhatsAppMessage.conversation_id.in_(conversation_ids),
            WhatsAppMessage.sender_type == 'agent'
        ).group_by(WhatsAppMessage.conversation_id).subquery()
        
        last_agents = db.session.query(WhatsAppMessage)\
            .options(joinedload(WhatsAppMessage.usuario))\
            .join(
                last_agent_subquery,
                and_(
                    WhatsAppMessage.conversation_id == last_agent_subquery.c.conversation_id,
                    WhatsAppMessage.sent_at == last_agent_subquery.c.max_sent_at,
                    WhatsAppMessage.id == last_agent_subquery.c.max_id
                )
            )\
            .all()
        
        last_agent_messages = {msg.conversation_id: msg for msg in last_agents}
    
    # Construir respuesta optimizada sin N+1 queries
    data = []
    for conv in conversations:
        last_msg = last_messages.get(conv.id)
        last_agent = last_agent_messages.get(conv.id)
        
        last_usuario = None
        if last_agent and last_agent.usuario:
            last_usuario = {
                "id": last_agent.usuario.id,
                "username": last_agent.usuario.username,
                "color": last_agent.usuario.color or "#007bff",
            }
        
        data.append({
            "id": conv.id,
            "display_name": conv.contact_name or _chat_display(conv.contact_number),
            "contact_number": conv.contact_number,
            "last_message_text": last_msg.message_text if last_msg else "",
            "last_message_sender": last_msg.sender_type if last_msg else None,
            "last_media_type": last_msg.media_type if last_msg else None,
            "last_usuario": last_usuario,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "updated_at_human": _to_local_time(conv.updated_at).strftime("%d/%m/%Y %H:%M") if conv.updated_at else "",
            "unread_count": unread_counts.get(conv.id, 0),
            "url": url_for("whatsapp_conversation_detail", conversation_id=conv.id),
        })
    
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
        msg_dict = _message_to_dict(message)
        # Log para debugging de mensajes con media
        if message.media_type:
            print(f"📎 API devolviendo mensaje con media - ID: {message.id}, tipo: {message.media_type}, external_id: {message.external_id}, media_url: {message.media_url}, media_route: {msg_dict.get('media_route')}")
        serialized.append(msg_dict)
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
        raw_name = (
            contact.get('name')
            or contact.get('contactName')
            or contact.get('contactNameShort')
            or contact.get('chatName')
            or (contact.get('groupMetadata') or {}).get('subject')
            or contact.get('pushname')
            or ""
        )
        normalized.append({
            'id': contact.get('id'),
            'name': raw_name.strip() if isinstance(raw_name, str) else raw_name,
            'type': contact.get('type'),
            'category': contact.get('category'),
            'chat_id': contact.get('id'),
        })

    return jsonify({'contacts': normalized})


@app.route('/whatsapp/health')
def whatsapp_health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/whatsapp/debug/mensajes')
@login_required
def whatsapp_debug_mensajes():
    """Ruta de diagnóstico para ver mensajes con media"""
    # Obtener los últimos 10 mensajes con media_type
    mensajes_con_media = WhatsAppMessage.query.filter(
        WhatsAppMessage.media_type.isnot(None)
    ).order_by(WhatsAppMessage.id.desc()).limit(10).all()
    
    resultado = []
    for msg in mensajes_con_media:
        resultado.append({
            'id': msg.id,
            'conversation_id': msg.conversation_id,
            'sender_type': msg.sender_type,
            'message_text': msg.message_text,
            'media_type': msg.media_type,
            'media_url': msg.media_url,
            'external_id': msg.external_id,
            'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
            'tiene_media_route': bool(msg.media_url or msg.external_id),
        })
    
    return jsonify({
        'total': len(resultado),
        'mensajes': resultado
    })


@app.route('/whatsapp/media/<int:message_id>')
def whatsapp_media(message_id: int):
    message = WhatsAppMessage.query.get_or_404(message_id)

    if not message.media_url and not message.external_id:
        abort(404)

    # Si media_url es un marcador temporal (id:xxx), extraer el id
    media_url = message.media_url
    if media_url and media_url.startswith('id:'):
        # Si es un marcador, usar external_id directamente
        pass
    elif media_url and not media_url.startswith('http'):
        # Si no es una URL válida, intentar usar external_id
        media_url = None

    try:
        if media_url and not media_url.startswith('id:'):
            proxied = requests.get(media_url, timeout=30)
            proxied.raise_for_status()
            mime_type = proxied.headers.get('Content-Type', 'application/octet-stream')
            return Response(proxied.content, mimetype=mime_type)
    except requests.exceptions.RequestException:
        pass

    # Si no se pudo obtener desde media_url, intentar descargar usando external_id
    try:
        api_url, api_token, instance_id = _green_api_credentials()
    except Exception:
        abort(404)

    # Usar external_id o extraer de media_url si es un marcador
    id_message = message.external_id
    if not id_message and media_url and media_url.startswith('id:'):
        id_message = media_url.replace('id:', '')

    if not id_message:
        abort(404)

    try:
        download_endpoint = f"{api_url}/waInstance{instance_id}/downloadFile/{api_token}"
        resp = requests.get(download_endpoint, params={'idMessage': id_message}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        file_data_base64 = payload.get('fileData')
        if not file_data_base64:
            abort(404)
        data = base64.b64decode(file_data_base64)
        mime_type = payload.get('mimeType', 'application/octet-stream')
        return Response(data, mimetype=mime_type)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error descargando media: {e}")
        abort(404)

# Ruta para polling de mensajes (respaldo al webhook)
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
