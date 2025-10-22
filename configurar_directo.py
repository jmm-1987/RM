"""
Script para configurar Green-API de forma directa y hacer envío real
"""

from app import app
from whatsapp_sender import green_api_sender
from green_api_config import GREEN_API_URL, GREEN_API_TOKEN

def configurar_directo():
    """
    Configurar Green-API de forma directa
    """
    with app.app_context():
        print("=== CONFIGURACIÓN DIRECTA GREEN-API ===")
        
        # Configurar directamente los atributos
        green_api_sender.api_url = GREEN_API_URL
        green_api_sender.api_token = GREEN_API_TOKEN
        green_api_sender.simulate_mode = False
        
        print(f"Configuración aplicada:")
        print(f"  API URL: {green_api_sender.api_url}")
        print(f"  API Token: {green_api_sender.api_token}")
        print(f"  Modo simulación: {green_api_sender.simulate_mode}")
        
        # Verificar estado
        conectado, mensaje = green_api_sender.check_instance_status()
        print(f"Estado: {mensaje}")
        
        if conectado:
            print("\nHaciendo envío REAL...")
            success, error = green_api_sender.send_message("34625433667", "ENVÍO REAL DESDE RECAMBIOS RM - Sistema funcionando correctamente")
            
            if success:
                print("ENVÍO REAL EXITOSO")
                print("El sistema está listo para envíos masivos reales")
            else:
                print(f"Error: {error}")
        else:
            print("Error: Instancia no conectada")

if __name__ == '__main__':
    configurar_directo()





