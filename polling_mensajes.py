#!/usr/bin/env python3
"""
Script para implementar polling de mensajes como respaldo al webhook
"""

import requests
import time
from datetime import datetime, timedelta

def obtener_mensajes_polling():
    """Obtener mensajes usando polling de Green-API"""
    
    GREEN_API_URL = 'https://7107.api.green-api.com'
    GREEN_API_TOKEN = '3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba'
    GREEN_API_INSTANCE_ID = '7107349111'
    
    try:
        # URL para obtener mensajes
        url = f'{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/receiveNotification/{GREEN_API_TOKEN}'
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'body' in data:
                mensaje_data = data['body']
                
                if mensaje_data.get('typeWebhook') == 'incomingMessageReceived':
                    print(f"📨 Mensaje recibido por polling:")
                    print(f"   De: {mensaje_data.get('senderData', {}).get('sender', 'Desconocido')}")
                    print(f"   Mensaje: {mensaje_data.get('messageData', {}).get('textMessageData', {}).get('textMessage', 'Sin texto')}")
                    print(f"   Timestamp: {datetime.now()}")
                    
                    return mensaje_data
                else:
                    print(f"ℹ️ Notificación recibida: {mensaje_data.get('typeWebhook', 'Desconocido')}")
            else:
                print("ℹ️ No hay mensajes nuevos")
                
        elif response.status_code == 404:
            print("ℹ️ No hay mensajes en cola")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en polling: {e}")
    
    return None

def polling_continuo():
    """Ejecutar polling continuo de mensajes"""
    print("🔄 Iniciando polling de mensajes...")
    print("Presiona Ctrl+C para detener")
    
    try:
        while True:
            obtener_mensajes_polling()
            time.sleep(5)  # Consultar cada 5 segundos
            
    except KeyboardInterrupt:
        print("\n⏹️ Polling detenido")

if __name__ == "__main__":
    print("🚀 Polling de Mensajes - Green-API")
    print("=" * 40)
    
    # Probar una vez
    print("1. Probando polling una vez...")
    mensaje = obtener_mensajes_polling()
    
    if mensaje:
        print("✅ ¡Polling funciona! Los mensajes se pueden recibir por este método.")
    else:
        print("ℹ️ No hay mensajes nuevos en este momento.")
    
    # Preguntar si quiere polling continuo
    continuar = input("\n¿Quieres ejecutar polling continuo? (s/n): ")
    if continuar.lower() == 's':
        polling_continuo()
