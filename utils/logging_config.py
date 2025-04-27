import logging
import sys


# Configuración básica de logging
def setup_logging():
    """
    Configura el logging para capturar excepciones, mostrar en consola,
    y levantar las excepciones nuevamente si es necesario.
    """
    # Logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # StreamHandler para mostrar los logs en la consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter y asociación al handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Handler y asociación al logger
    logger.addHandler(console_handler)

    # Configuración del logger para capturar las excepciones y mostrarlas
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Manejo de excepciones
    def exception_handler(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        # Levantar la excepción nuevamente para seguir con el flujo de ejecución
        raise exc_value  # Aquí levantamos la excepción para continuar el flujo

    sys.excepthook = exception_handler
