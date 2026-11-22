"""Frontera de ejecución: captura fallos, registra eventos y permite continuar."""

from dataclasses import dataclass
import logging
from pathlib import Path
import sys

from .modelo import ErrorSoftwareFJ


class ArchivoSeguro(logging.FileHandler):
    """Si falla una escritura posterior, informa por consola sin detener el lote."""

    def handleError(self, record):
        print('No se pudo escribir el log; evento: ' + record.getMessage(), file=sys.stderr)


def configurar_log(ruta='logs/software_fj.log'):
    """Usa UTF-8; si no puede abrir el archivo, registra por consola."""
    logger = logging.getLogger('software_fj.' + str(Path(ruta).resolve()))
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    formato = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    try:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        handler = ArchivoSeguro(ruta, encoding='utf-8')
    except OSError as causa:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formato)
        logger.addHandler(handler)
        logger.error('LOG_NO_DISPONIBLE: %s', causa)
    else:
        # 'else' se ejecuta únicamente cuando la apertura fue exitosa.
        handler.setFormatter(formato)
        logger.addHandler(handler)
        logger.info('LOG_LISTO: %s', ruta)
    return logger


@dataclass(frozen=True)
class Resultado:
    """Permite distinguir un retorno válido de una operación fallida."""

    correcto: bool
    valor: object = None
    error: Exception = None


def ejecutar(etiqueta, operacion, logger):
    """Cada operación tiene su propio try: un fallo no cancela las siguientes.

    Exception se captura solo en esta frontera para registrar fallos inesperados.
    No se captura BaseException: Ctrl+C y la salida del intérprete se respetan.
    """
    logger.info('INICIO | %s', etiqueta)
    try:
        valor = operacion()
    except ErrorSoftwareFJ as error:
        logger.exception('ERROR_CONTROLADO | %s | %s', etiqueta, type(error).__name__)
        return Resultado(False, error=error)
    except Exception as error:
        # Incluye TypeError por parámetros faltantes y fallos no previstos.
        logger.exception('ERROR_INESPERADO | %s | %s', etiqueta, type(error).__name__)
        return Resultado(False, error=error)
    else:
        logger.info('EXITO | %s', etiqueta)
        return Resultado(True, valor=valor)
    finally:
        # Se ejecuta con éxito o error; no cambia estados de negocio ni oculta fallos.
        logger.info('FIN | %s', etiqueta)
