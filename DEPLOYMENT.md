# Recambios RM - Sistema de Gestión

Sistema completo de gestión para distribución de recambios con envío de mensajes WhatsApp.

## 🚀 Despliegue en Render

### Pasos para desplegar:

1. **Subir el código a GitHub**
   - Crear un repositorio en GitHub
   - Subir todos los archivos del proyecto

2. **Crear servicio en Render**
   - Ir a [render.com](https://render.com)
   - Crear un nuevo "Web Service"
   - Conectar con tu repositorio de GitHub

3. **Configurar variables de entorno en Render:**
   ```
   RENDER=true
   SECRET_KEY=tu-clave-secreta-muy-segura-aqui
   DEBUG=false
   GREEN_API_URL=https://7107.api.green-api.com
   GREEN_API_TOKEN=tu-token-real-de-green-api
   GREEN_API_INSTANCE_ID=7107349111
   GREEN_API_PHONE=34625433667
   ```

4. **Configurar la base de datos:**
   - Render creará automáticamente una base de datos PostgreSQL
   - La URL se configurará automáticamente

5. **Configurar el build:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### 📋 Características del Sistema

- ✅ **Panel de Control**: Gestión completa de clientes, zonas y mensajes
- ✅ **Envío Masivo**: Mensajes WhatsApp por zonas
- ✅ **Gestión de Ofertas**: Crear y enviar ofertas con imágenes
- ✅ **Historial**: Seguimiento de mensajes enviados
- ✅ **Web Pública**: Catálogo de ofertas para clientes
- ✅ **Green-API**: Integración completa con WhatsApp

### 🔧 Configuración Post-Despliegue

1. **Acceder al panel**: `https://tu-app.onrender.com/panel`
2. **Configurar Green-API**: Ir a Configuración y probar la conexión
3. **Crear datos iniciales**: Usar las funciones de creación de datos
4. **Subir imágenes**: Las ofertas pueden incluir imágenes

### 📱 Funcionalidades Principales

- **Gestión de Clientes**: Por zonas de reparto
- **Plantillas de Mensajes**: Sistema flexible de mensajes
- **Envío de Ofertas**: Con imágenes y precios
- **Historial Completo**: Seguimiento de todos los envíos
- **Web Pública**: Catálogo online de ofertas

### 🛠️ Tecnologías

- **Backend**: Flask, SQLAlchemy
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Base de Datos**: PostgreSQL (producción) / SQLite (desarrollo)
- **WhatsApp**: Green-API
- **Despliegue**: Render, Gunicorn

### 📞 Soporte

Para cualquier problema con el despliegue, revisar:
1. Los logs de Render
2. La configuración de variables de entorno
3. La conexión con Green-API
4. Los permisos de archivos estáticos
