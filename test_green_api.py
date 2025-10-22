#!/usr/bin/env python3
"""
Script de prueba rápida para verificar Green-API
"""

import os
import sys

def test_green_api():
    print("🔍 Verificando configuración de Green-API...")
    
    try:
        # Verificar entorno
        if os.environ.get('RENDER'):
            print("🌐 Entorno: Producción (Render)")
            from config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
        else:
            print("💻 Entorno: Desarrollo local")
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN, GREEN_API_INSTANCE_ID, GREEN_API_PHONE
        
        print(f"📡 URL: {GREEN_API_URL}")
        print(f"🔑 Token: {GREEN_API_TOKEN[:10]}...")
        print(f"📱 Instancia: {GREEN_API_INSTANCE_ID}")
        print(f"📞 Teléfono: {GREEN_API_PHONE}")
        
        # Probar conexión
        print("\n🔌 Probando conexión...")
        from whatsapp_sender import configurar_green_api
        
        conectado, mensaje = configurar_green_api(GREEN_API_URL, GREEN_API_TOKEN)
        
        if conectado:
            print("✅ Conexión exitosa!")
            print(f"📝 Mensaje: {mensaje}")
            
            # Probar envío de mensaje
            print("\n📤 Probando envío de mensaje...")
            from whatsapp_sender import green_api_sender
            
            # Usar el número configurado como prueba
            numero_prueba = GREEN_API_PHONE
            mensaje_prueba = "🧪 Mensaje de prueba desde Recambios RM - Sistema funcionando correctamente"
            
            success, error = green_api_sender.send_message(numero_prueba, mensaje_prueba)
            
            if success:
                print(f"✅ Mensaje enviado exitosamente a {numero_prueba}")
            else:
                print(f"❌ Error enviando mensaje: {error}")
                
        else:
            print("❌ Error de conexión!")
            print(f"📝 Mensaje: {mensaje}")
            
    except ImportError as e:
        print(f"❌ Error importando configuración: {e}")
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == '__main__':
    test_green_api()

