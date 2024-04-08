# whatsapp-wrapper

Integration layer for WhatsApp Cloud API with Firestore for easy message storage and management.

# WhatsApp Cloud API Python Package

The WhatsAppAPI Python package provides a comprehensive and easy-to-use interface for interacting with WhatsApp's API.
This package enables developers to integrate WhatsApp messaging capabilities into their applications effortlessly.
From sending texts, images, videos, and documents to handling media files and managing message databases, this package
covers a wide range of functionalities to enhance communication solutions.

## Some Features

- **Send Messages**: Send text messages, images, videos, documents, audio, and stickers.
- **Media Management**: Upload and retrieve media files with support for temporary file caching.
- **Database Integration**: Optional [Firestore](https://firebase.google.com/docs/firestore) database integration to
  save chats and messages.
- **Custom Error Handling**: Implement custom error handling for robust application performance.
- **Message Replies**: Reply to messages to maintain context in conversations.
- **URL Previews**: Generate previews for URLs in text messages.
- **Message Reactions**: Add emoji reactions to messages.

## Installation

To install WhatsAppAPI, use pip:

```bash
pip install whatsappapi
```

## Quick Start

### Setting Up

To get started, import the `WhatsAppAPI` class from the package and configure it with your mobile ID and API token.

```python
from whatsapp_wrapper import WhatsAppAPI

api = WhatsAppAPI(mobile_id='your_mobile_id', api_token='your_api_token')
```

### Sending a Text Message

Sending a text message is straightforward:

```python
api.send_text(to='recipient_number', message='Hello, World!')
```

### Sending an Image

To send an image:

```python
api.send_image(to='recipient_number', image_id_or_url='image_url', caption='Check this out!')
```

### Saving Messages to Database

If you want to save messages to a [Firestore database](https://firebase.google.com/docs/firestore), you need to provide
a `DatabaseConfig` during initialization:

```python
from whatsapp_wrapper.whatsapp_db import DatabaseConfig

db_config: DatabaseConfig = {
    'credential_path': 'path/to/your/firestore/credential.json',
    'backup_folder': 'path/to/backup/folder'
}

api = WhatsAppAPI(mobile_id='your_mobile_id', api_token='your_api_token', database_config=db_config)
```

Messages will then be automatically saved to the database.

## Handling Errors

You can provide a custom error handler function during initialization to handle API errors according to your
application's requirements.

```python
def custom_error_handler(response, data):
    # Custom error handling logic
    pass


api = WhatsAppAPI(mobile_id='your_mobile_id', api_token='your_api_token', error_handler=custom_error_handler)
```

## References

### WhatsApp Documentation

- [API Endpoint References](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)
    - [Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages)
- [API Error Codes](https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes)

### Graph API Documentation

- [WhatsApp Business Account](https://developers.facebook.com/docs/graph-api/reference/whats-app-business-account/)

## Support and Contributions

For support, please open an issue on the project's GitHub page.
Contributions are welcome!
If you'd like to contribute,
please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
