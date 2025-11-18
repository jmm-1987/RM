# 📋 Referencias a Números de Teléfono en la Aplicación

## 🔍 Análisis de Referencias

### Número 34625433667 (625433667) - Green-API (Antiguo)

Este número aparece en varios lugares, principalmente en archivos de configuración antiguos de Green-API:

#### ✅ Archivos que NO afectan el código activo:
- `green_api_config.py` - Configuración de Green-API (ya no se usa)
- `templates/editar_cliente.html` - Solo como ejemplo en texto de ayuda
- Archivos de documentación (`.md`) - Solo ejemplos
- Scripts de prueba antiguos (`.py` en raíz)

#### ❌ Archivos que podrían causar conflictos:
- **Ninguno en el código activo** - `app.py` y `twilio_sender.py` NO tienen referencias hardcodeadas ✅

### Número 34619639616 - Twilio (Actual)

Este es el número que estás usando actualmente con Twilio:
- Configurado en variables de entorno: `TWILIO_WHATSAPP_NUMBER=whatsapp:+34619639616`
- No hay referencias hardcodeadas en el código ✅

## ⚠️ Posibles Conflictos

### 1. Archivo `green_api_config.py`
Este archivo todavía tiene el número viejo de Green-API:
```python
GREEN_API_PHONE = "34625433667"
```

**Solución:** Este archivo ya no se usa (migraste a Twilio), pero puedes eliminarlo o comentarlo para evitar confusión.

### 2. Scripts de Prueba Antiguos
Varios scripts en la raíz del proyecto tienen el número hardcodeado:
- `enviar_prueba.py`
- `debug_configuracion.py`
- `configurar_directo.py`
- etc.

**Solución:** Estos scripts son para Green-API y ya no se usan. Puedes eliminarlos o actualizarlos.

### 3. Variables de Entorno
Verifica que no tengas variables de entorno mezcladas:
- `GREEN_API_PHONE` (antigua, no debería estar)
- `TWILIO_WHATSAPP_NUMBER` (actual, debe ser `whatsapp:+34619639616`)

## ✅ Verificación

### Código Activo (app.py, twilio_sender.py)
✅ **NO hay referencias hardcodeadas** al número 34625433667
✅ **NO hay referencias hardcodeadas** al número 34619639616
✅ Los números se obtienen de variables de entorno correctamente

### Configuración Actual
- Twilio usa: `TWILIO_WHATSAPP_NUMBER` (debe ser `whatsapp:+34619639616`)
- Green-API ya no se usa (migración completada)

## 🔧 Recomendaciones

1. **Verifica variables de entorno en Render:**
   - Asegúrate de que `TWILIO_WHATSAPP_NUMBER=whatsapp:+34619639616`
   - Elimina cualquier variable `GREEN_API_*` si existe

2. **Limpia archivos antiguos (opcional):**
   - Puedes eliminar o renombrar `green_api_config.py`
   - Puedes eliminar scripts de prueba antiguos de Green-API

3. **Actualiza el ejemplo en editar_cliente.html:**
   - Cambiar el ejemplo de `34625433667` a un número genérico como `34612345678`

## 📝 Conclusión

**No hay conflictos en el código activo.** Las referencias al número 34625433667 están solo en:
- Archivos de configuración antiguos (no se usan)
- Documentación (solo ejemplos)
- Scripts de prueba antiguos (no se usan)

El código activo (`app.py`, `twilio_sender.py`) obtiene el número correctamente de las variables de entorno.

