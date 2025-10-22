"""
Script para configurar automáticamente Green-API con los datos proporcionados
"""

from app import app
from whatsapp_sender import configurar_green_api

def configurar_green_api_automatico():
    """
    Configurar Green-API con los datos de la instancia proporcionada
    """
    with app.app_context():
        try:
            # Intentar importar la configuración
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN
            
            print("Configurando Green-API...")
            print(f"URL: {GREEN_API_URL}")
            print(f"Token: {'*' * len(GREEN_API_TOKEN) if GREEN_API_TOKEN != '3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba' else 'NO CONFIGURADO'}")
            
            if GREEN_API_TOKEN == '3dd7b31137204b0ca3c233fd4f7ebda4cb0f594076244419ba':
                print("❌ Error: Debes configurar tu token real en green_api_config.py")
                print("1. Abre el archivo green_api_config.py")
                print("2. Reemplaza 'TU_TOKEN_AQUI' con tu token real de Green-API")
                print("3. Ejecuta este script nuevamente")
                return False, "Token no configurado"
            
            # Configurar Green-API
            conectado, mensaje = configurar_green_api(GREEN_API_URL, GREEN_API_TOKEN)
            
            if conectado:
                print(f"✅ Green-API configurado exitosamente: {mensaje}")
            else:
                print(f"❌ Error configurando Green-API: {mensaje}")
            
            return conectado, mensaje
            
        except ImportError:
            print("❌ Error: No se encontró el archivo green_api_config.py")
            print("Asegúrate de que el archivo existe y tiene la configuración correcta")
            return False, "Archivo de configuración no encontrado"
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
            return False, str(e)

if __name__ == '__main__':
    configurar_green_api_automatico()
