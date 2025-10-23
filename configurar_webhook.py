#!/usr/bin/env python3
"""
Script para configurar el webhook de Green-API para recibir mensajes
"""

import requests
import json
import os

def configurar_webhook():
    """Configurar webhook en Green-API para recibir mensajes"""
    
    # Configuración de Green-API
    try:
        if os.environ.get('RENDER'):
            from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
        else:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
    except ImportError:
        print("❌ Error: No se encontró la configuración de Green-API")
        print("Asegúrate de tener configurado green_api_config.py o las variables de entorno")
        return False
    
    # URL del webhook (debe ser accesible desde internet)
    # Esta debe ser la URL de TU aplicación web, no la de Green-API
    webhook_url = input("Ingresa la URL completa de tu webhook (ej: https://tu-dominio.com/webhook/whatsapp): ")
    
    if not webhook_url:
        print("❌ Error: Debe proporcionar una URL válida")
        return False
    
    try:
        # URL para configurar el webhook
        instance_id = GREEN_API_INSTANCE_ID
        url = f"{GREEN_API_URL}/waInstance{instance_id}/setSettings/{GREEN_API_TOKEN}"
        
        # Datos para configurar el webhook
        data = {
            "webhookUrl": webhook_url,
            "webhookUrlToken": "",  # Token opcional para seguridad
            "outgoingWebhook": "yes",
            "outgoingMessageWebhook": "yes",
            "incomingMessageWebhook": "yes",
            "stateWebhook": "yes",
            "deviceWebhook": "yes"
        }
        
        print(f"🔧 Configurando webhook en Green-API...")
        print(f"URL: {webhook_url}")
        print(f"API URL: {url}")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook configurado exitosamente!")
            print(f"Respuesta: {result}")
            
            # Verificar configuración actual
            verificar_configuracion()
            return True
        else:
            print(f"❌ Error configurando webhook: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_configuracion():
    """Verificar la configuración actual del webhook"""
    try:
        if os.environ.get('RENDER'):
            from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
        else:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
        
        instance_id = GREEN_API_INSTANCE_ID
        url = f"{GREEN_API_URL}/waInstance{instance_id}/getSettings/{GREEN_API_TOKEN}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            settings = response.json()
            print("\n📋 Configuración actual:")
            print(f"- Webhook URL: {settings.get('webhookUrl', 'No configurado')}")
            print(f"- Webhook Token: {settings.get('webhookUrlToken', 'No configurado')}")
            print(f"- Outgoing Webhook: {settings.get('outgoingWebhook', 'No')}")
            print(f"- Incoming Message Webhook: {settings.get('incomingMessageWebhook', 'No')}")
            print(f"- State Webhook: {settings.get('stateWebhook', 'No')}")
            print(f"- Device Webhook: {settings.get('deviceWebhook', 'No')}")
        else:
            print(f"❌ Error verificando configuración: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")

def probar_webhook():
    """Probar el webhook enviando un mensaje de prueba"""
    print("\n🧪 Para probar el webhook:")
    print("1. Envía un mensaje de WhatsApp al número configurado en Green-API")
    print("2. Ve a tu aplicación web en la sección 'Mensajes Recibidos'")
    print("3. El mensaje debería aparecer automáticamente")
    
    numero_test = input("\n¿Quieres enviar un mensaje de prueba? (s/n): ")
    if numero_test.lower() == 's':
        numero = input("Ingresa el número de teléfono (con código país): ")
        mensaje = input("Ingresa el mensaje de prueba: ")
        
        try:
            if os.environ.get('RENDER'):
                from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
            else:
                from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID
            
            instance_id = GREEN_API_INSTANCE_ID
            url = f"{GREEN_API_URL}/waInstance{instance_id}/sendMessage/{GREEN_API_TOKEN}"
            
            data = {
                "chatId": f"{numero}@c.us",
                "message": f"🧪 Mensaje de prueba desde Recambios RM:\n\n{mensaje}\n\nResponde a este mensaje para probar la recepción."
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mensaje de prueba enviado! ID: {result.get('idMessage')}")
                print("Ahora responde a ese mensaje desde WhatsApp para probar la recepción.")
            else:
                print(f"❌ Error enviando mensaje de prueba: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Configurador de Webhook para Green-API")
    print("=" * 50)
    
    # Verificar configuración actual
    print("1. Verificando configuración actual...")
    verificar_configuracion()
    
    # Configurar webhook
    print("\n2. Configurando webhook...")
    if configurar_webhook():
        # Probar webhook
        print("\n3. Probando webhook...")
        probar_webhook()
    
    print("\n✅ Configuración completada!")
    print("\n📝 Instrucciones:")
    print("- Los mensajes recibidos aparecerán en: /mensajes-recibidos")
    print("- Puedes responder desde la aplicación web")
    print("- El historial se guarda automáticamente en la base de datos")
