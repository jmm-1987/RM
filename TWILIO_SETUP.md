# 🚀 Configuración de Twilio para Recambios RM

## 📋 Variables de Entorno Necesarias

Para configurar Twilio en tu aplicación, necesitas las siguientes variables de entorno:

### Variables Requeridas:

1. **`TWILIO_ACCOUNT_SID`**
   - Descripción: Account SID de tu cuenta de Twilio
   - Dónde encontrarlo: Panel de Twilio → Dashboard → Account SID
   - Ejemplo: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

2. **`TWILIO_AUTH_TOKEN`**
   - Descripción: Auth Token de tu cuenta de Twilio
   - Dónde encontrarlo: Panel de Twilio → Dashboard → Auth Token (haz clic en el ojo para mostrarlo)
   - Ejemplo: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

3. **`TWILIO_WHATSAPP_NUMBER`**
   - Descripción: Número de WhatsApp Business de Twilio (formato: whatsapp:+34612345678)
   - Dónde encontrarlo: Panel de Twilio → Messaging → Try it out → Send a WhatsApp message
   - Formato: Debe empezar con `whatsapp:` seguido del número con código de país
   - Ejemplo: `whatsapp:+34612345678` (número de prueba) o `whatsapp:+34625433667` (número real)

## ⚙️ Pasos para Configurar

### 1. Obtener Credenciales de Twilio

1. Accede a tu cuenta de Twilio: https://console.twilio.com
2. En el Dashboard, encontrarás:
   - **Account SID**: Visible en la parte superior
   - **Auth Token**: Haz clic en el icono del ojo 👁️ para mostrarlo

### 2. Configurar Número de WhatsApp

#### Opción A: Empezar con Número de Prueba (Sandbox) - RECOMENDADO PARA EMPEZAR
1. Ve a: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Sigue las instrucciones para unirte al Sandbox
3. El número de prueba será algo como: `whatsapp:+14155238886`
4. **Ventajas**: Gratis, no requiere aprobación, puedes empezar inmediatamente
5. **Limitaciones**: Solo puedes enviar a números que hayas verificado en el Sandbox (envías un código a tu número personal)
6. **Ideal para**: Pruebas iniciales y desarrollo

#### Opción B: Usar tu Número Personal (Sandbox)
1. Puedes usar tu número personal de WhatsApp para pruebas
2. Únete al Sandbox y verifica tu número personal
3. Configura `TWILIO_WHATSAPP_NUMBER` con el número del Sandbox (ej: `whatsapp:+14155238886`)
4. Puedes enviar mensajes a tu número personal verificado
5. **Luego puedes cambiar** al número de la empresa cuando esté listo

#### Opción C: Número de Producción (Empresa)
1. Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
2. Solicita un número de WhatsApp Business para tu empresa
3. Una vez aprobado (puede tardar varios días), el número aparecerá en tu panel
4. **Ventajas**: Puedes enviar a cualquier número de WhatsApp, sin limitaciones
5. **Requisitos**: Aprobación de Twilio, número de empresa verificado
6. **Ideal para**: Producción y uso real con clientes

### 3. Configurar Variables de Entorno

#### En Desarrollo Local:
Crea un archivo `.env` en la raíz del proyecto o añade las variables a `config.py`:

```python
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+34612345678'  # Número de prueba o producción
```

#### En Producción (Render):
1. Ve a tu proyecto en Render
2. Settings → Environment Variables
3. Añade las tres variables:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_NUMBER`

### 4. Configurar Webhook en Twilio

1. Ve a: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. En "A MESSAGE COMES IN", configura la URL:
   ```
   https://tu-dominio.onrender.com/webhook/whatsapp
   ```
   O para desarrollo local con ngrok:
   ```
   https://tu-id.ngrok.io/webhook/whatsapp
   ```
3. Guarda la configuración

### 5. Verificar Configuración

1. Inicia la aplicación
2. Ve a: `/configuracion` en tu aplicación
3. Haz clic en "Configurar Twilio"
4. Introduce tus credenciales
5. Haz clic en "Enviar Prueba" para verificar que funciona

## 🔧 Funcionalidades Disponibles

Una vez configurado, podrás:

- ✅ **Envío masivo** de WhatsApp a clientes por zona
- ✅ **Mensajes personalizados** con plantillas
- ✅ **Solo a clientes marcados** para incluir en comunicados
- ✅ **Historial completo** de mensajes enviados
- ✅ **Gestión de ofertas** con web pública
- ✅ **Estado en tiempo real** de la conexión
- ✅ **Recepción de mensajes** vía webhook
- ✅ **Conversaciones avanzadas** con historial completo

## 📱 Formato de Números de Teléfono

El sistema acepta números en estos formatos:
- `612345678` (se convierte automáticamente a `34612345678`)
- `34612345678` (formato completo con código de país)
- `+34612345678` (con prefijo +)

**Importante**: Twilio requiere el formato `whatsapp:+34612345678` para enviar mensajes.

## ⚠️ Notas Importantes

1. **Número de Prueba (Sandbox)**: 
   - Solo puedes enviar mensajes a números verificados en el Sandbox
   - Para recibir mensajes, el remitente debe enviar un código al número de Twilio
   - **Puedes empezar con tu número personal** y luego cambiar al de la empresa
   - Para cambiar de número, solo actualiza la variable `TWILIO_WHATSAPP_NUMBER` en la configuración

2. **Número de Producción (Empresa)**:
   - Requiere aprobación de Twilio
   - Puede tardar varios días en ser aprobado
   - Permite enviar a cualquier número de WhatsApp
   - **Puedes migrar desde el Sandbox** sin problemas, solo cambia el número en la configuración

3. **Migración de Número**:
   - Puedes empezar con el Sandbox usando tu número personal para pruebas
   - Cuando tengas el número de la empresa aprobado, simplemente:
     1. Actualiza `TWILIO_WHATSAPP_NUMBER` en las variables de entorno
     2. O cambia el número desde `/configuracion/twilio` en la aplicación
     3. No necesitas cambiar código, solo la configuración

3. **Webhook**:
   - Debe ser una URL HTTPS pública
   - Para desarrollo local, usa ngrok o similar
   - Twilio valida la URL antes de activarla

4. **Costos**:
   - Revisa los precios en: https://www.twilio.com/whatsapp/pricing
   - Los números de prueba tienen limitaciones

## 🆘 Solución de Problemas

### Error: "Twilio no está configurado"
- Verifica que las tres variables de entorno estén configuradas
- Revisa que no haya espacios en blanco en los valores

### Error: "Invalid phone number"
- Asegúrate de que el número esté en formato `whatsapp:+34612345678`
- Verifica que el código de país sea correcto (34 para España)

### No se reciben mensajes
- Verifica que el webhook esté configurado correctamente en Twilio
- Asegúrate de que la URL sea HTTPS y sea accesible públicamente
- Revisa los logs de la aplicación para ver si llegan los webhooks

### Error al enviar mensajes
- Verifica que el número de destino esté en el formato correcto
- Para números de prueba, asegúrate de que estén verificados en el Sandbox
- Revisa el saldo de tu cuenta de Twilio

