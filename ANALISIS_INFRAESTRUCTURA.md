# 📊 Análisis de Infraestructura - Capacidad para 200 Conversaciones/Día

## 📈 Carga Estimada

- **200 conversaciones/día** × **10 mensajes/conversación** = **~2,000 mensajes/día**
- **Promedio**: ~0.023 mensajes/segundo
- **Picos estimados**: 1-5 mensajes/segundo (horas pico: 9-13h, 16-20h)
- **Webhooks entrantes**: ~2,000/día (uno por mensaje recibido)
- **Consultas API**: ~100-200/día (usuarios consultando conversaciones)

## ✅ Estado Actual de la Infraestructura

### **Fortalezas:**

1. **PostgreSQL en Render**
   - ✅ Base de datos robusta y escalable
   - ✅ Pool de conexiones configurado (`pool_pre_ping`, `pool_recycle`)
   - ✅ Índices en campos clave (`contact_number`, `conversation_id`, `sent_at`, `is_read`)

2. **Arquitectura**
   - ✅ Webhooks para recibir mensajes (más eficiente que polling)
   - ✅ Separación entre mensajes entrantes y salientes
   - ✅ Sistema de conversaciones estructurado

3. **Optimizaciones Existentes**
   - ✅ `lazy='dynamic'` en relaciones (evita cargar todos los mensajes)
   - ✅ Índices en campos de búsqueda frecuente
   - ✅ Pool de conexiones con reciclado automático

### **Áreas de Mejora Identificadas:**

#### 🔴 **CRÍTICAS (Implementar antes de producción):**

1. **Pool de Conexiones Insuficiente**
   ```python
   # Actual: Sin límites explícitos
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
       'pool_pre_ping': True,
       'pool_recycle': 300,
   }
   ```
   **Problema**: Sin `pool_size` y `max_overflow`, puede agotar conexiones en picos.
   **Solución**: Añadir límites explícitos.

2. **Queries N+1 en Lista de Conversaciones**
   ```python
   # Línea 2550: Carga todas las conversaciones sin optimización
   conversaciones = WhatsAppConversation.query.order_by(...).all()
   data = [_conversation_to_dict(c) for c in conversaciones]  # N+1 queries
   ```
   **Problema**: Por cada conversación, hace queries adicionales para `last_message()`, `last_agent_message()`, `unread_count()`.
   **Solución**: Usar `joinedload` o subconsultas.

3. **Falta de Caché**
   - Lista de conversaciones se consulta en cada request
   - Sin caché de consultas frecuentes

4. **Sin Límite de Paginación**
   - La lista de conversaciones carga TODAS las conversaciones
   - Con 200+ conversaciones, esto puede ser lento

#### 🟡 **IMPORTANTES (Implementar en corto plazo):**

5. **Índices Faltantes**
   - `whatsapp_message.sent_at` tiene índice, pero falta compuesto `(conversation_id, sent_at)`
   - `whatsapp_conversation.updated_at` no tiene índice (se usa para ordenar)

6. **Webhook sin Rate Limiting**
   - No hay protección contra spam de webhooks
   - Un ataque podría saturar la BD

7. **Logs Excesivos en Producción**
   - Muchos `print()` que deberían ser logs estructurados
   - Puede afectar rendimiento

## 🚀 Recomendaciones de Optimización

### **1. Optimizar Pool de Conexiones**

```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,          # Conexiones base
    'max_overflow': 20,       # Conexiones adicionales en picos
    'pool_timeout': 30,       # Timeout para obtener conexión
    'connect_args': {
        'sslmode': ssl_mode,
        'connect_timeout': 10
    }
}
```

### **2. Optimizar Query de Conversaciones (Eliminar N+1)**

```python
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy import func, select

@app.get('/whatsapp/api/conversaciones')
def whatsapp_api_conversations():
    # Cargar conversaciones con sus últimos mensajes en una sola query
    conversations = db.session.query(WhatsAppConversation)\
        .outerjoin(
            WhatsAppMessage,
            and_(
                WhatsAppMessage.conversation_id == WhatsAppConversation.id,
                WhatsAppMessage.sent_at == select(
                    func.max(WhatsAppMessage.sent_at)
                ).where(
                    WhatsAppMessage.conversation_id == WhatsAppConversation.id
                ).scalar_subquery()
            )
        )\
        .order_by(WhatsAppConversation.updated_at.desc())\
        .all()
    
    # Pre-cargar unread counts con subquery
    unread_counts = db.session.query(
        WhatsAppMessage.conversation_id,
        func.count(WhatsAppMessage.id).label('unread')
    ).filter_by(
        sender_type='customer',
        is_read=False
    ).group_by(WhatsAppMessage.conversation_id).all()
    
    unread_dict = {conv_id: count for conv_id, count in unread_counts}
    
    data = []
    for conv in conversations:
        data.append({
            'id': conv.id,
            'display_name': conv.contact_name or _chat_display(conv.contact_number),
            'unread_count': unread_dict.get(conv.id, 0),
            # ... resto de campos
        })
    
    return jsonify({'conversations': data})
```

### **3. Añadir Paginación**

```python
@app.get('/whatsapp/api/conversaciones')
def whatsapp_api_conversations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    pagination = WhatsAppConversation.query\
        .order_by(WhatsAppConversation.updated_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    data = [_conversation_to_dict(c) for c in pagination.items]
    return jsonify({
        'conversations': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })
```

### **4. Añadir Índices Compuestos**

```python
# En models.py o migración
# Índice compuesto para búsquedas frecuentes
db.Index('idx_message_conversation_sent', 
         WhatsAppMessage.conversation_id, 
         WhatsAppMessage.sent_at)

db.Index('idx_conversation_updated', 
         WhatsAppConversation.updated_at)
```

### **5. Implementar Caché (Opcional pero Recomendado)**

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.get('/whatsapp/api/conversaciones')
@cache.cached(timeout=5)  # Cache 5 segundos
def whatsapp_api_conversations():
    # ...
```

### **6. Rate Limiting para Webhooks**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

@app.route('/webhook/whatsapp', methods=['POST'])
@limiter.limit("100 per minute")  # Máximo 100 webhooks/minuto
def webhook_whatsapp():
    # ...
```

## 📊 Capacidad Estimada Post-Optimización

### **Con las optimizaciones:**

- ✅ **2,000 mensajes/día**: **SIN PROBLEMAS**
- ✅ **Picos de 10 mensajes/segundo**: **MANEJABLE**
- ✅ **Hasta 500 conversaciones activas**: **SOPORTABLE**
- ✅ **Hasta 5 usuarios simultáneos**: **ÓPTIMO**

### **Límites de Render (Plan Estándar):**

- **PostgreSQL**: Hasta 1GB de datos (suficiente para años)
- **Web Service**: 512MB RAM (suficiente con optimizaciones)
- **CPU**: Compartido pero suficiente para esta carga

## ⚠️ Señales de Alerta (Monitorear)

1. **Tiempo de respuesta > 2 segundos** en lista de conversaciones
2. **Errores de conexión a BD** (pool agotado)
3. **Webhooks fallando** (timeout o 500)
4. **Memoria > 400MB** en Render

## 🎯 Plan de Acción Recomendado

### **Fase 1 (CRÍTICA - Antes de producción):**
1. ✅ Añadir `pool_size` y `max_overflow` al pool de conexiones
2. ✅ Optimizar query de conversaciones (eliminar N+1)
3. ✅ Añadir paginación a la lista de conversaciones
4. ✅ Añadir índices compuestos

### **Fase 2 (IMPORTANTE - Primera semana):**
5. ✅ Implementar rate limiting en webhooks
6. ✅ Reemplazar `print()` por logging estructurado
7. ✅ Añadir métricas de rendimiento

### **Fase 3 (MEJORAS - Primer mes):**
8. ⚪ Implementar caché (si es necesario)
9. ⚪ Monitoreo y alertas
10. ⚪ Optimizaciones adicionales según métricas

## 💰 Costo Estimado en Render

- **PostgreSQL**: $7/mes (plan estándar)
- **Web Service**: $7/mes (plan estándar)
- **Total**: ~$14/mes

**Con esta carga, el plan gratuito podría funcionar, pero el estándar es más seguro.**

## ✅ Conclusión

**La infraestructura actual puede soportar 200 conversaciones/día**, pero necesita las optimizaciones críticas antes de producción para evitar problemas en picos de tráfico.

**Prioridad**: Implementar Fase 1 antes de lanzar a producción.

