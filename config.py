# Configuración para producción en Render
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env (solo en desarrollo local)
# En producción (Render), las variables se cargan desde las variables de entorno del sistema
try:
    load_dotenv()
except UnicodeDecodeError:
    # Si hay error de codificación, intentar con diferentes codificaciones
    import codecs
    try:
        # Intentar con encoding por defecto de Windows
        with codecs.open('.env', 'r', encoding='utf-8-sig') as f:
            content = f.read()
        with codecs.open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        load_dotenv()
    except Exception as e:
        print(f"⚠️ Advertencia: No se pudo cargar .env: {e}")
        print("   Continuando con variables de entorno del sistema...")

# URL de base de datos PostgreSQL por defecto (para desarrollo local)
# Formato: postgresql://usuario:contraseña@host:5432/nombre_bd
# IMPORTANTE: Reemplaza esta URL con la de tu base de datos PostgreSQL
# Ejemplo: 'postgresql://usuario:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/nombre_bd'
DEFAULT_DATABASE_URL = 'postgresql://usuario:contraseña@localhost:5432/nombre_bd'

# Configuración de la base de datos para producción - SOLO PostgreSQL
# Primero intenta variable de entorno, luego usa la URL por defecto
DATABASE_URL = os.environ.get('DATABASE_URL') or DEFAULT_DATABASE_URL

# Si es la URL por defecto sin modificar, advertir
if DATABASE_URL == DEFAULT_DATABASE_URL:
    print("⚠️ ADVERTENCIA: Usando URL de base de datos por defecto en config.py")

# Validar que sea PostgreSQL
if not DATABASE_URL.startswith(('postgresql://', 'postgres://')):
    raise ValueError(
        f"❌ ERROR: DATABASE_URL debe ser una URL de PostgreSQL. "
        f"URL recibida: {DATABASE_URL[:50] if DATABASE_URL else 'None'}... "
        "Esta aplicación solo soporta PostgreSQL."
    )

# Convertir postgres:// a postgresql:// (compatibilidad con Render)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Configuración de Twilio desde variables de entorno
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', '')  # Formato: whatsapp:+34612345678

# Configuración de la aplicación
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-para-produccion-cambiar')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))

# Configuración específica para Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
