"""
Script para hacer una prueba de envío real con Green-API
"""

from app import app
from whatsapp_sender import configurar_green_api, green_api_sender

def prueba_envio_real():
    """
    Hacer una prueba de envío real con Green-API
    """
    with app.app_context():
        print("Configurando Green-API para envío real...")
        
        try:
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN
            
            # Configurar Green-API
            conectado, mensaje = configurar_green_api(GREEN_API_URL, GREEN_API_TOKEN)
            
            if conectado:
                print(f"Green-API conectado: {mensaje}")
                
                # Verificar estado
                estado_conectado, estado_mensaje = green_api_sender.check_instance_status()
                print(f"Estado de instancia: {estado_mensaje}")
                
                if estado_conectado:
                    print("Haciendo prueba de envío real...")
                    
                    # Número de prueba (puedes cambiarlo por el tuyo)
                    numero_prueba = "34625433667"  # Tu número de la instancia
                    mensaje_prueba = "Prueba de envío REAL desde Recambios RM - Sistema funcionando correctamente"
                    
                    print(f"Enviando mensaje a {numero_prueba}...")
                    print(f"Mensaje: {mensaje_prueba}")
                    
                    success, error = green_api_sender.send_message(numero_prueba, mensaje_prueba)
                    
                    if success:
                        print("ENVÍO REAL EXITOSO - El sistema está funcionando correctamente")
                    else:
                        print(f"Error en envío real: {error}")
                else:
                    print(f"Instancia no conectada: {estado_mensaje}")
            else:
                print(f"Error conectando con Green-API: {mensaje}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    prueba_envio_real()





