import os
import tempfile

BASE_URL = 'https://graph.facebook.com'

LAST_API_VERSION = 'v19.0'

"""
When CONTEXT_AS_CHAIN is True, the user needs to reply to the last message in the conversation chain of answer and 
replies, in order to continue the conversation. If the user sends a new message without replying, the conversation 
chain will be reset.
When CONTEXT_AS_CHAIN is False and CONTEXT_HISTORY_DURATION is a positive non-null number, the bot considers the entire
conversation history as context for generating a reply, starting from the message that was CONTEXT_HISTORY_DURATION 
seconds ago.
In all other cases, the bot will generate a reply without any context.
"""
CONTEXT_AS_CHAIN = True
CONTEXT_HISTORY_DURATION = 24 * 60 * 60  # 24 hours

CACHE_DIR = os.path.join(tempfile.gettempdir(), "whatsapp_wrapper_cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
