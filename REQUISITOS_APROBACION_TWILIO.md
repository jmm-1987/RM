# 📋 Requisitos para Aprobación de WhatsApp Business en Twilio

## ¿Qué necesita tu número de WhatsApp Business para ser aprobado por Twilio?

Twilio requiere varios documentos y verificaciones para aprobar un número de WhatsApp Business. Aquí está todo lo que necesitas:

## 📄 Requisitos Principales

### 1. **Número de Teléfono Válido** ✅
- ✅ **Debe incluir código de país y área** (ej: +34 625 433 667)
- ✅ **Debe ser propiedad de tu empresa** (no personal)
- ✅ **Debe poder recibir llamadas de voz o SMS** (para verificación)
- ✅ **No puede ser un código corto** (números especiales)
- ✅ **No puede haber sido usado previamente** con otra API de WhatsApp Business
- ✅ **Debe estar activo** y funcionando

### 2. **Nombre de Visualización (Display Name)** ✅
- ✅ **Debe estar relacionado con tu negocio** (ej: "Recambios RM")
- ✅ **No puede violar políticas** de WhatsApp Business
- ✅ **Debe ser apropiado** para uso comercial
- ✅ **No puede contener palabras prohibidas**

### 3. **Cuenta de Facebook Business Manager** ✅
- ✅ **Debe estar verificada** (proceso de verificación de Facebook)
- ✅ **Necesaria para gestionar** la cuenta de WhatsApp Business
- ✅ **Debe estar asociada** a tu empresa

### 4. **Cuenta de WhatsApp Business API (WABA)** ✅
- ✅ **Debes crear o tener** una cuenta de WhatsApp Business API
- ✅ **Asociar el número** a esta cuenta
- ✅ **Completar el perfil** de la cuenta

### 5. **Verificación del Número** ✅
- ✅ **Recibir código por llamada o SMS** durante el registro
- ✅ **El número debe poder recibir** llamadas/mensajes internacionales
- ✅ **Verificar el código** en el proceso de registro

## 🔍 Proceso de Aprobación Completo

### Paso 1: Preparar Facebook Business Manager
1. Crea una cuenta en: https://business.facebook.com
2. Verifica tu cuenta de Facebook Business Manager
3. Asegúrate de tener permisos de administrador

### Paso 2: Crear Cuenta de WhatsApp Business API
1. En Facebook Business Manager, ve a "WhatsApp Accounts"
2. Crea una nueva cuenta de WhatsApp Business API (WABA)
3. Completa el perfil de la cuenta

### Paso 3: Solicitar Número en Twilio
1. Ve a: https://console.twilio.com/us1/develop/sms/whatsapp/learn
2. Haz clic en "Get Started" o "Request WhatsApp Business Number"
3. Completa el formulario con:
   - Número de teléfono empresarial
   - Nombre de visualización
   - Información de la empresa
   - Descripción del uso

### Paso 4: Verificación del Número
1. Twilio enviará un código por **llamada o SMS** al número
2. **Asegúrate de poder recibir** llamadas/mensajes internacionales
3. Ingresa el código en el proceso de registro
4. Verifica la propiedad del número

### Paso 5: Revisión y Aprobación
- Twilio y WhatsApp revisarán tu solicitud
- Pueden pedirte información adicional
- El proceso puede tardar **3-7 días hábiles** (a veces más)
- Recibirás emails de actualización del estado

### Paso 6: Aprobación Final
- Recibirás un email cuando tu número sea aprobado
- El número aparecerá en tu panel de Twilio
- Podrás empezar a enviar mensajes a cualquier número

## ⚠️ Requisitos Importantes

### Para Empresas (B2B)
- ✅ **Número de teléfono empresarial** (no personal)
- ✅ **Cuenta de Facebook Business Manager verificada**
- ✅ **Cuenta de WhatsApp Business API (WABA)**
- ✅ **Nombre de visualización apropiado**
- ✅ **Documentación de la empresa** (pueden solicitarla)
- ✅ **Descripción clara del uso** del servicio

### Para Negocios Pequeños
- ✅ **Número de teléfono empresarial** verificado
- ✅ **Cuenta de Facebook Business Manager**
- ✅ **Cuenta de WhatsApp Business API**
- ✅ **Descripción del negocio**
- ✅ **Nombre de visualización** relacionado con el negocio

### Restricciones Comunes
- ❌ **No se aprueban números personales** para uso comercial masivo
- ❌ **No se aprueban números virtuales** sin verificación adecuada
- ❌ **No se aprueban** sin cuenta de Facebook Business Manager
- ❌ **No se aprueban** sin cuenta de WhatsApp Business API
- ❌ **No se aprueban** si el nombre de visualización no es apropiado
- ❌ **No se aprueban** si el número no puede recibir llamadas/SMS internacionales

## 📝 Ejemplo de Descripción del Negocio

**Buena descripción:**
> "Somos una empresa de recambios de automóviles que envía notificaciones a nuestros clientes sobre disponibilidad de piezas, ofertas especiales y recordatorios de mantenimiento. Los mensajes son opt-in y los clientes pueden darse de baja en cualquier momento."

**Mala descripción:**
> "Enviar mensajes a clientes"

## 🎯 Consejos para Aprobación Rápida

1. **Documentación completa**: Asegúrate de tener todos los documentos listos antes de solicitar
2. **Descripción detallada**: Explica claramente cómo usarás WhatsApp Business
3. **Número empresarial**: Usa un número de teléfono empresarial, no personal
4. **Sitio web**: Tener un sitio web profesional ayuda mucho
5. **Política de privacidad**: Si tienes sitio web, incluye política de privacidad
6. **Responder rápido**: Si Twilio pide información adicional, responde lo antes posible

## 📞 Alternativa: Empezar con Sandbox

Mientras esperas la aprobación, puedes:

1. **Usar el Sandbox de Twilio** (gratis, sin aprobación)
2. **Probar todas las funcionalidades** con tu número personal verificado
3. **Desarrollar y probar** la aplicación completamente
4. **Migrar al número de producción** cuando sea aprobado (solo cambiar una variable)

## 🔄 Migración desde Sandbox

Cuando tu número sea aprobado:

1. **Actualiza la variable de entorno**:
   ```bash
   TWILIO_WHATSAPP_NUMBER=whatsapp:+34625433667  # Tu número aprobado
   ```

2. **O desde la aplicación**:
   - Ve a `/configuracion/twilio`
   - Actualiza el número
   - Guarda

3. **Actualiza el webhook** en Twilio para el nuevo número

4. **¡Listo!** Tu aplicación funcionará con el número de producción

## 📚 Recursos Útiles

- **Guía oficial de Twilio**: https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-message
- **Centro de ayuda**: https://support.twilio.com/hc/en-us
- **Panel de Twilio**: https://console.twilio.com

## ⏱️ Tiempos Estimados

- **Sandbox**: Inmediato (solo verificar tu número)
- **Número de producción**: 3-7 días hábiles (puede variar)
- **Revisión adicional**: +2-3 días si piden más información

## 💡 Recomendación para Recambios RM

### Plan de Acción Recomendado:

**Fase 1: Preparación (Mientras pruebas con Sandbox)**
1. ✅ Crea cuenta en **Facebook Business Manager**: https://business.facebook.com
2. ✅ Verifica tu cuenta de Facebook Business Manager
3. ✅ Crea una **Cuenta de WhatsApp Business API (WABA)** en Facebook
4. ✅ Prepara el **número de teléfono empresarial** que usarás
5. ✅ Asegúrate de que el número **puede recibir llamadas/SMS internacionales**

**Fase 2: Pruebas con Sandbox**
1. ✅ Usa el **Sandbox de Twilio** con tu número personal
2. ✅ Prueba toda la aplicación completamente
3. ✅ Verifica que todo funciona correctamente

**Fase 3: Solicitar Número de Producción**
1. ✅ Ve a Twilio y solicita el número de WhatsApp Business
2. ✅ Usa el **número de teléfono empresarial**
3. ✅ Nombre de visualización: **"Recambios RM"** o similar
4. ✅ Descripción: "Notificaciones a clientes sobre disponibilidad de recambios de automóviles, ofertas especiales y recordatorios de mantenimiento. Los mensajes son opt-in y los clientes pueden darse de baja en cualquier momento."
5. ✅ Asocia tu cuenta de WhatsApp Business API (WABA)

**Fase 4: Migración**
1. ✅ Cuando sea aprobado (3-7 días), actualiza `TWILIO_WHATSAPP_NUMBER`
2. ✅ Configura el webhook en Twilio
3. ✅ ¡Listo para producción!

**No hay problema en empezar con tu número personal (Sandbox) y luego cambiar al de la empresa cuando esté aprobado.**

