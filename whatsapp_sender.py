"""
Módulo para el envío de mensajes de WhatsApp usando Green-API
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_default_config() -> Dict[str, Optional[str]]:
    """
    Cargar configuración de Green-API desde variables de entorno o archivos locales.
    """
    config = {
        "api_url": os.environ.get("GREEN_API_URL"),
        "api_token": os.environ.get("GREEN_API_TOKEN"),
        "instance_id": os.environ.get("GREEN_API_INSTANCE_ID"),
        "phone": os.environ.get("GREEN_API_PHONE"),
    }

    if all(config.values()):
        return config

    # Determinar posibles fuentes según entorno
    fuentes = []
    if os.environ.get("RENDER"):
        fuentes.append("config")
    else:
        fuentes.extend(["green_api_config", "config"])

    for fuente in fuentes:
        try:
            if fuente == "config":
                from config import (  # type: ignore
                    GREEN_API_URL,
                    GREEN_API_TOKEN,
                    GREEN_API_INSTANCE_ID,
                    GREEN_API_PHONE,
                )
            else:
                from green_api_config import (  # type: ignore
                    GREEN_API_URL,
                    GREEN_API_TOKEN,
                    GREEN_API_INSTANCE_ID,
                    GREEN_API_PHONE,
                )

            config.setdefault("api_url", GREEN_API_URL)
            config.setdefault("api_token", GREEN_API_TOKEN)
            config.setdefault("instance_id", GREEN_API_INSTANCE_ID)
            config.setdefault("phone", GREEN_API_PHONE)
            break
        except ImportError:
            continue

    return config


class GreenAPISender:
    """
    Clase para manejar el envío de mensajes de WhatsApp usando Green-API
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        instance_id: Optional[str] = None,
        phone: Optional[str] = None,
    ):
        """
        Inicializar el sender de Green-API

        Args:
            api_url: URL de la API de Green-API (ej: https://7107.api.green-api.com)
            api_token: Token de autenticación de Green-API
            instance_id: ID de la instancia en Green-API
            phone: Número asociado a la instancia (informativo)
        """
        self.api_url = api_url
        self.api_token = api_token
        self.instance_id = instance_id
        self.phone = phone
        self._update_simulation_mode()

        if not self.simulate_mode:
            logger.info(
                "Green-API configurado: %s (Instancia: %s)",
                self.api_url,
                self.instance_id,
            )

    def send_message(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Enviar un mensaje de WhatsApp usando Green-API
        """
        if self.simulate_mode:
            return self._simulate_send(phone_number, message)
        return self._green_api_send(phone_number, message)

    def send_image(self, phone_number: str, image_path: str, caption: str = "") -> Tuple[bool, str]:
        """
        Enviar una imagen de WhatsApp usando Green-API
        """
        if self.simulate_mode:
            return self._simulate_send_image(phone_number, image_path, caption)
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

        error_msg = "Error simulado en el envío de imagen"
        logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
        return False, error_msg

    def _green_api_send(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Envío real usando Green-API
        """
        try:
            if not self.api_url or not self.api_token or not self.instance_id:
                error_msg = "Green-API no está configurado correctamente (falta URL, token o ID de instancia)"
                logger.error(error_msg)
                return False, error_msg

            # Formatear número de teléfono (agregar código país si no lo tiene)
            formatted_number = self._format_phone_number(phone_number)

            # URL del endpoint de Green-API
            url = f"{self.api_url}/waInstance{self.instance_id}/sendMessage/{self.api_token}"

            data = {
                "chatId": f"{formatted_number}@c.us",
                "message": message,
            }

            headers = {
                "Content-Type": "application/json"
            }

            logger.info(f"Enviando a Green-API: {url}")
            logger.info(f"Datos: {data}")

            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("idMessage"):
                    logger.info(f"✓ Mensaje enviado exitosamente a {phone_number}. ID: {response_data['idMessage']}")
                    return True, ""

                error_msg = f"Error en respuesta: {response_data}"
                logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
                return False, error_msg

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
            import base64

            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                error_msg = f"Archivo de imagen no encontrado: {image_path}"
                logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
                return False, error_msg

            if not self.api_url or not self.api_token or not self.instance_id:
                error_msg = "Green-API no está configurado correctamente (falta URL, token o ID de instancia)"
                logger.error(error_msg)
                return False, error_msg

            formatted_number = self._format_phone_number(phone_number)

            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            filename = os.path.basename(image_path)

            url = f"{self.api_url}/waInstance{self.instance_id}/sendFileByUpload/{self.api_token}"

            data = {
                "chatId": f"{formatted_number}@c.us",
                "file": image_data,
                "filename": filename,
                "caption": caption,
            }

            headers = {
                "Content-Type": "application/json"
            }

            logger.info(f"Enviando imagen a Green-API: {url}")
            logger.info(f"Archivo: {filename}, Tamaño: {len(image_data)} bytes")

            response = requests.post(url, json=data, headers=headers, timeout=60)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("idMessage"):
                    logger.info(f"✓ Imagen enviada exitosamente a {phone_number}. ID: {response_data['idMessage']}")
                    return True, ""

                error_msg = f"Error en respuesta: {response_data}"
                logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
                return False, error_msg

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
        clean_number = "".join(filter(str.isdigit, phone_number))

        if clean_number.startswith("6") and len(clean_number) == 9:
            clean_number = "34" + clean_number
        elif clean_number.startswith("600") and len(clean_number) == 12:
            clean_number = "34" + clean_number[1:]

        return clean_number

    def check_instance_status(self) -> Tuple[bool, str]:
        """
        Verificar el estado de la instancia de Green-API
        """
        if self.simulate_mode:
            return True, "Modo simulación activo"

        try:
            if not self.api_url or not self.api_token or not self.instance_id:
                return False, "Configuración incompleta: falta URL, token o ID de instancia"

            url = f"{self.api_url}/waInstance{self.instance_id}/getStateInstance/{self.api_token}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                state = data.get("stateInstance", "unknown")
                if state == "authorized":
                    return True, "Instancia autorizada y lista"
                return False, f"Estado de instancia: {state}"

            return False, f"Error HTTP {response.status_code}"

        except Exception as e:
            return False, f"Error de conexión: {str(e)}"

    def send_bulk_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Enviar múltiples mensajes
        """
        results = []

        for msg_data in messages:
            phone = msg_data["phone"]
            message = msg_data["message"]

            success, error = self.send_message(phone, message)

            results.append(
                {
                    "phone": phone,
                    "success": success,
                    "error": error,
                }
            )

        return results

    def _update_simulation_mode(self):
        """
        Actualiza si se debe operar en modo simulación.
        """
        self.simulate_mode = not (
            self.api_url and self.api_token and self.instance_id
        )


# Instancia global para usar en la aplicación
_default_config = _load_default_config()
green_api_sender = GreenAPISender(
    api_url=_default_config.get("api_url"),
    api_token=_default_config.get("api_token"),
    instance_id=_default_config.get("instance_id"),
    phone=_default_config.get("phone"),
)


def enviar_whatsapp(telefono: str, mensaje: str) -> bool:
    """
    Función de conveniencia para enviar WhatsApp
    Mantiene compatibilidad con el código existente
    """
    success, _ = green_api_sender.send_message(telefono, mensaje)
    return success


def configurar_green_api(
    api_url: str,
    api_token: str,
    instance_id: Optional[str] = None,
    phone: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Configurar el sender para usar Green-API real
    """
    global green_api_sender

    green_api_sender.api_url = api_url
    green_api_sender.api_token = api_token
    if instance_id:
        green_api_sender.instance_id = instance_id
    if phone:
        green_api_sender.phone = phone
    green_api_sender._update_simulation_mode()

    logger.info("Green-API configurado para envío real")

    conectado, mensaje = green_api_sender.check_instance_status()
    if conectado:
        logger.info(f"✓ Green-API conectado: {mensaje}")
    else:
        logger.warning(f"⚠ Green-API no conectado: {mensaje}")

    return conectado, mensaje
