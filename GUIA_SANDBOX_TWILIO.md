# 🚀 Guía Paso a Paso: Configurar Sandbox de Twilio

## 📋 ¿Qué es el Sandbox?

El Sandbox de Twilio es un entorno de pruebas gratuito que te permite:
- ✅ Empezar a usar WhatsApp inmediatamente (sin aprobación)
- ✅ Probar todas las funcionalidades
- ✅ Enviar mensajes a números verificados
- ⚠️ Limitación: Solo puedes enviar a números que verifiques en el Sandbox

## 🎯 Paso 1: Acceder al Sandbox

1. **Abre tu navegador** y ve a:
   ```
   https://console.twilio.com/us1/develop/sms/whatsapp/learn
   ```

2. **Inicia sesión** en tu cuenta de Twilio (o créala si no tienes)

3. **Busca la sección "Sandbox"** o "Try it out"

## 📱 Paso 2: Unirte al Sandbox

1. **En la página del Sandbox**, verás algo como:
   ```
   Join the Sandbox
   Send "join [código]" to +1 415 523 8886
   ```

2. **Abre WhatsApp** en tu teléfono

3. **Envía un mensaje** al número que te indique Twilio (normalmente `+1 415 523 8886`)
   - El mensaje debe ser: `join [código]` (reemplaza `[código]` con el código que te muestra Twilio)
   - Ejemplo: Si el código es `abc-123`, envía: `join abc-123`

4. **Espera la confirmación** de Twilio en WhatsApp (te dirá que te has unido al Sandbox)

## ✅ Paso 3: Verificar tu Número Personal

Para poder enviarte mensajes de prueba:

1. **En el panel de Twilio**, en la sección del Sandbox
2. **Busca "Add number"** o "Verify number"
3. **Ingresa tu número personal**: `+34619639616`
4. **Twilio te enviará un código** por WhatsApp
5. **Ingresa el código** en el panel de Twilio
6. **Tu número quedará verificado** ✅

## ⚙️ Paso 4: Configurar el Número en tu Aplicación

Ahora necesitas cambiar el número "From" en tu aplicación al número del Sandbox.

### Opción A: Desde Render (Recomendado)

1. **Ve a tu servicio en Render**: https://dashboard.render.com
2. **Selecciona tu servicio** (rm-p1r1 o similar)
3. **Ve a "Environment"** en el menú lateral
4. **Busca la variable** `TWILIO_WHATSAPP_NUMBER`
5. **Cambia el valor** a:
   ```
   whatsapp:+14155238886
   ```
6. **Guarda los cambios**
7. **Render reiniciará automáticamente** tu aplicación

### Opción B: Desde la Aplicación Web

1. **Ve a tu aplicación**: `https://rm-p1r1.onrender.com`
2. **Inicia sesión**
3. **Ve a**: `/configuracion/twilio`
4. **En el campo "WhatsApp Number"**, ingresa:
   ```
   whatsapp:+14155238886
   ```
5. **Haz clic en "Guardar"** o "Configurar Twilio"

## 🧪 Paso 5: Probar que Funciona

1. **Ve a la sección de WhatsApp** en tu aplicación: `/whatsapp`
2. **Inicia una nueva conversación** o abre una existente
3. **Envía un mensaje de prueba** a tu número personal (`+34619639616`)
4. **Deberías recibir el mensaje** en tu WhatsApp ✅

## 📋 Verificación Final

### ✅ Checklist

- [ ] Te has unido al Sandbox de Twilio
- [ ] Has verificado tu número personal en el Sandbox
- [ ] Has cambiado `TWILIO_WHATSAPP_NUMBER` a `whatsapp:+14155238886`
- [ ] Has reiniciado la aplicación (si usaste Render, se reinicia automáticamente)
- [ ] Has enviado un mensaje de prueba
- [ ] Has recibido el mensaje en tu WhatsApp

### 🔍 Verificar en los Logs

Después de enviar un mensaje, revisa los logs de Render. Deberías ver:

```
📤 Intentando enviar mensaje:
   From (remitente): whatsapp:+14155238886
   To (destino): whatsapp:+34619639616
✓ Mensaje enviado exitosamente a 34619639616. SID: SM...
```

**NO deberías ver:**
```
✗ Error enviando a ...: Error Twilio 63007
```

## ⚠️ Limitaciones del Sandbox

1. **Solo números verificados**: Solo puedes enviar a números que hayas verificado en el Sandbox
2. **Número del Sandbox**: Siempre usarás `whatsapp:+14155238886` como remitente
3. **Para producción**: Necesitarás aprobar tu número real (ver `REQUISITOS_APROBACION_TWILIO.md`)

## 🔄 Agregar Más Números al Sandbox

Para enviar mensajes a otros números:

1. **En el panel de Twilio**, ve a la sección del Sandbox
2. **Haz clic en "Add number"** o "Verify number"
3. **Ingresa el número** que quieres verificar (formato: +34612345678)
4. **Twilio enviará un código** por WhatsApp a ese número
5. **La persona debe enviar el código** de vuelta a Twilio
6. **El número quedará verificado** y podrás enviarle mensajes

## 🆘 Solución de Problemas

### Problema: "No puedo unirme al Sandbox"

**Solución:**
- Asegúrate de enviar el mensaje exacto que te indica Twilio
- Verifica que estés enviando al número correcto
- Espera unos segundos y vuelve a intentar

### Problema: "Sigo recibiendo error 63007"

**Solución:**
1. Verifica que hayas cambiado `TWILIO_WHATSAPP_NUMBER` a `whatsapp:+14155238886`
2. Verifica que la aplicación se haya reiniciado
3. Revisa los logs para ver qué número está usando como "From"
4. Ve a `/diagnostico-twilio` en tu aplicación para verificar la configuración

### Problema: "No puedo verificar mi número"

**Solución:**
- Asegúrate de que el número esté en formato internacional: `+34619639616`
- Verifica que puedas recibir mensajes de WhatsApp
- Intenta de nuevo después de unos minutos

### Problema: "No recibo mensajes"

**Solución:**
1. Verifica que tu número esté verificado en el Sandbox
2. Verifica que el webhook esté configurado (ver `CONFIGURAR_WEBHOOK_TWILIO.md`)
3. Revisa los logs para ver si hay errores

## 📞 Siguiente Paso: Migrar a Producción

Una vez que todo funcione con el Sandbox, puedes:

1. **Solicitar aprobación** de tu número real (`+34619639616`)
2. **Ver**: `REQUISITOS_APROBACION_TWILIO.md` para los pasos
3. **Cuando esté aprobado**, solo cambia `TWILIO_WHATSAPP_NUMBER` de vuelta a `whatsapp:+34619639616`

## ✅ Resumen Rápido

1. Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
2. Únete al Sandbox enviando el código por WhatsApp
3. Verifica tu número personal en el Sandbox
4. Cambia `TWILIO_WHATSAPP_NUMBER` a `whatsapp:+14155238886`
5. Prueba enviando un mensaje
6. ¡Listo! 🎉

