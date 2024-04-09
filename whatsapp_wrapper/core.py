from __future__ import annotations

import time
import warnings

import requests
from requests import Response

from .configs import BASE_URL, LAST_API_VERSION
from .exceptions import WhatsAppAPIWarning
from .media_utilities import check_media_type_supported, save_media_to_temp_cache
from .message_object import MessageObject
from .whatsapp_db import DatabaseConfig, WhatsAppDB, configure_database


def _default_error_handler(_, response: Response, data: dict):
    status_code = response.status_code
    error_message = (
        f"Request was failed with status code: {status_code}."
        f" Data: {data}"
    )
    raise Exception(error_message)


class WhatsAppAPI:
    BASE_URL = BASE_URL
    DEFAULT_API_VERSION = LAST_API_VERSION

    _MESSAGE_URI = 'messages'
    _MEDIA_URI = 'media'

    def __init__(self, mobile_id: str, api_token: str, version: str = LAST_API_VERSION,
                 database_config: DatabaseConfig = None, error_handler=None):
        self.mobile_id = mobile_id
        self.bearer_token = api_token
        self.version = version or self.DEFAULT_API_VERSION
        if database_config is None:
            self._db = None
            txt = "Database configuration is not provided. Chats will not be saved."
            warnings.warn(txt, WhatsAppAPIWarning)
        else:
            self._db = configure_database(database_config)
        self.error_handler = self._custom_error_handler_factory(error_handler or _default_error_handler)
        self._banned_users = []

    def _custom_error_handler_factory(self, external_error_handler):
        """Bind an external error handler to the current instance."""

        def error_handler(response: Response, data: dict):
            # Call the external error handler with self as the first argument
            external_error_handler(self, response, data)

        return error_handler

    @property
    def db(self) -> WhatsAppDB:
        return self._db

    @property
    def banned_users(self) -> list[str]:
        if self.db:
            db_banned_users = self.db.list_banned_user_names()
        else:
            db_banned_users = []
        ret = self._banned_users + db_banned_users
        ret = list(set(ret))
        return ret

    @banned_users.setter
    def banned_users(self, value: list[str]):
        self._banned_users = value

    @property
    def base_url(self):
        return f'{self.BASE_URL}/{self.version}'

    @property
    def mobile_url(self):
        return f'{self.base_url}/{self.mobile_id}'

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.bearer_token}'}

    def request(self, method: str, uri: str, params: dict = None, data: dict = None, base_url: str = None,
                headers: dict = None) -> Response:
        method = method.upper()
        if method not in ['GET', 'POST']:
            raise ValueError(f"Invalid method: {method}")
        elif method == 'GET':
            if data:
                raise ValueError(f"Data is not allowed for GET requests")
        elif method == 'POST':
            if params:
                raise ValueError(f"Params is not allowed for POST requests")
            if not data:
                raise ValueError(f"Data is required for POST requests")

        base_url = base_url or self.base_url
        url = f"{base_url}/{uri}"
        headers = headers or self.headers

        if method == 'GET':
            r = requests.request(method, url, headers=headers, params=params)
        else:
            r = requests.request(method, url, headers=headers, json=data)

        if r.status_code != 200:
            r = self.error_handler(r, data)

        return r

    def get_request(self, uri: str, params: dict = None, base_url: str = None, headers: dict = None):
        return self.request('GET', uri=uri, params=params, base_url=base_url, headers=headers)

    def post_request(self, uri: str, data: dict = None, base_url: str = None, headers: dict = None):
        return self.request('POST', uri=uri, data=data, base_url=base_url, headers=headers)

    def get_media_details(self, media_id: str) -> dict:
        r = self.get_request(media_id)
        ret = r.json()
        return ret

    def get_media_data(self, media_url: str) -> bytes:
        r = requests.get(media_url, headers=self.headers)
        if r.status_code != 200:
            raise Exception(f"Failed to get media data! Status code: {r.status_code} - Reason: {r.reason}")
        ret = r.content
        return ret

    def get_media_file(self, media_url: str, mime_type: str) -> str:
        check_media_type_supported(mime_type, raise_error=True)
        media = self.get_media_data(media_url)
        file = save_media_to_temp_cache(mime_type, media)
        return file

    def get_media(self, media_id: str) -> str:
        metadata = self.get_media_details(media_id)
        url = metadata['url']
        mime_type = metadata['mime_type']
        file = self.get_media_file(url, mime_type)
        return file

    def save_message_to_db(self, data: dict, wa_id: str):
        if self.db is None:
            txt = f"Database configuration is not provided. Message {data} will not be saved."
            warnings.warn(txt, WhatsAppAPIWarning)
        else:
            self.db.add_chat_message(data, wa_id)

    def _send_message(self, data: dict, save_to_db: bool = True) -> dict:
        base_url = self.mobile_url
        uri = self._MESSAGE_URI
        r = self.post_request(uri, data=data, base_url=base_url)
        ret = r.json()
        ret['data'] = data
        if save_to_db:
            ret['data']['id'] = ret['messages'][0]['id']
            ret['data']['timestamp'] = time.time()
            self.save_message_to_db(ret['data'], data['to'])
        return ret

    def mark_as_read(self, message_id: str) -> dict:
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        ret = self._send_message(data, save_to_db=False)
        return ret

    def send_text(self, to: str, message: str, preview_url: bool = False,
                  reply_to_message_id: str = None, save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.text(message, preview_url=preview_url)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret

    def send_reaction(self, to: str, reply_to_message_id: str, emoji: str, save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.reaction(emoji)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret

    def send_audio(self, to: str, audio_id_or_url: str, reply_to_message_id: str = None,
                   save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.audio(audio_id_or_url)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret

    def send_document(self, to: str, document_id_or_url: str, caption: str = None, filename: str = None,
                      reply_to_message_id: str = None, save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.document(document_id_or_url, caption=caption, filename=filename)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret

    def send_image(self, to: str, image_id_or_url: str, caption: str = None, reply_to_message_id: str = None,
                   save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.image(image_id_or_url, caption=caption)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret

    def send_sticker(self, to: str, sticker_id_or_url: str, reply_to_message_id: str = None,
                     save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.sticker(sticker_id_or_url)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret

    def send_video(self, to: str, video_id_or_url: str, caption: str = None, reply_to_message_id: str = None,
                   save_to_db: bool = True) -> dict:
        message_obj = MessageObject(to, reply_to_message_id=reply_to_message_id)
        payload = message_obj.video(video_id_or_url, caption=caption)
        ret = self._send_message(payload, save_to_db=save_to_db)
        return ret
