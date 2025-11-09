"""
Script para verificar directamente la configuración de Green-API
"""

from app import app
from whatsapp_sender import configurar_green_api, green_api_sender

def verificar_configuracion():
    """
    Verificar que la configuración de Green-API esté funcionando
    """
    with app.app_context():
        print("=== VERIFICACIÓN DE CONFIGURACIÓN GREEN-API ===")
        
        try:
            from green_api_config import (
                GREEN_API_URL,
                GREEN_API_TOKEN,
                GREEN_API_INSTANCE_ID,
                GREEN_API_PHONE,
            )
            
            print(f"1. Datos de configuración:")
            print(f"   URL: {GREEN_API_URL}")
            print(f"   Token: {GREEN_API_TOKEN[:10]}...")
            
            print(f"\n2. Estado inicial:")
            print(f"   Modo simulación: {green_api_sender.simulate_mode}")
            print(f"   API URL: {green_api_sender.api_url}")
            print(f"   API Token: {green_api_sender.api_token}")
            
            print(f"\n3. Configurando Green-API...")
            conectado, mensaje = configurar_green_api(
                GREEN_API_URL,
                GREEN_API_TOKEN,
                GREEN_API_INSTANCE_ID,
                GREEN_API_PHONE,
            )
            
            print(f"\n4. Estado después de configuración:")
            print(f"   Modo simulación: {green_api_sender.simulate_mode}")
            print(f"   API URL: {green_api_sender.api_url}")
            print(f"   API Token: {green_api_sender.api_token}")
            print(f"   Conectado: {conectado}")
            print(f"   Mensaje: {mensaje}")
            
            if not green_api_sender.simulate_mode:
                print(f"\n5. Haciendo prueba de envío...")
                success, error = green_api_sender.send_message(
                    GREEN_API_PHONE or "34625433667",
                    "Prueba de envío real",
                )
                print(f"   Resultado: {success}")
                if error:
                    print(f"   Error: {error}")
            else:
                print(f"\n5. ERROR: Aún en modo simulación")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    verificar_configuracion()











