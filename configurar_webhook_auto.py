#!/usr/bin/env python3
"""
Script para configurar automáticamente el webhook de Green-API
"""

import requests
import json
import os

def configurar_webhook_automatico():
    """Configurar webhook automáticamente usando la configuración fija"""
    
    # Configuración fija de Green-API
    GREEN_API_URL = "https://7107.api.green-api.com"
    GREEN_API_TOKEN = "3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba"
    GREEN_API_INSTANCE_ID = "7107349111"
    
    print("🔧 Configuración automática de webhook")
    print(f"Instance ID: {GREEN_API_INSTANCE_ID}")
    print(f"API URL: {GREEN_API_URL}")
    
    # Solicitar URL del webhook
    webhook_url = input("\nIngresa la URL completa de tu webhook (ej: https://tu-dominio.com/webhook/whatsapp): ")
    
    if not webhook_url:
        print("❌ Error: Debe proporcionar una URL válida")
        return False
    
    try:
        # URL para configurar el webhook
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/setSettings/{GREEN_API_TOKEN}"
        
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
        
        print(f"\n🔧 Configurando webhook...")
        print(f"Webhook URL: {webhook_url}")
        print(f"API Endpoint: {url}")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook configurado exitosamente!")
            print(f"Respuesta: {result}")
            
            # Verificar configuración actual
            verificar_configuracion_actual()
            return True
        else:
            print(f"❌ Error configurando webhook: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_configuracion_actual():
    """Verificar la configuración actual del webhook"""
    GREEN_API_URL = "https://7107.api.green-api.com"
    GREEN_API_TOKEN = "3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba"
    GREEN_API_INSTANCE_ID = "7107349111"
    
    try:
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/getSettings/{GREEN_API_TOKEN}"
        
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
            
            # Verificar estado de la instancia
            verificar_estado_instancia()
        else:
            print(f"❌ Error verificando configuración: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")

def verificar_estado_instancia():
    """Verificar el estado de la instancia de WhatsApp"""
    GREEN_API_URL = "https://7107.api.green-api.com"
    GREEN_API_TOKEN = "3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba"
    GREEN_API_INSTANCE_ID = "7107349111"
    
    try:
        url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/getStateInstance/{GREEN_API_TOKEN}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            state = response.json()
            estado = state.get('stateInstance', 'unknown')
            print(f"\n📱 Estado de la instancia: {estado}")
            
            if estado == 'authorized':
                print("✅ WhatsApp está autorizado y listo para enviar/recibir mensajes")
            elif estado == 'notAuthorized':
                print("❌ WhatsApp no está autorizado. Necesitas escanear el código QR")
            elif estado == 'blocked':
                print("❌ WhatsApp está bloqueado. Contacta con soporte")
            else:
                print(f"⚠️ Estado desconocido: {estado}")
        else:
            print(f"❌ Error verificando estado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando estado: {e}")

def probar_envio_mensaje():
    """Probar el envío de un mensaje"""
    GREEN_API_URL = "https://7107.api.green-api.com"
    GREEN_API_TOKEN = "3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba"
    GREEN_API_INSTANCE_ID = "7107349111"
    
    print("\n🧪 Prueba de envío de mensaje")
    numero_test = input("¿Quieres enviar un mensaje de prueba? (s/n): ")
    
    if numero_test.lower() == 's':
        numero = input("Ingresa el número de teléfono (con código país, ej: 34625433667): ")
        mensaje = input("Ingresa el mensaje de prueba: ")
        
        try:
            url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"
            
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
                print(f"Respuesta: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Configurador Automático de Webhook - Green-API")
    print("=" * 60)
    print("Configuración fija:")
    print("- Instance ID: 7107349111")
    print("- API URL: https://7107.api.green-api.com")
    print("- Token: 3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba")
    print("=" * 60)
    
    # Verificar configuración actual
    print("\n1. Verificando configuración actual...")
    verificar_configuracion_actual()
    
    # Configurar webhook
    print("\n2. Configurando webhook...")
    if configurar_webhook_automatico():
        # Probar envío
        print("\n3. Probando envío de mensajes...")
        probar_envio_mensaje()
    
    print("\n✅ Configuración completada!")
    print("\n📝 Instrucciones:")
    print("- Los mensajes recibidos aparecerán en: /mensajes-recibidos")
    print("- Puedes responder desde la aplicación web")
    print("- El historial se guarda automáticamente en la base de datos")
    print("- Si WhatsApp no está autorizado, escanea el código QR en el panel de Green-API")
