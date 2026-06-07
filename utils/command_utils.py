import logging
import re

logger = logging.getLogger("EVA")


def is_conversation_command(text):
    """
    Verifica si el texto es un comando de conversación con EVA.
    Requiere que "eva" sea una palabra completa al inicio del texto.
    """
    return bool(re.match(r"^eva\b", text.strip(), re.IGNORECASE))


def extract_conversation_text(text):
    """
    Extrae el texto de la conversación quitando el comando "eva"
    """
    return re.sub(r"^eva\W*", "", text, flags=re.IGNORECASE).strip()
