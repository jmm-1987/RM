# 🚀 Configuración de Green-API para Recambios RM

## 📋 Información de tu Instancia

Basándome en la imagen que proporcionaste, aquí están los datos de tu instancia de Green-API:

- **ID de Instancia**: `7107349111`
- **URL de la API**: `https://7107.api.green-api.com`
- **Número de Teléfono**: `34625433667`
- **Estado**: `Authorized` ✅

## ⚙️ Pasos para Configurar

### 1. Obtener tu Token de Autenticación

1. Ve a tu panel de Green-API: https://console.green-api.com
2. Selecciona tu instancia `7107349111`
3. En la sección de configuración, busca `apiTokenInstance`
4. Haz clic en el icono del ojo 👁️ para mostrar el token
5. Copia el token completo

### 2. Configurar el Sistema

**Opción A: Configuración Automática**
1. Abre el archivo `green_api_config.py`
2. Reemplaza `TU_TOKEN_AQUI` con tu token real
3. Ejecuta: `python configurar_green_api_auto.py`

**Opción B: Configuración Manual**
1. Ve al panel admin: http://localhost:5000
2. Haz clic en "Configuración" en el menú
3. Haz clic en "Configurar Green-API"
4. Introduce:
   - **URL**: `https://7107.api.green-api.com`
   - **Token**: Tu token de autenticación
5. Haz clic en "Guardar Configuración"

### 3. Probar la Configuración

1. En la página de configuración, haz clic en "Enviar Prueba"
2. Introduce un número de teléfono de prueba
3. Haz clic en "Enviar Prueba"
4. Verifica que recibas el mensaje en WhatsApp

## 🔧 Funcionalidades Disponibles

Una vez configurado, podrás:

- ✅ **Envío masivo** de WhatsApp a clientes por zona
- ✅ **Mensajes personalizados** con plantillas
- ✅ **Solo a clientes marcados** para incluir en comunicados
- ✅ **Historial completo** de mensajes enviados
- ✅ **Gestión de ofertas** con web pública
- ✅ **Estado en tiempo real** de la conexión

## 📱 Formato de Números de Teléfono

El sistema acepta números en estos formatos:
- `612345678` (se convierte automáticamente a `34612345678`)
- `34612345678` (formato internacional completo)
- `+34612345678` (con prefijo +)

## 🚨 Solución de Problemas

### Error: "Instancia no autorizada"
- Verifica que tu instancia esté en estado "Authorized" en Green-API
- Asegúrate de que WhatsApp esté conectado en tu instancia

### Error: "Token inválido"
- Verifica que hayas copiado el token completo
- Asegúrate de que no haya espacios extra

### Error: "Número no válido"
- Verifica el formato del número de teléfono
- Asegúrate de que el número tenga WhatsApp activo

## 📊 Monitoreo

El sistema incluye:
- **Logs detallados** de cada envío
- **Estado de conexión** en tiempo real
- **Estadísticas** de mensajes enviados
- **Historial completo** de actividad

## 🔒 Seguridad

- Los tokens se almacenan de forma segura
- Los números de teléfono se formatean automáticamente
- Se incluye validación de datos antes del envío
- Logs de auditoría para seguimiento

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs del sistema
2. Verifica la configuración en Green-API
3. Prueba con un número de teléfono conocido
4. Contacta al soporte técnico si es necesario

---

**¡Tu sistema está listo para enviar WhatsApp masivos!** 🎉

