# Configuración para producción en Render
import os

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

# Configuración de Green-API desde variables de entorno
GREEN_API_URL = os.environ.get('GREEN_API_URL', 'https://7107.api.green-api.com')
GREEN_API_TOKEN = os.environ.get('GREEN_API_TOKEN', '3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba')
GREEN_API_INSTANCE_ID = os.environ.get('GREEN_API_INSTANCE_ID', '7107349111')
GREEN_API_PHONE = os.environ.get('GREEN_API_PHONE', '34625433667')

# Configuración de la aplicación
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-para-produccion-cambiar')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))

# Configuración específica para Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
