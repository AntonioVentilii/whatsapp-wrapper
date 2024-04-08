import os
import tempfile

BASE_URL = 'https://graph.facebook.com'

LAST_API_VERSION = 'v19.0'

CACHE_DIR = os.path.join(tempfile.gettempdir(), "whatsapp_wrapper_cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
