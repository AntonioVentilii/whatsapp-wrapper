from __future__ import annotations


class MessageObject:
    """
    A class to construct message objects for sending via the WhatsApp Cloud API.

    Attributes:
        to (str): The recipient's identifier.
        reply_to_message_id (str, optional): The ID of the message to reply to. Default is None.
        messaging_product (str, optional): The messaging product, default is 'whatsapp'.

    Methods:
        base_data: Returns the base data structure for a message.
        text: Constructs a text message payload.
        reaction: Constructs a reaction message payload.
        audio: Constructs an audio message payload.
        document: Constructs a document message payload.
        image: Constructs an image message payload.
        sticker: Constructs a sticker message payload.
        video: Constructs a video message payload.
        location: Constructs a location message payload.
        contacts: Constructs a contacts message payload (not implemented).
        interactive: Constructs an interactive message payload (not implemented).
        template: Constructs a template message payload (not implemented).
    """

    def __init__(self, to: str, reply_to_message_id: str = None, messaging_product: str = 'whatsapp'):
        """
        Initializes the MessageObject with recipient information and optional reply context.

        Parameters:
            to (str): The recipient's phone number ID.
            reply_to_message_id (str, optional): ID of the message being replied to.
            messaging_product (str, optional): The messaging product, default is 'whatsapp'.
        """
        self.to = to
        self.reply_to_message_id = reply_to_message_id
        self.messaging_product = messaging_product
        self.recipient_type = 'individual'

    @property
    def base_data(self):
        """
        Constructs the base data structure common to all messages.

        Returns:
            dict: The base data structure for a message.
        """
        data = {
            'to': str(self.to),
            'messaging_product': self.messaging_product,
            'recipient_type': self.recipient_type,
            'context': {
                'message_id': self.reply_to_message_id
            }
        }
        return data

    def text(self, text: str, preview_url: bool = True) -> dict:
        """
        Constructs a payload for sending a text message.

        Parameters:
            text (str): The message body.
            preview_url (bool, optional): Whether to preview URLs in the message. Defaults to True.

        Returns:
            dict: The payload for a text message.
        """
        data = self.base_data
        data['type'] = 'text'
        data['text'] = {
            'preview_url': preview_url,
            'body': text
        }
        return data

    def reaction(self, emoji: str) -> dict:
        """
        Constructs a payload for sending a reaction to a message.

        Parameters:
            emoji (str): The emoji used for the reaction.

        Returns:
            dict: The payload for a reaction message.

        Raises:
            ValueError: If `reply_to_message_id` is None, as it's required for reaction messages.
        """
        if self.reply_to_message_id is None:
            raise ValueError('reply_to_message_id is required for reaction message type.')
        data = self.base_data
        data.pop('context')
        data['type'] = 'reaction'
        data['reaction'] = {
            'message_id': self.reply_to_message_id,
            'emoji': emoji
        }
        return data

    def _media(self, media_type: str, media_id_or_url: str, caption: str = None, filename: str = None) -> dict:
        """
        Internal method to construct a payload for sending a media message.

        Parameters:
            media_type (str): The type of media (audio, document, image, sticker, video).
            media_id_or_url (str): The ID or URL of the media.
            caption (str, optional): The caption for the media. Default is None.
            filename (str, optional): The filename for the media. Default is None.

        Returns:
            dict: The payload for a media message.
        """
        data = self.base_data
        handle_type = 'link' if 'https' in media_id_or_url else 'id'
        data['type'] = media_type
        data[media_type] = {
            handle_type: media_id_or_url
        }
        if caption:
            data['image']['caption'] = caption
        if filename:
            data['image']['filename'] = filename
        return data

    def audio(self, audio_id_or_url: str) -> dict:
        """
        Constructs a payload for sending an audio message.

        Parameters:
            audio_id_or_url (str): The ID or URL of the audio to send.

        Returns:
            dict: The payload for an audio message.
        """
        data = self._media('audio', audio_id_or_url)
        return data

    def document(self, document_id_or_url: str, caption: str = None, filename: str = None) -> dict:
        """
        Constructs a payload for sending a document message.

        Parameters:
            document_id_or_url (str): The ID or URL of the document to send.
            caption (str, optional): The caption for the document. Default is None.
            filename (str, optional): The filename for the document. Default is None.

        Returns:
            dict: The payload for a document message.
        """
        data = self._media('document', document_id_or_url, caption, filename)
        return data

    def image(self, image_id_or_url: str, caption: str = None) -> dict:
        """
        Constructs a payload for sending an image message.

        Parameters:
            image_id_or_url (str): The ID or URL of the image to send.
            caption (str, optional): The caption for the image. Default is None.

        Returns:
            dict: The payload for an image message.
        """
        data = self._media('image', image_id_or_url, caption)
        return data

    def sticker(self, sticker_id_or_url: str) -> dict:
        """
        Constructs a payload for sending a sticker message.

        Parameters:
            sticker_id_or_url (str): The ID or URL of the sticker to send.

        Returns:
            dict: The payload for a sticker message.
        """
        data = self._media('sticker', sticker_id_or_url)
        return data

    def video(self, video_id_or_url: str, caption: str = None) -> dict:
        """
        Constructs a payload for sending a video message.

        Parameters:
            video_id_or_url (str): The ID or URL of the video to send.
            caption (str, optional): The caption for the video. Default is None.

        Returns:
            dict: The payload for a video message.
        """
        data = self._media('video', video_id_or_url, caption)
        return data

    def location(self, latitude: float, longitude: float, name: str, address: str) -> dict:
        """
        Constructs a payload for sending a location message.

        Parameters:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            name (str): The name of the location.
            address (str): The address of the location.

        Returns:
            dict: The payload for a location message.
        """
        data = self.base_data
        data['type'] = 'location'
        data['location'] = {
            'latitude': latitude,
            'longitude': longitude,
            'name': name,
            'address': address
        }
        return data

    def contacts(self, contacts: list[dict]) -> dict:
        # TODO: match the contacts format with schema
        raise NotImplementedError('This method is not implemented yet!')

    def interactive(self) -> dict:
        raise NotImplementedError('This method is not implemented yet!')

    def template(self) -> dict:
        raise NotImplementedError('This method is not implemented yet!')
