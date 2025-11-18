# 🔧 Desactivar Green-API y Configurar Twilio

## ⚠️ Problema Actual

Tu aplicación está recibiendo webhooks de **Green-API**, pero el código ahora solo acepta mensajes de **Twilio**. Por eso los mensajes no aparecen en las conversaciones.

## ✅ Solución: Desactivar Green-API y Configurar Twilio

### Paso 1: Desactivar Webhook de Green-API

Tienes dos opciones:

#### Opción A: Desde el Panel de Green-API (Recomendado)

1. Ve a tu panel de Green-API: https://console.green-api.com
2. Accede a la configuración de tu instancia
3. Ve a **"Webhooks"** o **"Configuración"**
4. **Desactiva** o **elimina** el webhook que apunta a:
   ```
   https://rm-p1r1.onrender.com/webhook/whatsapp
   ```
5. Guarda los cambios

#### Opción B: Usando la API de Green-API

Si tienes acceso a la API, puedes desactivar el webhook ejecutando:

```python
import requests

GREEN_API_URL = 'https://7107.api.green-api.com'
GREEN_API_TOKEN = 'TU_TOKEN_AQUI'
GREEN_API_INSTANCE_ID = 'TU_INSTANCE_ID'

# Desactivar webhook
url = f'{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/setSettings/{GREEN_API_TOKEN}'
data = {
    'webhookUrl': '',  # URL vacía desactiva el webhook
    'incomingWebhook': 'no',
    'incomingMessageWebhook': 'no'
}
response = requests.post(url, json=data)
print(response.json())
```

### Paso 2: Verificar que Green-API está Desactivado

Después de desactivar, verifica que ya no lleguen webhooks:

1. Revisa los logs de tu aplicación
2. No deberías ver más mensajes con `User-Agent: "GREEN-API"`
3. No deberías ver más errores 400 en `/webhook/whatsapp`

### Paso 3: Configurar Twilio

Ahora necesitas configurar Twilio para que envíe webhooks a tu aplicación:

#### 3.1. Configurar Webhook en Twilio Console

1. Ve a: https://console.twilio.com
2. Navega a **Messaging** → **Try it out** → **Send a WhatsApp message**
3. O ve directamente a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
4. En la sección **"Webhook Configuration"** o **"When a message comes in"**:
   - Ingresa la URL: `https://rm-p1r1.onrender.com/webhook/whatsapp`
   - Método: `POST`
   - Guarda los cambios

#### 3.2. Configurar desde el Código (Opcional)

Si prefieres configurarlo programáticamente, puedes usar la API de Twilio:

```python
from twilio.rest import Client

account_sid = 'TU_ACCOUNT_SID'
auth_token = 'TU_AUTH_TOKEN'
whatsapp_number = 'whatsapp:+34612345678'  # Tu número de Twilio

client = Client(account_sid, auth_token)

# Configurar webhook para el número de WhatsApp
# Nota: Esto puede requerir permisos especiales en Twilio
```

#### 3.3. Verificar Variables de Entorno

Asegúrate de tener configuradas estas variables de entorno:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_WHATSAPP_NUMBER=whatsapp:+34612345678
```

### Paso 4: Probar la Configuración

1. **Envía un mensaje de prueba** desde WhatsApp a tu número de Twilio
2. **Revisa los logs** de tu aplicación:
   - Deberías ver: `🔍 Webhook Twilio recibido - keys: ['From', 'To', 'Body', ...]`
   - NO deberías ver: `⚠️ Webhook Green-API rechazado`
3. **Verifica en la aplicación**:
   - Ve a `/whatsapp` en tu aplicación
   - El mensaje debería aparecer en las conversaciones

## 🔍 Verificación

### Logs Correctos (Twilio)
```
🔍 Webhook Twilio recibido - keys: ['From', 'To', 'Body', 'MessageSid', ...]
✅ Mensaje recibido de 34612345678: Hola...
```

### Logs Incorrectos (Green-API aún activo)
```
⚠️ Webhook Green-API rechazado - keys: ['typeWebhook', 'instanceData', ...]
⚠️ Este webhook solo acepta mensajes de Twilio. Por favor, desactiva el webhook de Green-API.
```

## 📝 Notas Importantes

1. **Transición**: Durante la transición, es normal ver algunos webhooks de Green-API siendo rechazados. Una vez desactivado, dejarán de llegar.

2. **Sandbox vs Producción**: 
   - Si estás usando el **Sandbox de Twilio**, el webhook se configura automáticamente
   - Si estás usando un **número de producción**, necesitas configurarlo manualmente

3. **Mensajes Perdidos**: Los mensajes que llegaron mientras Green-API estaba activo pero Twilio no, no se procesaron. Una vez configurado Twilio correctamente, los nuevos mensajes se procesarán normalmente.

## 🆘 Si Sigues Teniendo Problemas

1. **Verifica que Twilio esté configurado**:
   - Ve a `/configuracion/twilio` en tu aplicación
   - Verifica que las credenciales sean correctas

2. **Revisa los logs**:
   - Busca errores relacionados con Twilio
   - Verifica que los webhooks de Twilio lleguen correctamente

3. **Prueba el webhook manualmente**:
   - Puedes usar herramientas como Postman o curl para enviar un webhook de prueba de Twilio

## ✅ Checklist Final

- [ ] Webhook de Green-API desactivado
- [ ] Webhook de Twilio configurado en el panel de Twilio
- [ ] Variables de entorno de Twilio configuradas
- [ ] Mensaje de prueba enviado desde WhatsApp
- [ ] Mensaje aparece en la aplicación en `/whatsapp`
- [ ] Logs muestran `🔍 Webhook Twilio recibido` (no `⚠️ Webhook Green-API rechazado`)

