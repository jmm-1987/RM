"""
Módulo para el envío de mensajes de WhatsApp usando Twilio
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

from twilio.rest import Client
from twilio.base.exceptions import TwilioException, TwilioRestException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_default_config() -> Dict[str, Optional[str]]:
    """
    Cargar configuración de Twilio desde variables de entorno o archivos locales.
    """
    config = {
        "account_sid": os.environ.get("TWILIO_ACCOUNT_SID"),
        "auth_token": os.environ.get("TWILIO_AUTH_TOKEN"),
        "whatsapp_number": os.environ.get("TWILIO_WHATSAPP_NUMBER"),
    }

    if all(config.values()):
        return config

    # Intentar cargar desde archivo config si existe
    try:
        from config import (
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_WHATSAPP_NUMBER,
        )

        config.setdefault("account_sid", TWILIO_ACCOUNT_SID)
        config.setdefault("auth_token", TWILIO_AUTH_TOKEN)
        config.setdefault("whatsapp_number", TWILIO_WHATSAPP_NUMBER)
    except ImportError:
        pass

    return config


class TwilioSender:
    """
    Clase para manejar el envío de mensajes de WhatsApp usando Twilio
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        whatsapp_number: Optional[str] = None,
    ):
        """
        Inicializar el sender de Twilio

        Args:
            account_sid: Account SID de Twilio
            auth_token: Auth Token de Twilio
            whatsapp_number: Número de WhatsApp Business (formato: whatsapp:+34612345678)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.whatsapp_number = whatsapp_number
        self._client = None
        self._update_simulation_mode()

        if not self.simulate_mode:
            try:
                self._client = Client(account_sid, auth_token)
                logger.info("Twilio configurado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente Twilio: {e}")
                self.simulate_mode = True

    def send_message(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Enviar un mensaje de WhatsApp usando Twilio
        """
        if self.simulate_mode:
            return self._simulate_send(phone_number, message)
        return self._twilio_send(phone_number, message)

    def send_image(self, phone_number: str, image_url: str, caption: str = "") -> Tuple[bool, str]:
        """
        Enviar una imagen de WhatsApp usando Twilio
        Nota: Twilio requiere que la imagen esté en una URL pública
        """
        if self.simulate_mode:
            return self._simulate_send_image(phone_number, image_url, caption)
        return self._twilio_send_media(phone_number, image_url, caption, media_type="image")

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

    def _simulate_send_image(self, phone_number: str, image_url: str, caption: str) -> Tuple[bool, str]:
        """
        Simular envío de imagen (para desarrollo/testing)
        """
        logger.info(f"SIMULANDO envío de imagen a {phone_number}: {image_url}")

        # Simular éxito/error aleatorio para testing
        import random

        success = random.random() > 0.1  # 90% de éxito

        if success:
            logger.info(f"✓ Imagen enviada exitosamente a {phone_number}")
            return True, ""

        error_msg = "Error simulado en el envío de imagen"
        logger.error(f"✗ Error enviando imagen a {phone_number}: {error_msg}")
        return False, error_msg

    def _twilio_send(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Envío real usando Twilio
        """
        try:
            if not self._client:
                error_msg = "Cliente Twilio no inicializado"
                logger.error(error_msg)
                return False, error_msg
            
            if not self.whatsapp_number:
                error_msg = "Número de WhatsApp no configurado. Configura TWILIO_WHATSAPP_NUMBER (formato: whatsapp:+34612345678)"
                logger.error(error_msg)
                return False, error_msg

            # Verificar formato del número From
            if not self.whatsapp_number.startswith('whatsapp:'):
                error_msg = f"Formato incorrecto del número From. Debe empezar con 'whatsapp:'. Actual: {self.whatsapp_number}. Ejemplo correcto: whatsapp:+34612345678"
                logger.error(error_msg)
                return False, error_msg

            # Formatear número de teléfono para Twilio (formato: whatsapp:+34612345678)
            formatted_number = self._format_phone_number(phone_number)

            logger.info(f"Enviando mensaje desde {self.whatsapp_number} a {formatted_number}")

            # Enviar mensaje usando Twilio
            message_obj = self._client.messages.create(
                body=message,
                from_=self.whatsapp_number,  # Formato: whatsapp:+34612345678
                to=formatted_number,  # Formato: whatsapp:+34612345678
            )

            logger.info(f"✓ Mensaje enviado exitosamente a {phone_number}. SID: {message_obj.sid}")
            return True, message_obj.sid

        except TwilioRestException as e:
            error_msg = f"Error Twilio {e.code}: {e.msg}"
            logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
            
            # Mensajes de error más descriptivos
            if e.code == 63007:
                error_msg = f"Error 63007: El número 'From' ({self.whatsapp_number}) no está configurado o no existe en tu cuenta de Twilio. Verifica que el número esté correctamente configurado en el panel de Twilio y que uses el formato correcto (whatsapp:+34612345678). Si usas Sandbox, el número debe ser whatsapp:+14155238886"
            elif e.code == 21211:
                error_msg = f"Error 21211: Número de destino inválido ({formatted_number}). Verifica el formato del número."
            elif e.code == 21608:
                error_msg = f"Error 21608: No tienes permiso para enviar a este número. Si usas Sandbox, asegúrate de que el número esté verificado."
            
            return False, error_msg
        except TwilioException as e:
            error_msg = f"Error de conexión Twilio: {str(e)}"
            logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"✗ Error enviando a {phone_number}: {error_msg}")
            return False, error_msg

    def _twilio_send_media(self, phone_number: str, media_url: str, caption: str = "", media_type: str = "image") -> Tuple[bool, str]:
        """
        Envío real de media usando Twilio
        """
        try:
            if not self._client or not self.whatsapp_number:
                error_msg = "Twilio no está configurado correctamente"
                logger.error(error_msg)
                return False, error_msg

            formatted_number = self._format_phone_number(phone_number)

            # Construir el mensaje con media
            body = caption if caption else ""
            
            message_obj = self._client.messages.create(
                body=body,
                media_url=[media_url],  # Twilio acepta lista de URLs
                from_=self.whatsapp_number,
                to=formatted_number,
            )

            logger.info(f"✓ {media_type.capitalize()} enviado exitosamente a {phone_number}. SID: {message_obj.sid}")
            return True, message_obj.sid

        except TwilioRestException as e:
            error_msg = f"Error Twilio {e.code}: {e.msg}"
            logger.error(f"✗ Error enviando {media_type} a {phone_number}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"✗ Error enviando {media_type} a {phone_number}: {error_msg}")
            return False, error_msg

    def _format_phone_number(self, phone_number: str) -> str:
        """
        Formatear número de teléfono para Twilio (formato: whatsapp:+34612345678)
        """
        # Limpiar número (solo dígitos)
        clean_number = "".join(filter(str.isdigit, phone_number))

        # Agregar código de país si es necesario
        if clean_number.startswith("6") and len(clean_number) == 9:
            clean_number = "34" + clean_number
        elif clean_number.startswith("600") and len(clean_number) == 12:
            clean_number = "34" + clean_number[1:]

        # Formato Twilio: whatsapp:+34612345678
        return f"whatsapp:+{clean_number}"

    def check_account_status(self) -> Tuple[bool, str]:
        """
        Verificar el estado de la cuenta de Twilio
        """
        if self.simulate_mode:
            return True, "Modo simulación activo"

        try:
            if not self._client:
                return False, "Cliente Twilio no inicializado"

            # Intentar obtener información de la cuenta
            account = self._client.api.accounts(self.account_sid).fetch()
            
            if account.status == "active":
                return True, f"Cuenta activa: {account.friendly_name}"
            return False, f"Estado de cuenta: {account.status}"

        except TwilioRestException as e:
            return False, f"Error verificando cuenta: {e.msg}"
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
            self.account_sid and self.auth_token and self.whatsapp_number
        )


# Instancia global para usar en la aplicación
_default_config = _load_default_config()
twilio_sender = TwilioSender(
    account_sid=_default_config.get("account_sid"),
    auth_token=_default_config.get("auth_token"),
    whatsapp_number=_default_config.get("whatsapp_number"),
)


def enviar_whatsapp(telefono: str, mensaje: str) -> bool:
    """
    Función de conveniencia para enviar WhatsApp
    Mantiene compatibilidad con el código existente
    """
    success, _ = twilio_sender.send_message(telefono, mensaje)
    return success


def configurar_twilio(
    account_sid: str,
    auth_token: str,
    whatsapp_number: str,
) -> Tuple[bool, str]:
    """
    Configurar el sender para usar Twilio real
    """
    global twilio_sender

    twilio_sender.account_sid = account_sid
    twilio_sender.auth_token = auth_token
    twilio_sender.whatsapp_number = whatsapp_number
    twilio_sender._update_simulation_mode()

    logger.info("Twilio configurado para envío real")

    # Reinicializar cliente
    try:
        twilio_sender._client = Client(account_sid, auth_token)
    except Exception as e:
        logger.error(f"Error inicializando cliente Twilio: {e}")
        return False, f"Error inicializando cliente: {str(e)}"

    conectado, mensaje = twilio_sender.check_account_status()
    if conectado:
        logger.info(f"✓ Twilio conectado: {mensaje}")
    else:
        logger.warning(f"⚠ Twilio no conectado: {mensaje}")

    return conectado, mensaje

