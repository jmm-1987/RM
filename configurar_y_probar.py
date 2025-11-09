"""
Script para configurar Green-API y hacer envío real
"""

from app import app
from whatsapp_sender import configurar_green_api, green_api_sender

def configurar_y_probar():
    """
    Configurar Green-API y hacer una prueba de envío real
    """
    with app.app_context():
        print("=== CONFIGURANDO GREEN-API PARA ENVÍOS REALES ===")
        
        try:
            from green_api_config import (
                GREEN_API_URL,
                GREEN_API_TOKEN,
                GREEN_API_INSTANCE_ID,
                GREEN_API_PHONE,
            )
            
            print(f"URL: {GREEN_API_URL}")
            print(f"Token: {GREEN_API_TOKEN[:10]}...")
            
            # Configurar Green-API
            print("Configurando Green-API...")
            conectado, mensaje = configurar_green_api(
                GREEN_API_URL,
                GREEN_API_TOKEN,
                GREEN_API_INSTANCE_ID,
                GREEN_API_PHONE,
            )
            
            if conectado:
                print(f"Green-API configurado: {mensaje}")
                
                # Verificar que no esté en modo simulación
                print(f"Modo simulación: {green_api_sender.simulate_mode}")
                
                if not green_api_sender.simulate_mode:
                    print("MODO REAL ACTIVADO - Los envíos serán reales")
                    
                    # Hacer prueba de envío
                    numero_prueba = GREEN_API_PHONE or "34625433667"
                    mensaje_prueba = "PRUEBA REAL - Sistema Recambios RM funcionando correctamente"
                    
                    print(f"Enviando mensaje REAL a {numero_prueba}...")
                    success, error = green_api_sender.send_message(numero_prueba, mensaje_prueba)
                    
                    if success:
                        print("ENVÍO REAL EXITOSO")
                        print("El sistema está listo para envíos masivos reales")
                    else:
                        print(f"Error en envío real: {error}")
                else:
                    print("Aún en modo simulación")
            else:
                print(f"Error configurando Green-API: {mensaje}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    configurar_y_probar()
