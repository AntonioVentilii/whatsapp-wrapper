from __future__ import annotations

import base64
import os
import time
from typing import Optional, TypedDict

from firestore_wrapper import FirestoreDB

from .configs import CACHE_DIR


class DatabaseConfig(TypedDict, total=False):
    credential_path: Optional[str]
    credential_encoded_json: Optional[str]
    database: Optional[str]
    backup_folder: Optional[str]


CHAT_COLLECTION = 'chats'
BANNED_USERS_COLLECTION = 'banned_users'
COLLECTIONS = [
    CHAT_COLLECTION,
    BANNED_USERS_COLLECTION,
]


def encoded_credentials_to_json(encoded_str: str) -> str:
    json_data = base64.b64decode(encoded_str).decode('utf-8')
    file = os.path.join(CACHE_DIR, 'firestore_credentials.json')
    with open(file, 'w') as json_file:
        json_file.write(json_data)
    return file


def json_to_encoded_credentials(file: str) -> str:
    if os.path.exists(file):
        with open(file, 'r') as json_file:
            json_data = json_file.read()
        encoded_json = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
    else:
        raise ValueError(f'Credentials file {file} not found')
    return encoded_json


def clean_chat_data(messages: dict) -> list[dict]:
    cleaned_messages = [
        {
            'body': message['text']['body'],
            'from': message.get('from'),
            'to': message.get('to'),
            'timestamp': message['timestamp'],
        } for message in messages.values() if message.get('type') == 'text'
    ]
    return cleaned_messages


def find_message_chain(messages: dict, message_id: str) -> list[dict]:
    if message_id not in messages:
        return []

    message = messages[message_id]

    if message.get('type') != 'text':
        return []

    message_info = {
        'body': message['text']['body'],
        'from': message.get('from'),
        'to': message.get('to'),
        'timestamp': message['timestamp'],
    }

    result = [message_info]

    if 'context' in message:
        context = message['context']
        next_message_id = context.get('id', context.get('message_id'))
        if message_id is None:
            raise ValueError(f"Message ID not found in context for message {message_id}")
        previous_messages = find_message_chain(messages, next_message_id)
        result = previous_messages + result

    return result


def configure_database(config: DatabaseConfig) -> WhatsAppDB:
    credential_path = config.get('credential_path')
    credential_encoded_json = config.get('credential_encoded_json')
    if credential_path is None and credential_encoded_json is None:
        raise ValueError("Database configuration requires either a credential path or encoded JSON.")
    if credential_path and credential_encoded_json:
        print("Both credential path and encoded JSON are provided. Using credential path.")
    credential_path = credential_path or encoded_credentials_to_json(credential_encoded_json)
    database = config.get('database')
    backup_folder = config.get('backup_folder')
    db = WhatsAppDB(credentials_path=credential_path, database=database, backup_folder=backup_folder)
    return db


class WhatsAppDB(FirestoreDB):

    def __init__(self, credentials_path: str, database: str = None, backup_folder: str = None):
        super().__init__(credentials_path, database=database, collections=COLLECTIONS, backup_folder=backup_folder)

    def add_chat_message(self, message: dict, wa_id: str) -> str:
        message_id = message['id']
        data = {message_id: message}
        chat_id = self.update_document(CHAT_COLLECTION, wa_id, data, create_if_missing=True)
        return chat_id

    def add_banned_user(self, data: dict, user_id: str) -> str:
        token_id = self.add_document(BANNED_USERS_COLLECTION, data, document_name=user_id)
        return token_id

    def update_banned_user(self, user_id: str, data: dict):
        self.update_document(BANNED_USERS_COLLECTION, user_id, data)

    def delete_chat(self, wa_id: str):
        self.delete_document(CHAT_COLLECTION, wa_id)

    def delete_banned_user(self, user_id: str):
        self.delete_document(BANNED_USERS_COLLECTION, user_id)

    def get_chat(self, wa_id: str) -> dict:
        return self.get_document_data(CHAT_COLLECTION, wa_id)

    def get_filtered_chat(self, wa_id: str, filters: list[tuple[str, str, str | float]]) -> dict:
        chat = self.get_chat(wa_id)
        filtered_chat = {}
        for message_id, message in chat.items():
            for field, operator, value in filters:
                if field not in message:
                    continue
                message_value = message[field]
                if isinstance(value, float) and not isinstance(message_value, float):
                    try:
                        message_value = float(message_value)
                    except ValueError:
                        continue
                if isinstance(message_value, float) and not isinstance(value, float):
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                if operator == '==' and message_value == value:
                    filtered_chat[message_id] = message
                elif operator == '!=' and message_value != value:
                    filtered_chat[message_id] = message
                elif operator == '>' and message_value > value:
                    filtered_chat[message_id] = message
                elif operator == '<' and message_value < value:
                    filtered_chat[message_id] = message
                elif operator == '>=' and message_value >= value:
                    filtered_chat[message_id] = message
                elif operator == '<=' and message_value <= value:
                    filtered_chat[message_id] = message
        return filtered_chat

    def list_banned_user_names(self) -> list[str]:
        return self.get_document_names(BANNED_USERS_COLLECTION)

    def list_banned_users(self, with_id: bool = False, as_dict: bool = False) -> list[dict] | dict[str, dict]:
        ret = self.get_collection_data(BANNED_USERS_COLLECTION, with_id=with_id)
        if as_dict:
            ret = {x['id']: x for x in ret}
        return ret

    def get_banned_user(self, user_id: str, with_id: bool = False) -> dict:
        return self.get_document_data(BANNED_USERS_COLLECTION, user_id, with_id=with_id)['access_token']

    def get_conversation_chain(self, wa_id: str, message_id: str) -> list[dict]:
        chat = self.get_chat(wa_id)
        message_ids = list(chat.keys())
        if message_id not in message_ids:
            raise ValueError(f"Message ID {message_id} not found in chat history for {wa_id}")
        chain = find_message_chain(chat, message_id)
        return chain

    def get_conversation_history(self, wa_id: str, since_seconds_ago: int = None) -> list[dict]:
        if since_seconds_ago is not None and since_seconds_ago > 0:
            start_time = time.time() - since_seconds_ago
            chat = self.get_filtered_chat(wa_id, [('timestamp', '>=', start_time)])
        else:
            chat = self.get_chat(wa_id)
        # TODO: remove the cleanup part to accept all messages
        cleaned_chat = clean_chat_data(chat)
        chat_as_list = cleaned_chat  # list(chat.values())
        sorted_chat = sorted(chat_as_list, key=lambda x: int(x['timestamp']))
        return sorted_chat

    def get_conversation(self, wa_id: str, since_seconds_ago: int = None, chain_mode: bool = False,
                         message_id: str = None) -> list[dict]:
        if chain_mode:
            if message_id is None:
                raise ValueError("Message ID is required in chain mode")
            chat = self.get_conversation_chain(wa_id, message_id)
        else:
            chat = self.get_conversation_history(wa_id, since_seconds_ago=since_seconds_ago)
        return chat
