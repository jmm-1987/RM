# 📱 Sistema de Mensajes Recibidos - Recambios RM

## 🎯 Funcionalidades Implementadas

✅ **Recepción de mensajes**: Los mensajes de WhatsApp llegan automáticamente a tu aplicación
✅ **Interfaz web**: Ve todos los mensajes recibidos en una interfaz amigable
✅ **Respuesta directa**: Responde mensajes desde la aplicación web
✅ **Historial completo**: Todas las conversaciones se guardan en la base de datos
✅ **Tipos de mensaje**: Soporte para texto, imágenes, audio, video y documentos
✅ **Identificación de clientes**: Los mensajes se vinculan automáticamente con clientes existentes

## 🚀 Instalación y Configuración

### 1. Migrar Base de Datos
```bash
python migrar_mensajes_recibidos.py
```

### 2. Configurar Webhook en Green-API
```bash
python configurar_webhook.py
```

**Necesitarás:**
- La URL pública de tu aplicación (ej: `https://tu-dominio.com/webhook/whatsapp`)
- Si estás en desarrollo local, usa un túnel como ngrok:
  ```bash
  ngrok http 5000
  ```

### 3. Verificar Configuración
1. Ve a tu aplicación web
2. Navega a **"Mensajes Recibidos"** en el menú
3. Envía un mensaje de WhatsApp al número configurado
4. El mensaje debería aparecer automáticamente

## 📋 Cómo Usar el Sistema

### Ver Mensajes Recibidos
- **Ruta**: `/mensajes-recibidos`
- **Funciones**:
  - Ver mensajes sin leer (destacados en rojo)
  - Ver mensajes leídos
  - Marcar mensajes como leídos
  - Ver conversación completa
  - Responder mensajes

### Responder Mensajes
1. Haz clic en **"Responder"** en cualquier mensaje
2. Escribe tu respuesta
3. Haz clic en **"Enviar Respuesta"**
4. La respuesta se envía por WhatsApp y se guarda en el historial

### Ver Conversación Completa
1. Haz clic en **"Ver conversación"**
2. Ve todo el historial de mensajes con ese contacto
3. Puedes responder directamente desde ahí

## 🔧 Configuración Técnica

### Webhook URL
El webhook debe apuntar a: `https://tu-dominio.com/webhook/whatsapp`

### Tipos de Mensaje Soportados
- **Texto**: Mensajes de texto normales
- **Imagen**: Fotos con descripción opcional
- **Audio**: Mensajes de voz
- **Video**: Videos con descripción opcional
- **Documento**: Archivos PDF, documentos, etc.

### Base de Datos
Se crean automáticamente estas tablas:
- `mensaje_recibido`: Almacena mensajes entrantes
- `respuesta_mensaje`: Almacena respuestas enviadas

## 🛠️ Solución de Problemas

### Los mensajes no llegan
1. Verifica que el webhook esté configurado correctamente
2. Asegúrate de que la URL sea accesible desde internet
3. Revisa los logs de Green-API en su panel de control

### Error al responder
1. Verifica que Green-API esté configurado correctamente
2. Asegúrate de que el número de destino sea válido
3. Revisa que la instancia esté autorizada

### Base de datos no se actualiza
1. Verifica que la migración se ejecutó correctamente
2. Revisa los permisos de la base de datos
3. Ejecuta `python migrar_mensajes_recibidos.py` nuevamente

## 📱 Uso en Múltiples Dispositivos

### Opción 1: WhatsApp Multidispositivo (Recomendado)
1. En tu teléfono principal: WhatsApp → Configuración → Dispositivos vinculados
2. En otros dispositivos: Vincular a cuenta existente
3. Escanea el código QR
4. Todos los dispositivos pueden enviar/recibir mensajes

### Opción 2: Solo Aplicación Web
- Usa únicamente la aplicación web para gestionar mensajes
- Los mensajes llegan automáticamente al webhook
- Puedes responder desde cualquier dispositivo con acceso web

## 🔒 Seguridad

- El webhook está protegido contra ataques básicos
- Los mensajes se almacenan de forma segura en la base de datos
- Las respuestas se envían solo a números válidos
- Se registra todo el historial para auditoría

## 📊 Monitoreo

### Logs de la Aplicación
Los mensajes recibidos se registran en la consola:
```
✅ Mensaje recibido de 34625433667: Hola, necesito un filtro de aire...
```

### Historial Completo
- Todos los mensajes se guardan en la base de datos
- Puedes consultar el historial completo en `/mensajes-recibidos`
- Las conversaciones se organizan por número de teléfono

## 🎉 ¡Listo!

Tu sistema de mensajes está completamente funcional. Ahora puedes:
- Recibir mensajes de WhatsApp automáticamente
- Responder desde la aplicación web
- Mantener un historial completo de conversaciones
- Usar el mismo número en múltiples dispositivos

¿Necesitas ayuda? Revisa los logs de la aplicación o contacta al soporte técnico.
