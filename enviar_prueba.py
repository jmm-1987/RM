import requests

GREEN_API_URL = 'https://7107.api.green-api.com'
GREEN_API_TOKEN = '3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba'
GREEN_API_INSTANCE_ID = '7107349111'

print('🧪 Enviando mensaje de prueba...')
print('Envía un mensaje de WhatsApp al número: 34625433667')
print('Luego ve a tu aplicación en: https://rm-p1r1.onrender.com/mensajes-recibidos')

# Enviar mensaje de prueba
url = f'{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}'

data = {
    'chatId': '34625433667@c.us',  # Enviar a ti mismo
    'message': '🧪 Mensaje de prueba desde Recambios RM:\n\nEste es un mensaje de prueba para verificar que el webhook funciona.\n\nResponde a este mensaje para probar la recepción automática.'
}

response = requests.post(url, json=data, timeout=30)

if response.status_code == 200:
    result = response.json()
    print(f'✅ Mensaje de prueba enviado! ID: {result.get("idMessage")}')
    print('Ahora responde a ese mensaje desde WhatsApp para probar la recepción.')
else:
    print(f'❌ Error enviando mensaje: {response.status_code}')
    print(f'Respuesta: {response.text}')
