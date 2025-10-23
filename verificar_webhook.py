import requests

GREEN_API_URL = 'https://7107.api.green-api.com'
GREEN_API_TOKEN = '3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba'
GREEN_API_INSTANCE_ID = '7107349111'

url = f'{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/getSettings/{GREEN_API_TOKEN}'
response = requests.get(url)
settings = response.json()

print('📋 Configuración actual del webhook:')
print(f'- Webhook URL: {settings.get("webhookUrl", "No configurado")}')
print(f'- Incoming Webhook: {settings.get("incomingWebhook", "No")}')
print(f'- Incoming Message Webhook: {settings.get("incomingMessageWebhook", "No")}')
print(f'- Outgoing Webhook: {settings.get("outgoingWebhook", "No")}')
print(f'- State Webhook: {settings.get("stateWebhook", "No")}')

# Verificar si está correcto
if (settings.get('incomingWebhook') == 'yes' and 
    settings.get('incomingMessageWebhook') == 'yes' and
    'rm-p1r1.onrender.com' in settings.get('webhookUrl', '')):
    print('\n✅ ¡Configuración correcta! Los mensajes entrantes están habilitados.')
    print('Ahora los mensajes de WhatsApp deberían llegar a tu aplicación.')
else:
    print('\n⚠️ La configuración aún no está correcta.')
    print('Verificando configuración...')
    for key, value in settings.items():
        if 'webhook' in key.lower() or 'incoming' in key.lower():
            print(f'  {key}: {value}')
