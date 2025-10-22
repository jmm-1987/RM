"""
Módulo para el envío de mensajes de WhatsApp usando Green-API
"""

import requests
import json
from typing import Dict, List, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GreenAPISender:
    """
    Clase para manejar el envío de mensajes de WhatsApp usando Green-API
    """
    
    def __init__(self, api_url: str = None, api_token: str = None):
        """
        Inicializar el sender de Green-API
        
        Args:
            api_url: URL de la API de Green-API (ej: https://7107.api.green-api.com)
            api_token: Token de autenticación de Green-API
        """
        self.api_url = api_url
        self.api_token = api_token
        self.simulate_mode = not (api_url and api_token)
        
        if not self.simulate_mode:
            logger.info(f"Green-API configurado: {api_url}")
    
    def send_message(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Enviar un mensaje de WhatsApp usando Green-API
        
        Args:
            phone_number: Número de teléfono del destinatario (con código país)
            message: Mensaje a enviar
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje de error)
        """
        if self.simulate_mode:
            return self._simulate_send(phone_number, message)
        else:
            return self._green_api_send(phone_number, message)
    
    def send_image(self, phone_number: str, image_path: str, caption: str = "") -> Tuple[bool, str]:
        """
        Enviar una imagen de WhatsApp usando Green-API
        
        Args:
            phone_number: Número de teléfono del destinatario (con código país)
            image_path: Ruta al archivo de imagen
            caption: Texto descriptivo de la imagen
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje de error)
        """
        if self.simulate_mode:
            return self._simulate_send_image(phone_number, image_path, caption)
        else:
            return self._green_api_send_image(phone_number, image_path, caption)
    
    def _simulate_send(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Simular envío de mensaje (para desarrollo/testing)
        """
        logger.info(f"SIMULANDO envío a {phone_number}: {message[:50]}...")
        
        # Simular éxito/error aleatorio para testing
        import random
        success = random.random() > 0.1  # 90% de éxito
        
        if success:
            logger.info(f"✓ Mensaje enviado exitosamente a {phone_number}")
            return True, ""
        else:
            error_msg = "Error simulado en el envío"
            logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
            return False, error_msg
    
    def _simulate_send_image(self, phone_number: str, image_path: str, caption: str) -> Tuple[bool, str]:
        """
        Simular envío de imagen (para desarrollo/testing)
        """
        logger.info(f"SIMULANDO envío de imagen a {phone_number}: {image_path}")
        
        # Simular éxito/error aleatorio para testing
        import random
        success = random.random() > 0.1  # 90% de éxito
        
        if success:
            logger.info(f"✓ Imagen enviada exitosamente a {phone_number}")
            return True, ""
        else:
            error_msg = "Error simulado en el envío de imagen"
            logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
            return False, error_msg
    
    def _green_api_send(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Envío real usando Green-API
        """
        try:
            # Formatear número de teléfono (agregar código país si no lo tiene)
            formatted_number = self._format_phone_number(phone_number)
            
            # URL del endpoint de Green-API
            # Extraer el ID de instancia correcto (7107349111)
            instance_id = "7107349111"
            url = f"{self.api_url}/waInstance{instance_id}/sendMessage/{self.api_token}"
            
            # Datos del mensaje
            data = {
                "chatId": f"{formatted_number}@c.us",
                "message": message
            }
            
            # Headers
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Enviando a Green-API: {url}")
            logger.info(f"Datos: {data}")
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('idMessage'):
                    logger.info(f"✓ Mensaje enviado exitosamente a {phone_number}. ID: {response_data['idMessage']}")
                    return True, ""
                else:
                    error_msg = f"Error en respuesta: {response_data}"
                    logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
                    return False, error_msg
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text}"
                logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error de conexión: {str(e)}"
            logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
            return False, error_msg
    
    def _green_api_send_image(self, phone_number: str, image_path: str, caption: str) -> Tuple[bool, str]:
        """
        Envío real de imagen usando Green-API
        """
        try:
            import os
            import base64
            
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                error_msg = f"Archivo de imagen no encontrado: {image_path}"
                logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
                return False, error_msg
            
            # Formatear número de teléfono
            formatted_number = self._format_phone_number(phone_number)
            
            # Leer y codificar la imagen en base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Obtener el nombre del archivo
            filename = os.path.basename(image_path)
            
            # URL del endpoint de Green-API para enviar archivos
            instance_id = "7107349111"
            url = f"{self.api_url}/waInstance{instance_id}/sendFileByUpload/{self.api_token}"
            
            # Datos del archivo
            data = {
                "chatId": f"{formatted_number}@c.us",
                "file": image_data,
                "filename": filename,
                "caption": caption
            }
            
            # Headers
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Enviando imagen a Green-API: {url}")
            logger.info(f"Archivo: {filename}, Tamaño: {len(image_data)} bytes")
            
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('idMessage'):
                    logger.info(f"✓ Imagen enviada exitosamente a {phone_number}. ID: {response_data['idMessage']}")
                    return True, ""
                else:
                    error_msg = f"Error en respuesta: {response_data}"
                    logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
                    return False, error_msg
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text}"
                logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
                return False, error_msg
                
        except FileNotFoundError as e:
            error_msg = f"Archivo no encontrado: {str(e)}"
            logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Error de conexión: {str(e)}"
            logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
            return False, error_msg
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Formatear número de teléfono para Green-API
        """
        # Limpiar el número (quitar espacios, guiones, etc.)
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Si no tiene código de país, agregar +34 (España)
        if clean_number.startswith('6') and len(clean_number) == 9:
            clean_number = '34' + clean_number
        elif clean_number.startswith('600') and len(clean_number) == 12:
            clean_number = '34' + clean_number[1:]  # Quitar el 0 inicial
        
        return clean_number
    
    def check_instance_status(self) -> Tuple[bool, str]:
        """
        Verificar el estado de la instancia de Green-API
        
        Returns:
            Tuple[bool, str]: (conectado, mensaje de estado)
        """
        if self.simulate_mode:
            return True, "Modo simulación activo"
        
        try:
            # Usar el ID de instancia correcto
            instance_id = "7107349111"
            url = f"{self.api_url}/waInstance{instance_id}/getStateInstance/{self.api_token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                state = data.get('stateInstance', 'unknown')
                if state == 'authorized':
                    return True, "Instancia autorizada y lista"
                else:
                    return False, f"Estado de instancia: {state}"
            else:
                return False, f"Error HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"
    
    def send_bulk_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Enviar múltiples mensajes
        
        Args:
            messages: Lista de diccionarios con 'phone' y 'message'
            
        Returns:
            Lista de resultados con 'success', 'phone', 'error'
        """
        results = []
        
        for msg_data in messages:
            phone = msg_data['phone']
            message = msg_data['message']
            
            success, error = self.send_message(phone, message)
            
            results.append({
                'phone': phone,
                'success': success,
                'error': error
            })
        
        return results

# Instancia global para usar en la aplicación
green_api_sender = GreenAPISender()

# Función de conveniencia para usar en la aplicación Flask
def enviar_whatsapp(telefono: str, mensaje: str) -> bool:
    """
    Función de conveniencia para enviar WhatsApp
    Mantiene compatibilidad con el código existente
    """
    success, _ = green_api_sender.send_message(telefono, mensaje)
    return success

# Configuración para producción
def configurar_green_api(api_url: str, api_token: str):
    """
    Configurar el sender para usar Green-API real
    """
    global green_api_sender
    
    # Configurar directamente los atributos de la instancia global
    green_api_sender.api_url = api_url
    green_api_sender.api_token = api_token
    green_api_sender.simulate_mode = False
    
    logger.info("Green-API configurado para envío real")
    
    # Verificar estado de la instancia
    conectado, mensaje = green_api_sender.check_instance_status()
    if conectado:
        logger.info(f"✓ Green-API conectado: {mensaje}")
    else:
        logger.warning(f"⚠ Green-API no conectado: {mensaje}")
    
    return conectado, mensaje
