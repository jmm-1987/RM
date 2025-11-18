# 📱 Configurar Webhook de Twilio para Recibir Mensajes

## ❌ Problema

No puedes recibir mensajes de WhatsApp en tu aplicación. Los mensajes que te envían no aparecen.

## 🔍 Causa

Twilio necesita saber **dónde enviar los mensajes entrantes**. Esto se configura mediante un **webhook** (URL que Twilio llama cuando llega un mensaje).

## ✅ Solución: Configurar el Webhook en Twilio

### Paso 1: Obtener la URL de tu Webhook

Tu aplicación tiene un endpoint para recibir mensajes:
```
https://rm-p1r1.onrender.com/webhook/whatsapp
```

**⚠️ Importante:** Esta URL debe ser:
- ✅ Pública (accesible desde internet)
- ✅ HTTPS (no HTTP)
- ✅ Accesible 24/7 (tu aplicación debe estar corriendo)

### Paso 2: Configurar el Webhook en Twilio Console

#### Opción A: Si Usas Sandbox

1. Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
2. En la sección **"Sandbox Configuration"** o **"Webhook Configuration"**
3. Busca el campo **"When a message comes in"** o **"Webhook URL"**
4. Ingresa tu URL:
   ```
   https://rm-p1r1.onrender.com/webhook/whatsapp
   ```
5. Método: `POST`
6. Guarda los cambios

#### Opción B: Si Usas Número de Producción

1. Ve a: https://console.twilio.com
2. Navega a **Messaging** → **Settings** → **WhatsApp Sandbox** (si usas Sandbox)
   O **Messaging** → **Try it out** → **Send a WhatsApp message** (si usas producción)
3. Busca la sección **"Webhook Configuration"** o **"When a message comes in"**
4. Ingresa tu URL:
   ```
   https://rm-p1r1.onrender.com/webhook/whatsapp
   ```
5. Método: `POST`
6. Guarda los cambios

#### Opción C: Configurar por Número (Producción)

Si tienes un número de WhatsApp Business aprobado:

1. Ve a: https://console.twilio.com
2. Navega a **Phone Numbers** → **Manage** → **Active numbers**
3. Haz clic en tu número de WhatsApp
4. En la sección **"Messaging"** o **"WhatsApp"**
5. Busca **"A message comes in"** o **"Webhook URL"**
6. Ingresa:
   ```
   https://rm-p1r1.onrender.com/webhook/whatsapp
   ```
7. Método: `POST`
8. Guarda los cambios

### Paso 3: Verificar que el Webhook Funciona

1. **Envía un mensaje de prueba** desde WhatsApp a tu número de Twilio
2. **Revisa los logs** de tu aplicación en Render
3. Deberías ver:
   ```
   🔍 Webhook Twilio recibido - keys: ['From', 'To', 'Body', 'MessageSid', ...]
   ✅ Mensaje recibido de 34612345678: Tu mensaje aquí...
   ```

### Paso 4: Verificar en la Aplicación

1. Ve a `/whatsapp` en tu aplicación
2. El mensaje debería aparecer en las conversaciones
3. Si no aparece, revisa los logs para ver si hay errores

## 🔧 Configuración Avanzada

### Formato de Respuesta del Webhook

Tu aplicación responde con TwiML (formato XML que Twilio espera):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

Esto le dice a Twilio que el mensaje fue recibido correctamente.

### Verificar que el Webhook Está Activo

1. Ve a tu panel de Twilio
2. Revisa la configuración del webhook
3. Deberías ver tu URL configurada
4. Twilio puede mostrar el último intento de llamada al webhook

## ⚠️ Problemas Comunes

### Problema: "No recibo mensajes"

**Soluciones:**
1. ✅ Verifica que el webhook esté configurado en Twilio
2. ✅ Verifica que la URL sea correcta: `https://rm-p1r1.onrender.com/webhook/whatsapp`
3. ✅ Verifica que tu aplicación esté corriendo (no en sleep)
4. ✅ Verifica que la URL sea HTTPS (no HTTP)
5. ✅ Revisa los logs de Render para ver si llegan las peticiones

### Problema: "El webhook devuelve error 400"

**Causa:** El webhook está recibiendo datos en formato incorrecto o de Green-API.

**Solución:** 
- El código ahora rechaza explícitamente webhooks de Green-API
- Solo acepta webhooks de Twilio
- Si ves `⚠️ Webhook Green-API rechazado`, desactiva el webhook de Green-API

### Problema: "Los mensajes no aparecen en la aplicación"

**Soluciones:**
1. ✅ Verifica que el mensaje llegue al webhook (revisa logs)
2. ✅ Verifica que no haya errores en el procesamiento del mensaje
3. ✅ Verifica que la base de datos esté funcionando
4. ✅ Revisa los logs para ver si hay errores al guardar el mensaje

### Problema: "Twilio no puede alcanzar mi webhook"

**Causas posibles:**
- La aplicación está en sleep (Render free tier)
- La URL no es pública
- Hay un firewall bloqueando las peticiones

**Soluciones:**
1. ✅ Asegúrate de que la aplicación esté corriendo
2. ✅ Verifica que la URL sea accesible desde internet
3. ✅ Prueba la URL manualmente: `curl https://rm-p1r1.onrender.com/webhook/whatsapp`

## 📋 Checklist de Configuración

- [ ] Webhook configurado en Twilio Console
- [ ] URL del webhook: `https://rm-p1r1.onrender.com/webhook/whatsapp`
- [ ] Método: `POST`
- [ ] Aplicación corriendo (no en sleep)
- [ ] URL es HTTPS (no HTTP)
- [ ] Mensaje de prueba enviado desde WhatsApp
- [ ] Logs muestran `🔍 Webhook Twilio recibido`
- [ ] Mensaje aparece en `/whatsapp` de la aplicación

## 🧪 Probar el Webhook Manualmente

Puedes probar si el webhook funciona enviando una petición de prueba:

```bash
curl -X POST https://rm-p1r1.onrender.com/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+34612345678&To=whatsapp:+34619639616&Body=Test&MessageSid=SM123456789"
```

Si funciona, deberías ver en los logs:
```
🔍 Webhook Twilio recibido - keys: ['From', 'To', 'Body', 'MessageSid']
```

## 📞 Soporte

Si después de seguir estos pasos sigues sin recibir mensajes:

1. **Revisa los logs de Render** para ver si llegan peticiones al webhook
2. **Revisa el panel de Twilio** para ver el estado del webhook
3. **Verifica que tu número de Twilio esté activo** y configurado correctamente
4. **Prueba enviando un mensaje desde WhatsApp** y revisa los logs inmediatamente

## 🔄 Actualizar el Webhook

Si cambias la URL de tu aplicación o el endpoint:

1. Ve al panel de Twilio
2. Actualiza la URL del webhook
3. Guarda los cambios
4. Prueba enviando un mensaje de prueba

