import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MenuAPIService:
    """
    Servicio para integración con el módulo de Menú (M1)
    """
    def __init__(self):
        # URL base del módulo M1 - configurar en settings.py
        self.base_url = getattr(settings, 'MENU_API_URL', 'http://localhost:8001/api')
        self.timeout = 10  # Timeout en segundos
    
    def validar_stock(self, platos):
        """
        Valida y reserva temporalmente el stock de platos
        
        Args:
            platos: Lista de diccionarios con estructura:
                    [{'plato_id': 1, 'cantidad': 2}, ...]
        
        Returns:
            dict: {'success': bool, 'message': str, 'data': dict}
        """
        url = f"{self.base_url}/stock/validar"
        
        payload = {
            'platos': platos
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Stock validado correctamente: {data}")
                return {
                    'success': True,
                    'message': 'Stock validado y reservado temporalmente',
                    'data': data
                }
            else:
                error_msg = response.json().get('message', 'Error desconocido')
                logger.error(f"Error al validar stock: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'data': None
                }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con M1")
            return {
                'success': False,
                'message': 'Tiempo de espera agotado al conectar con el sistema de menú',
                'data': None
            }
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con M1")
            return {
                'success': False,
                'message': 'No se pudo conectar con el sistema de menú',
                'data': None
            }
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': None
            }
    
    def consumir_stock(self, pedido_id, platos):
        """
        Consume definitivamente el stock de platos
        
        Args:
            pedido_id: ID del pedido
            platos: Lista de diccionarios con estructura:
                    [{'plato_id': 1, 'cantidad': 2}, ...]
        
        Returns:
            dict: {'success': bool, 'message': str, 'data': dict}
        """
        url = f"{self.base_url}/stock/consumir"
        
        payload = {
            'pedido_id': pedido_id,
            'platos': platos
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Stock consumido correctamente para pedido {pedido_id}")
                return {
                    'success': True,
                    'message': 'Stock consumido correctamente',
                    'data': data
                }
            else:
                error_msg = response.json().get('message', 'Error desconocido')
                logger.error(f"Error al consumir stock: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'data': None
                }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con M1")
            return {
                'success': False,
                'message': 'Tiempo de espera agotado al conectar con el sistema de menú',
                'data': None
            }
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con M1")
            return {
                'success': False,
                'message': 'No se pudo conectar con el sistema de menú',
                'data': None
            }
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': None
            }
    
    def cancelar_reserva(self, platos):
        """
        Cancela una reserva temporal de stock
        
        Args:
            platos: Lista de diccionarios con estructura:
                    [{'plato_id': 1, 'cantidad': 2}, ...]
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        url = f"{self.base_url}/stock/cancelar-reserva"
        
        payload = {
            'platos': platos
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Reserva cancelada correctamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al cancelar reserva'
                }
                
        except Exception as e:
            logger.error(f"Error al cancelar reserva: {str(e)}")
            return {
                'success': False,
                'message': f'Error al cancelar reserva: {str(e)}'
            }