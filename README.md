# Sistema de WhatsApp Masivo para Tienda de Recambios

Este sistema permite enviar mensajes de WhatsApp masivos a clientes organizados por zonas geográficas. Es ideal para tiendas de recambios que realizan repartos por zonas y quieren avisar a sus clientes antes de las visitas.

## Características

- ✅ Gestión de clientes por zonas geográficas
- ✅ Plantillas de mensajes personalizables
- ✅ Envío masivo de WhatsApp por zona
- ✅ Historial de envíos
- ✅ Interfaz web moderna y responsive
- ✅ Base de datos SQLite con SQLAlchemy
- ✅ Simulación de envío para desarrollo

## Tecnologías Utilizadas

- **Backend**: Python Flask
- **Base de datos**: SQLite con SQLAlchemy
- **Frontend**: HTML5, Bootstrap 5, Jinja2
- **WhatsApp**: Módulo personalizable para integración con APIs

## Instalación

1. **Clonar o descargar el proyecto**

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Crear la base de datos y datos de ejemplo**:
   ```bash
   python crear_datos.py
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python app.py
   ```

5. **Abrir en el navegador**:
   ```
   http://localhost:5000
   ```

## Estructura del Proyecto

```
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── whatsapp_sender.py     # Módulo para envío de WhatsApp
├── crear_datos.py         # Script para crear datos de ejemplo
├── requirements.txt       # Dependencias de Python
├── recambios.db          # Base de datos SQLite (se crea automáticamente)
└── templates/            # Plantillas HTML
    ├── base.html
    ├── index.html
    ├── clientes.html
    ├── mensajes.html
    ├── enviar_masivo.html
    ├── resultado_envio.html
    └── historial.html
```

## Funcionalidades

### 1. Gestión de Clientes
- Ver clientes por zona
- Filtrar por zona específica
- Información de contacto completa

### 2. Plantillas de Mensajes
- Mensajes predefinidos personalizables
- Variables dinámicas: `{nombre_cliente}`, `{zona}`
- Gestión de plantillas activas/inactivas

### 3. Envío Masivo
- Selección de zona y plantilla
- Envío a todos los clientes activos de la zona
- Resultados detallados del envío
- Manejo de errores

### 4. Historial
- Registro de todos los envíos
- Estado de cada mensaje (enviado/error)
- Fechas y detalles de errores

## Configuración para Producción

### Integración con WhatsApp Business API

Para usar con la API real de WhatsApp Business, modifica el archivo `whatsapp_sender.py`:

```python
from whatsapp_sender import configurar_whatsapp_real

# Configurar con tus credenciales
configurar_whatsapp_real(
    api_url="https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID",
    api_token="YOUR_ACCESS_TOKEN"
)
```

### Variables de Entorno

Crea un archivo `.env` para configuraciones sensibles:

```env
FLASK_SECRET_KEY=tu_clave_secreta_muy_segura
WHATSAPP_API_URL=https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN=tu_token_de_acceso
```

## Datos de Ejemplo

El sistema incluye datos de ejemplo:

- **5 zonas**: Centro, Norte, Sur, Este, Oeste
- **15 clientes**: Distribuidos por las diferentes zonas
- **5 plantillas**: Mensajes típicos para tienda de recambios

## Personalización

### Agregar Nuevas Variables a las Plantillas

1. Modifica la función de personalización en `app.py`:
```python
mensaje_personalizado = plantilla.contenido.format(
    nombre_cliente=cliente.nombre,
    zona=zona.nombre,
    nueva_variable=valor_nuevo  # Agregar aquí
)
```

2. Actualiza las plantillas en la base de datos con la nueva variable.

### Modificar el Diseño

Los templates usan Bootstrap 5 y son completamente personalizables. Modifica los archivos en la carpeta `templates/`.

## Solución de Problemas

### Error de Base de Datos
```bash
# Eliminar base de datos y recrear
rm recambios.db
python crear_datos.py
```

### Puerto en Uso
```bash
# Cambiar puerto en app.py
app.run(debug=True, port=5001)
```

### Dependencias
```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## Soporte

Para soporte técnico o consultas, contacta con el desarrollador.

