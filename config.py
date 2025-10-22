# Configuración para producción en Render
import os

# Configuración de la base de datos para producción
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///recambios.db')

# Si es PostgreSQL, convertir la URL
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Configuración de Green-API desde variables de entorno
GREEN_API_URL = os.environ.get('GREEN_API_URL', 'https://7107.api.green-api.com')
GREEN_API_TOKEN = os.environ.get('GREEN_API_TOKEN', 'TU_TOKEN_AQUI')
GREEN_API_INSTANCE_ID = os.environ.get('GREEN_API_INSTANCE_ID', '7107349111')
GREEN_API_PHONE = os.environ.get('GREEN_API_PHONE', '34625433667')

# Configuración de la aplicación
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-para-produccion-cambiar')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))

# Configuración específica para Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
