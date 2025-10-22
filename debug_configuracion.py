"""
Script para debuggear la configuración de Green-API
"""

from app import app
from whatsapp_sender import GreenAPISender

def debug_configuracion():
    """
    Debuggear la configuración de Green-API
    """
    with app.app_context():
        print("=== DEBUG CONFIGURACIÓN GREEN-API ===")
        
        try:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN
            
            print(f"1. Datos del archivo de configuración:")
            print(f"   GREEN_API_URL: {GREEN_API_URL}")
            print(f"   GREEN_API_TOKEN: {GREEN_API_TOKEN}")
            print(f"   Tipo URL: {type(GREEN_API_URL)}")
            print(f"   Tipo Token: {type(GREEN_API_TOKEN)}")
            
            print(f"\n2. Creando nueva instancia directamente:")
            sender_directo = GreenAPISender(GREEN_API_URL, GREEN_API_TOKEN)
            print(f"   Modo simulación: {sender_directo.simulate_mode}")
            print(f"   API URL: {sender_directo.api_url}")
            print(f"   API Token: {sender_directo.api_token}")
            
            print(f"\n3. Probando envío con instancia directa:")
            success, error = sender_directo.send_message("34625433667", "Prueba directa")
            print(f"   Resultado: {success}")
            if error:
                print(f"   Error: {error}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    debug_configuracion()





