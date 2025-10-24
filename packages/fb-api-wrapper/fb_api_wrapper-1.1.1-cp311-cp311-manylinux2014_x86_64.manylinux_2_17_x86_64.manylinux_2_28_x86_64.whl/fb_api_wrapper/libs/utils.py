import random
import string
import base64
from .log_ import logger

def random_cookies(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def encode_base64(input_string):
    try:
        encoded_bytes = base64.b64encode(input_string.encode('utf-8'))
        encoded_string = encoded_bytes.decode('utf-8')
        return encoded_string
    except Exception as e:
        logger.error("Error encoding Base64:", str(e))
        return None