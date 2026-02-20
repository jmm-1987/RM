# 📝 Configuración de Variables de Entorno para Desarrollo Local

## 🚀 Inicio Rápido

1. **Copia el archivo de ejemplo**:
   ```bash
   cp .env.example .env
   ```

2. **Edita el archivo `.env`** con tus valores reales:
   - Abre `.env` con tu editor de texto
   - Completa las variables necesarias (ver abajo)

3. **Instala las dependencias** (si aún no lo has hecho):
   ```bash
   pip install -r requirements.txt
   ```

4. **¡Listo!** La aplicación cargará automáticamente las variables del archivo `.env`

## 📋 Variables Necesarias

### Base de Datos (PostgreSQL)

```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nombre_bd
```

**Ejemplo:**
```env
DATABASE_URL=postgresql://postgres:mipassword@localhost:5432/recambios_rm
```

### Twilio (WhatsApp)

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

**Dónde encontrarlas:**
- Ve a: https://console.twilio.com
- En el Dashboard encontrarás Account SID y Auth Token
- Para el número, usa el Sandbox: `whatsapp:+14155238886` (ver `GUIA_SANDBOX_TWILIO.md`)

### Configuración de la Aplicación

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
PORT=5000
```

**Generar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🔒 Seguridad

- ✅ El archivo `.env` está en `.gitignore` (NO se sube a Git)
- ✅ El archivo `.env.example` es solo una plantilla (sin valores reales)
- ⚠️ **NUNCA** subas el archivo `.env` a Git o repositorios públicos

## 📖 Más Información

- **Twilio Sandbox**: Ver `GUIA_SANDBOX_TWILIO.md`
- **Configuración de Twilio**: Ver `TWILIO_SETUP.md`
- **Base de datos**: Asegúrate de tener PostgreSQL instalado y corriendo localmente

## 🆘 Solución de Problemas

### La aplicación no carga las variables del .env

1. Verifica que el archivo se llame exactamente `.env` (con el punto al inicio)
2. Verifica que esté en la raíz del proyecto (mismo nivel que `app.py`)
3. Reinicia la aplicación después de crear/modificar el `.env`

### Error: "ModuleNotFoundError: No module named 'dotenv'"

Instala python-dotenv:
```bash
pip install python-dotenv
```

O instala todas las dependencias:
```bash
pip install -r requirements.txt
```

### Las variables no se cargan correctamente

1. Verifica que no haya espacios alrededor del `=` en el `.env`
2. No uses comillas en los valores (a menos que sean parte del valor)
3. Cada variable debe estar en una línea separada

## ✅ Verificar que Funciona

Después de configurar el `.env`, puedes verificar que las variables se cargan correctamente:

```python
# En Python
from config import TWILIO_ACCOUNT_SID, DATABASE_URL
print(f"Account SID: {TWILIO_ACCOUNT_SID[:10]}...")
print(f"Database: {DATABASE_URL[:30]}...")
```

O simplemente ejecuta la aplicación y verifica que no hay errores de configuración.


