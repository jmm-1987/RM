"""
Script para probar el envío masivo con la base de datos actualizada
"""

from app import app, db
from models import MensajeEnviado, Cliente, MensajePlantilla, Zona
from whatsapp_sender import configurar_green_api, green_api_sender
from datetime import datetime

def probar_envio_masivo():
    """
    Probar el envío masivo con la base de datos actualizada
    """
    with app.app_context():
        print("=== PRUEBA DE ENVÍO MASIVO ===")
        
        try:
            # Configurar Green-API
            from green_api_config import GREEN_API_URL, GREEN_API_TOKEN
            conectado, mensaje = configurar_green_api(GREEN_API_URL, GREEN_API_TOKEN)
            
            if not conectado:
                print(f"Error: {mensaje}")
                return
            
            print(f"Green-API configurado: {mensaje}")
            
            # Obtener datos de prueba
            zona = Zona.query.first()
            plantilla = MensajePlantilla.query.first()
            cliente = Cliente.query.filter_by(zona_id=zona.id, activo=True).first()
            
            if not all([zona, plantilla, cliente]):
                print("Error: No hay datos suficientes para la prueba")
                return
            
            print(f"Zona: {zona.nombre}")
            print(f"Plantilla: {plantilla.nombre}")
            print(f"Cliente: {cliente.nombre} ({cliente.telefono})")
            
            # Crear mensaje personalizado
            mensaje_personalizado = plantilla.contenido.format(
                nombre_cliente=cliente.nombre,
                zona=zona.nombre
            )
            
            print(f"Mensaje: {mensaje_personalizado}")
            
            # Enviar mensaje
            print("\nEnviando mensaje...")
            success, error_msg = green_api_sender.send_message(cliente.telefono, mensaje_personalizado)
            
            # Registrar en base de datos
            mensaje_enviado = MensajeEnviado(
                cliente_id=cliente.id,
                plantilla_id=plantilla.id,
                mensaje_final=mensaje_personalizado,
                enviado=success,
                fecha_envio=datetime.utcnow() if success else None,
                error=error_msg if not success else None
            )
            db.session.add(mensaje_enviado)
            db.session.commit()
            
            if success:
                print("ENVÍO EXITOSO")
                print(f"Mensaje guardado en BD con ID: {mensaje_enviado.id}")
            else:
                print(f"Error en envío: {error_msg}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    probar_envio_masivo()




