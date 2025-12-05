# 🔄 Guía: Reactivar Número de WhatsApp en Twilio

## 📋 Pasos para Reactivar tu Número

### Paso 1: Acceder a la Consola de Twilio

1. **Inicia sesión** en tu cuenta de Twilio:
   ```
   https://console.twilio.com
   ```

2. **Verifica tu cuenta** está activa y tiene saldo suficiente

### Paso 2: Verificar el Estado del Número

1. **Navega a Phone Numbers**:
   - En el menú lateral, ve a **Phone Numbers** → **Manage** → **Active numbers**
   - O directamente: https://console.twilio.com/us1/develop/phone-numbers/manage/active

2. **Busca tu número de WhatsApp**:
   - Si aparece en la lista, verifica su estado
   - Si **NO aparece**, puede que haya sido liberado o nunca se haya configurado

### Paso 3: Reactivar el Número

#### Opción A: Si el número aparece pero está inactivo

1. **Haz clic en el número** para abrir su configuración
2. **Verifica las configuraciones**:
   - **Messaging**: Debe estar habilitado
   - **WhatsApp**: Debe estar configurado
   - **Webhook URL**: Debe apuntar a tu aplicación
     ```
     https://tu-dominio.onrender.com/webhook/whatsapp
     ```

3. **Guarda los cambios**

#### Opción B: Si el número NO aparece (fue liberado)

1. **Adquirir un nuevo número de WhatsApp Business**:
   - Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
   - Solicita un nuevo número de WhatsApp Business
   - Espera la aprobación (puede tardar varios días)

2. **O usar el Sandbox temporalmente**:
   - Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
   - Únete al Sandbox
   - El número será: `whatsapp:+14155238886`
   - Configura `TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886`

### Paso 4: Verificar Configuración de WhatsApp

1. **Ve a la configuración de WhatsApp**:
   ```
   https://console.twilio.com/us1/develop/sms/whatsapp/learn
   ```

2. **Verifica el estado**:
   - Si usas **Sandbox**: Verifica que estés unido y que tu número personal esté verificado
   - Si usas **Producción**: Verifica que tu número de empresa esté aprobado

3. **Configura el Webhook**:
   - En "A MESSAGE COMES IN", configura:
     ```
     https://tu-dominio.onrender.com/webhook/whatsapp
     ```
   - O para desarrollo local con ngrok:
     ```
     https://tu-id.ngrok.io/webhook/whatsapp
     ```

### Paso 5: Actualizar Variables de Entorno

Una vez que tengas el número activo:

1. **En Render** (si estás en producción):
   - Ve a tu servicio: https://dashboard.render.com
   - Settings → Environment
   - Actualiza `TWILIO_WHATSAPP_NUMBER` con el número correcto:
     ```
     TWILIO_WHATSAPP_NUMBER=whatsapp:+34612345678
     ```
   - **Reinicia el servicio**

2. **En desarrollo local**:
   - Actualiza `config.py` o `.env`:
     ```python
     TWILIO_WHATSAPP_NUMBER = 'whatsapp:+34612345678'
     ```
   - Reinicia la aplicación

### Paso 6: Verificar que Funciona

1. **Ve a tu aplicación**: `/configuracion`
2. **Haz clic en "Diagnóstico Twilio"**
3. **Verifica el estado**:
   - ✅ Debe mostrar "Conectado y funcionando"
   - ✅ El número debe aparecer correctamente configurado

4. **Prueba enviar un mensaje**:
   - Ve a `/configuracion`
   - Usa la función "Enviar mensaje de prueba"
   - Si funciona, el número está reactivado ✅

## ⚠️ Problemas Comunes

### Error: "Número no encontrado" o Error 63007

**Causa**: El número no está configurado en Twilio o el formato es incorrecto.

**Solución**:
1. Verifica el formato: debe ser `whatsapp:+34612345678`
2. Si usas Sandbox, debe ser `whatsapp:+14155238886`
3. Verifica en el panel de Twilio que el número exista

### Error: "Cuenta suspendida" o "Sin saldo"

**Causa**: Tu cuenta de Twilio no tiene saldo o está suspendida.

**Solución**:
1. Ve a: https://console.twilio.com/us1/account/billing
2. Verifica tu saldo
3. Añade crédito si es necesario
4. Contacta soporte si la cuenta está suspendida

### Error: "Número no aprobado para WhatsApp Business"

**Causa**: El número no ha sido aprobado para WhatsApp Business.

**Solución**:
1. Si es un número nuevo, espera la aprobación (3-7 días)
2. Usa el Sandbox mientras tanto
3. Verifica que cumplas los requisitos: https://console.twilio.com/us1/develop/sms/whatsapp/learn

## 📞 Contactar Soporte de Twilio

Si después de seguir estos pasos el número aún no funciona:

1. **Soporte de Twilio**: https://www.twilio.com/help/contact
2. **Documentación**: https://www.twilio.com/docs/whatsapp
3. **Estado del servicio**: https://status.twilio.com

## ✅ Checklist de Reactivación

- [ ] Cuenta de Twilio activa y con saldo
- [ ] Número visible en "Active Numbers" o Sandbox configurado
- [ ] Webhook configurado correctamente
- [ ] Variable `TWILIO_WHATSAPP_NUMBER` actualizada
- [ ] Servicio reiniciado (si aplica)
- [ ] Prueba de envío exitosa
- [ ] Diagnóstico muestra "Conectado"

## 🔗 Enlaces Útiles

- **Consola de Twilio**: https://console.twilio.com
- **WhatsApp Sandbox**: https://console.twilio.com/us1/develop/sms/whatsapp/learn
- **Phone Numbers**: https://console.twilio.com/us1/develop/phone-numbers/manage/active
- **Billing**: https://console.twilio.com/us1/account/billing
- **Soporte**: https://www.twilio.com/help/contact

