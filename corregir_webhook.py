#!/usr/bin/env python3
"""
Script para corregir la configuración del webhook de Green-API
"""

import requests
import json

def corregir_configuracion_webhook():
    """Corregir la configuración del webhook para recibir mensajes"""
    
    # Configuración fija
    GREEN_API_URL = "https://7107.api.green-api.com"
    GREEN_API_TOKEN = "3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba"
    GREEN_API_INSTANCE_ID = "7107349111"
    
    print("🔧 Corrigiendo configuración del webhook...")
    print("Problema detectado:")
    print("- incomingWebhook: 'no' (debe ser 'yes')")
    print("- webhookUrl: apunta a Green-API (debe apuntar a tu aplicación)")
    
    # Solicitar URL correcta del webhook
    print("\n📝 Necesito la URL de tu aplicación web donde está desplegada.")
    print("Ejemplos:")
    print("- Si está en Render: https://tu-app.onrender.com/webhook/whatsapp")
    print("- Si está en Heroku: https://tu-app.herokuapp.com/webhook/whatsapp")
    print("- Si usas ngrok: https://abc123.ngrok.io/webhook/whatsapp")
    
    webhook_url = input("\nIngresa la URL completa de tu webhook: ")
    
    if not webhook_url:
        print("❌ Error: Debe proporcionar una URL válida")
        return False
    
    try:
        # URL para configurar el webhook
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/setSettings/{GREEN_API_TOKEN}"
        
        # Configuración CORRECTA para recibir mensajes
        data = {
            "webhookUrl": webhook_url,
            "webhookUrlToken": "",  # Token opcional para seguridad
            "incomingWebhook": "yes",  # ¡IMPORTANTE! Habilitar mensajes entrantes
            "incomingMessageWebhook": "yes",  # ¡IMPORTANTE! Habilitar mensajes entrantes
            "outgoingWebhook": "yes",
            "outgoingMessageWebhook": "yes",
            "stateWebhook": "yes",
            "deviceWebhook": "yes"
        }
        
        print(f"\n🔧 Configurando webhook correctamente...")
        print(f"Webhook URL: {webhook_url}")
        print(f"incomingWebhook: yes")
        print(f"incomingMessageWebhook: yes")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook configurado correctamente!")
            print(f"Respuesta: {result}")
            
            # Verificar que se aplicó correctamente
            verificar_configuracion_corregida()
            return True
        else:
            print(f"❌ Error configurando webhook: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_configuracion_corregida():
    """Verificar que la configuración se aplicó correctamente"""
    GREEN_API_URL = "https://7107.api.green-api.com"
    GREEN_API_TOKEN = "3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba"
    GREEN_API_INSTANCE_ID = "7107349111"
    
    try:
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/getSettings/{GREEN_API_TOKEN}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            settings = response.json()
            print("\n📋 Verificando configuración corregida:")
            print(f"- Webhook URL: {settings.get('webhookUrl', 'No configurado')}")
            print(f"- Incoming Webhook: {settings.get('incomingWebhook', 'No')}")
            print(f"- Incoming Message Webhook: {settings.get('incomingMessageWebhook', 'No')}")
            print(f"- Outgoing Webhook: {settings.get('outgoingWebhook', 'No')}")
            print(f"- State Webhook: {settings.get('stateWebhook', 'No')}")
            
            # Verificar si está correcto
            if (settings.get('incomingWebhook') == 'yes' and 
                settings.get('incomingMessageWebhook') == 'yes' and
                settings.get('webhookUrl') != 'https://7107.api.green-api.com'):
                print("\n✅ ¡Configuración corregida exitosamente!")
                print("Ahora los mensajes entrantes deberían llegar a tu aplicación.")
            else:
                print("\n⚠️ La configuración aún no está correcta.")
                print("Verifica que la URL del webhook sea la de tu aplicación.")
        else:
            print(f"❌ Error verificando configuración: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")

def probar_recepcion():
    """Instrucciones para probar la recepción"""
    print("\n🧪 Para probar la recepción de mensajes:")
    print("1. Asegúrate de que tu aplicación esté ejecutándose")
    print("2. Envía un mensaje de WhatsApp al número: 34625433667")
    print("3. Ve a tu aplicación web en la sección 'Mensajes Recibidos'")
    print("4. El mensaje debería aparecer automáticamente")
    print("\n💡 Si no funciona:")
    print("- Verifica que la URL del webhook sea accesible desde internet")
    print("- Revisa los logs de tu aplicación")
    print("- Asegúrate de que el endpoint /webhook/whatsapp esté funcionando")

if __name__ == "__main__":
    print("🚀 Corrector de Configuración de Webhook - Green-API")
    print("=" * 60)
    print("Problema detectado: Los mensajes entrantes no están habilitados")
    print("=" * 60)
    
    if corregir_configuracion_webhook():
        probar_recepcion()
    
    print("\n✅ Proceso completado!")
