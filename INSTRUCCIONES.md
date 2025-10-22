# Instrucciones de Instalación y Uso

## Requisitos Previos

1. **Instalar Python 3.8 o superior**
   - Descargar desde: https://www.python.org/downloads/
   - Durante la instalación, marcar "Add Python to PATH"

2. **Verificar instalación**
   ```bash
   python --version
   ```

## Instalación del Sistema

1. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

2. **Crear base de datos y datos de ejemplo**
   ```bash
   python crear_datos.py
   ```

3. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

4. **Abrir en el navegador**
   ```
   http://localhost:5000
   ```

## Datos Creados

El sistema ahora incluye:

### 8 Zonas:
- **Centro**: Zona centro de la ciudad, talleres principales y comerciales
- **Norte**: Zona norte, talleres industriales y de vehículos pesados  
- **Sur**: Zona sur, talleres de barrio y familiares
- **Este**: Zona este, talleres especializados y de alta gama
- **Oeste**: Zona oeste, talleres de vehículos comerciales
- **Polígono Industrial**: Polígono industrial, talleres de maquinaria pesada
- **Zona Residencial**: Zona residencial, talleres de vehículos particulares
- **Carretera Nacional**: Carretera nacional, talleres de carretera y emergencias

### 100 Clientes distribuidos por zonas:
- **Centro**: 12 clientes (Madrid)
- **Norte**: 13 clientes (Alcobendas, San Sebastián de los Reyes)
- **Sur**: 12 clientes (Getafe, Leganés)
- **Este**: 13 clientes (Alcalá de Henares, Torrejón de Ardoz)
- **Oeste**: 12 clientes (Móstoles, Alcorcón)
- **Polígono Industrial**: 12 clientes (Fuenlabrada, Parla)
- **Zona Residencial**: 13 clientes (Las Rozas, Majadahonda)
- **Carretera Nacional**: 13 clientes (Colmenar Viejo, Tres Cantos)

### Campos de cada cliente:
- **Nombre**: Nombre del taller/cliente
- **Teléfono**: Número para WhatsApp (formato español)
- **Email**: Dirección de correo electrónico
- **Dirección**: Dirección física del taller
- **Población**: Ciudad donde está ubicado
- **Zona**: Zona de reparto asignada
- **Estado**: Activo/Inactivo

## Funcionalidades del Sistema

1. **Gestión de Clientes**: Ver y filtrar clientes por zona
2. **Plantillas de Mensajes**: Mensajes predefinidos con variables
3. **Envío Masivo**: Enviar WhatsApp a todos los clientes de una zona
4. **Historial**: Registro completo de todos los envíos
5. **Interfaz Web**: Diseño responsive y moderno

## Personalización

- Los mensajes pueden incluir variables: `{nombre_cliente}`, `{zona}`
- El sistema simula el envío de WhatsApp (90% éxito, 10% error)
- Para producción, configurar la API real de WhatsApp Business

## Solución de Problemas

Si tienes problemas:

1. **Error de base de datos**: Eliminar `recambios.db` y ejecutar `python crear_datos.py` de nuevo
2. **Puerto ocupado**: Cambiar puerto en `app.py` línea final
3. **Dependencias**: Ejecutar `pip install --upgrade -r requirements.txt`

