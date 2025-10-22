from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from models import db, Zona, Cliente, MensajePlantilla, MensajeEnviado, Oferta, MensajeOferta
from whatsapp_sender import enviar_whatsapp, configurar_green_api, green_api_sender
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración para producción
if os.environ.get('RENDER'):
    # Configuración para Render - usar PostgreSQL
    from config import DATABASE_URL, SECRET_KEY, DEBUG, PORT
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = DEBUG
else:
    # Configuración para desarrollo local - usar SQLite local
    app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recambios.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True

# Configuración común
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crear directorio de uploads si no existe  
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Variable para controlar la inicialización
_sistema_inicializado = False

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
            # Personalizar mensaje con datos del cliente
            mensaje_personalizado = plantilla.contenido.format(
                nombre_cliente=cliente.nombre,
                zona=zona.nombre
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
    if request.method == 'POST':
        api_url = request.form.get('api_url')
        api_token = request.form.get('api_token')
        
        if not api_url or not api_token:
            flash('Debe proporcionar tanto la URL como el token de Green-API', 'error')
            return redirect(url_for('configurar_green_api_route'))
        
        # Configurar Green-API
        conectado, mensaje = configurar_green_api(api_url, api_token)
        
        if conectado:
            flash(f'Green-API configurado exitosamente: {mensaje}', 'success')
        else:
            flash(f'Error configurando Green-API: {mensaje}', 'error')
        
        return redirect(url_for('configuracion'))
    
    return render_template('configurar_green_api.html')

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
        conectado, mensaje = configurar_green_api(GREEN_API_URL, GREEN_API_TOKEN)
        
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
                from config import GREEN_API_URL, GREEN_API_TOKEN
            else:
                from green_api_config import GREEN_API_URL, GREEN_API_TOKEN
            
            if GREEN_API_TOKEN != 'TU_TOKEN_AQUI':
                conectado, mensaje = configurar_green_api(GREEN_API_URL, GREEN_API_TOKEN)
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
