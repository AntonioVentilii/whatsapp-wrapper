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
            'body': message.get('text', {}).get('body'),
            'from': message.get('from'),
            'to': message.get('to'),
            'timestamp': message['timestamp'],
        } for message in messages.values()
        if message.get('type') is not None and message.get('text') is not None
    ]
    return cleaned_messages


def find_message_chain(messages: dict, message_id: str) -> list[dict]:
    """
    Recursively finds a message chain based on message IDs in a context field, starting from the specified message ID.

    Args:
        messages (dict): A dictionary containing all messages.
        message_id (str): The ID of the message from which to start the chain.

    Raises:
        ValueError: If the message ID is not found in the provided messages.

    Returns:
        list[dict]: A list of dictionaries representing the message chain, ordered from the first message to the
            specified one.
    """
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
    """
    Configures and returns a database connection instance based on the provided configuration.

    Args:
        config (DatabaseConfig): A dictionary containing database configuration options.

    Raises:
        ValueError: If neither a credential path nor encoded JSON credentials are provided in the configuration.

    Returns:
        WhatsAppDB: An instance of the WhatsAppDB class configured with the specified options.
    """
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
    """
    A class for interacting with the Firestore database, specifically designed for a WhatsApp-like chat application.

    This class extends FirestoreDB to provide methods tailored to storing, retrieving, and managing chat messages
    and banned user data.
    """

    def __init__(self, credentials_path: str, database: str = None, backup_folder: str = None):
        """
        Initializes a new instance of the WhatsAppDB class.

        Args:
            credentials_path (str): The file path to the Firestore credentials JSON.
            database (str, optional): The name of the Firestore database to use. Defaults to None.
            backup_folder (str, optional): The path to the folder used for backups. Defaults to None.
        """
        super().__init__(credentials_path, database=database, collections=COLLECTIONS, backup_folder=backup_folder)

    def add_chat_message(self, message: dict, wa_id: str) -> str:
        """
         Adds a new chat message to the database under the specified WhatsApp ID.

         Args:
             message (dict): The message data to add.
             wa_id (str): The WhatsApp ID associated with the message.

         Returns:
             str: The ID of the chat document where the message was added.
         """
        message_id = message['id']
        data = {message_id: message}
        chat_id = self.update_document(CHAT_COLLECTION, wa_id, data, create_if_missing=True)
        return chat_id

    def add_banned_user(self, data: dict, user_id: str) -> str:
        """
        Adds a new banned user to the database.

        Args:
            data (dict): The data of the banned user to add.
            user_id (str): The ID of the user to ban.

        Returns:
            str: The token ID of the banned user document.
        """
        token_id = self.add_document(BANNED_USERS_COLLECTION, data, document_name=user_id)
        return token_id

    def update_banned_user(self, user_id: str, data: dict):
        """
        Updates the data for a banned user in the database.

        Args:
            user_id (str): The ID of the user to update.
            data (dict): A dictionary of the data to update for the banned user.
        """
        self.update_document(BANNED_USERS_COLLECTION, user_id, data)

    def delete_chat(self, wa_id: str):
        """
        Deletes a chat document from the database based on the specified WhatsApp ID.

        Args:
            wa_id (str): The WhatsApp ID associated with the chat document to delete.
        """
        self.delete_document(CHAT_COLLECTION, wa_id)

    def delete_banned_user(self, user_id: str):
        """
        Deletes a banned user document from the database based on the specified user ID.

        Args:
            user_id (str): The ID of the banned user to delete.
        """
        self.delete_document(BANNED_USERS_COLLECTION, user_id)

    def get_chat(self, wa_id: str) -> dict:
        """
        Retrieves the chat document associated with the specified WhatsApp ID.

        Args:
            wa_id (str): The WhatsApp ID associated with the chat to retrieve.

        Returns:
            dict: The chat document data.
        """
        return self.get_document_data(CHAT_COLLECTION, wa_id)

    def get_filtered_chat(self, wa_id: str, filters: list[tuple[str, str, str | float]]) -> dict:
        """
        Retrieves and filters a chat document based on specified filters.

        Args:
            wa_id (str): The WhatsApp ID associated with the chat to retrieve and filter.
            filters (list[tuple[str, str, str | float]]): A list of filter tuples where each tuple contains
                a field name, an operator as a string ('==', '!=', '>', '<', '>=', '<='), and a value to compare.

        Returns:
            dict: The filtered chat document data.
        """
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
        """
        Lists the names (document IDs) of all banned users in the database.

        Returns:
            list[str]: A list of banned user names (IDs).
        """
        return self.get_document_names(BANNED_USERS_COLLECTION)

    def list_banned_users(self, with_id: bool = False, as_dict: bool = False) -> list[dict] | dict[str, dict]:
        """
        Retrieves a list or dictionary of all banned users.

        Args:
            with_id (bool, optional): If True, includes the document IDs in the returned data. Defaults to False.
            as_dict (bool, optional): If True, returns the data as a dictionary indexed by user IDs instead of a list.
                Defaults to False.

        Returns:
            list[dict] | dict[str, dict]: The banned users data as a list of dictionaries or a dictionary of
                dictionaries.
        """
        ret = self.get_collection_data(BANNED_USERS_COLLECTION, with_id=with_id)
        if as_dict:
            ret = {x['id']: x for x in ret}
        return ret

    def get_banned_user(self, user_id: str, with_id: bool = False) -> dict:
        """
        Retrieves the data for a banned user based on the specified user ID.

        Args:
            user_id (str): The ID of the banned user to retrieve.
            with_id (bool, optional): If True, includes the document ID in the returned data. Defaults to False.

        Returns:
            dict: The data for the banned user.
        """
        return self.get_document_data(BANNED_USERS_COLLECTION, user_id, with_id=with_id)['access_token']

    def get_conversation_chain(self, wa_id: str, message_id: str) -> list[dict]:
        """
        Retrieves a conversation chain starting from the specified message ID.

        Args:
            wa_id (str): The WhatsApp ID associated with the chat.
            message_id (str): The starting message ID of the conversation chain to retrieve.

        Raises:
            ValueError: If the specified message ID is not found in the chat history.

        Returns:
            list[dict]: A list of message dictionaries representing the conversation chain.
        """
        chat = self.get_chat(wa_id)
        message_ids = list(chat.keys())
        if message_id not in message_ids:
            raise ValueError(f"Message ID {message_id} not found in chat history for {wa_id}")
        chain = find_message_chain(chat, message_id)
        return chain

    def get_conversation_history(self, wa_id: str, since_seconds_ago: int = None) -> list[dict]:
        """
        Retrieves the conversation history for a given WhatsApp ID, optionally filtering by messages since a certain
        time.

        Args:
            wa_id (str): The WhatsApp ID associated with the chat.
            since_seconds_ago (int, optional): The time in seconds to look back from the current time for messages. If
                None, retrieves all messages.

        Returns:
            list[dict]: A list of dictionaries representing the conversation history, sorted by timestamp.
        """
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
        """
        Retrieves a conversation for a given WhatsApp ID. Can operate in two modes: retrieving all messages since a
        given time, or retrieving a specific conversation chain starting from a given message ID.

        Args:
            wa_id (str): The WhatsApp ID associated with the chat.
            since_seconds_ago (int, optional): In non-chain mode, the time in seconds to look back from the current
                time for messages. Defaults to None.
            chain_mode (bool, optional): If True, operates in chain mode to retrieve a conversation chain starting
                from the specified message ID. Defaults to False.
            message_id (str, optional): In chain mode, the starting message ID of the conversation chain to
                retrieve. Defaults to None.

        Raises:
            ValueError: If chain_mode is True and no message_id is provided.

        Returns:
            list[dict]: A list of dictionaries representing the conversation, either as a history or a specific chain.
        """
        if chain_mode:
            if message_id is None:
                raise ValueError("Message ID is required in chain mode")
            chat = self.get_conversation_chain(wa_id, message_id)
        else:
            chat = self.get_conversation_history(wa_id, since_seconds_ago=since_seconds_ago)
        return chat
