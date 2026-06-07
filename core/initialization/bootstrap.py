import logging
import sys
import traceback
import threading

def setup_logging(log_file):
    """Configura el sistema de logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='w'
    )
    logger = logging.getLogger('EVA')
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def setup_exception_handlers(logger):
    """Configura los manejadores globales de excepciones."""
    def _global_exception_handler(exc_type, exc_value, exc_traceback):
        logger.critical("EXCEPCIÓN NO CAPTURADA", exc_info=(exc_type, exc_value, exc_traceback))
        print("=" * 80, flush=True)
        print("EXCEPCIÓN NO CAPTURADA - EVA SE CERRARÁ", flush=True)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("=" * 80, flush=True)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def _thread_exception_handler(args):
        logger.critical(f"EXCEPCIÓN EN HILO {args.thread.name}", exc_info=args.exc_info)
        print(f"EXCEPCIÓN EN HILO {args.thread.name}", flush=True)
        traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = _global_exception_handler
    threading.excepthook = _thread_exception_handler
