# 📱 Migración de Número en Twilio

## ¿Puedo empezar con mi número personal y luego cambiar al de la empresa?

**¡Sí!** Puedes empezar con tu número personal para pruebas y luego cambiar al número de la empresa sin problemas.

## Proceso Recomendado

### Fase 1: Pruebas Iniciales (Número Personal)

1. **Configura el Sandbox de Twilio**:
   - Ve a: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
   - Únete al Sandbox enviando el código a tu número personal
   - El número del Sandbox será algo como: `whatsapp:+14155238886`

2. **Configura las variables de entorno**:
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Número del Sandbox
   ```

3. **Verifica tu número personal**:
   - En el Sandbox, verifica tu número personal de WhatsApp
   - Así podrás enviar y recibir mensajes de prueba

4. **Prueba la aplicación**:
   - Envía mensajes de prueba a tu número personal
   - Verifica que los webhooks funcionen correctamente
   - Prueba todas las funcionalidades

### Fase 2: Migración al Número de la Empresa

1. **Solicita el número de WhatsApp Business**:
   - Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
   - Solicita un número de WhatsApp Business para tu empresa
   - Espera la aprobación (puede tardar varios días)

2. **Una vez aprobado, actualiza la configuración**:

   **Opción A: Variables de Entorno (Recomendado)**
   ```bash
   TWILIO_WHATSAPP_NUMBER=whatsapp:+34625433667  # Número de la empresa
   ```
   Reinicia la aplicación.

   **Opción B: Desde la Aplicación**
   - Ve a `/configuracion/twilio`
   - Actualiza el campo "Número de WhatsApp" con el nuevo número
   - Guarda la configuración

3. **Actualiza el Webhook en Twilio**:
   - Ve a la configuración del nuevo número en Twilio
   - Configura el webhook: `https://tu-dominio.com/webhook/whatsapp`
   - Guarda los cambios

4. **Prueba con el nuevo número**:
   - Envía un mensaje de prueba
   - Verifica que todo funcione correctamente

## Ventajas de este Enfoque

✅ **Puedes empezar inmediatamente** sin esperar la aprobación del número de empresa  
✅ **Pruebas completas** antes de usar el número de producción  
✅ **Migración sencilla** - solo cambias una variable  
✅ **Sin cambios de código** - la aplicación funciona igual con ambos números  
✅ **Sin pérdida de datos** - todas las conversaciones y mensajes se mantienen  

## Consideraciones

⚠️ **Números de prueba (Sandbox)**:
- Solo puedes enviar a números verificados en el Sandbox
- Limitado a pruebas y desarrollo

✅ **Números de producción**:
- Puedes enviar a cualquier número de WhatsApp
- Sin limitaciones
- Listo para uso real con clientes

## ¿Qué pasa con los mensajes y conversaciones existentes?

- ✅ **Se mantienen**: Todas las conversaciones y mensajes guardados en la base de datos
- ✅ **Siguen funcionando**: Puedes ver el historial completo
- ✅ **Nuevos mensajes**: Se enviarán desde el nuevo número automáticamente

## Resumen

1. **Empieza con Sandbox** → Configura con número de prueba
2. **Prueba todo** → Verifica que funciona correctamente
3. **Solicita número empresa** → Mientras pruebas, solicita el número de producción
4. **Migra cuando esté listo** → Solo cambia `TWILIO_WHATSAPP_NUMBER`
5. **¡Listo!** → Tu aplicación funciona con el número de la empresa

**No hay problema en empezar con tu número personal y luego cambiar al de la empresa. Es la forma recomendada de hacerlo.**

