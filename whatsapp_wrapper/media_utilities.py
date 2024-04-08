import os
import uuid
from datetime import datetime, timedelta
from mimetypes import guess_extension

from .configs import CACHE_DIR

supported_types = {
    'audio': ['audio/aac', 'audio/mp4', 'audio/mpeg', 'audio/amr', 'audio/ogg'],
    'document': ['text/plain', 'application/pdf', 'application/vnd.ms-powerpoint', 'application/msword',
                 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'image': ['image/jpeg', 'image/png'],
    'video': ['video/mp4', 'video/3gp'],
    'sticker': ['image/webp'],
}
flat_supported_types = [item for sublist in supported_types.values() for item in sublist]

type_to_extension = {
    'audio/ogg': '.ogg',
}


def check_media_type_supported(mime_type: str, raise_error: bool = False) -> bool:
    check = mime_type in flat_supported_types
    if not check and raise_error:
        raise ValueError(f"MIME type '{mime_type}' is not supported.")
    return check


def delete_old_files_in_cache(cache_dir: str = None):
    cache_dir = cache_dir or CACHE_DIR

    if not os.path.exists(cache_dir):
        print("Cache directory does not exist.")
        return

    threshold_date = datetime.now() - timedelta(weeks=1)

    for filename in os.listdir(cache_dir):
        file_path = os.path.join(cache_dir, filename)

        mod_time = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mod_time)

        if file_date < threshold_date:
            os.remove(file_path)
            print(f"Deleted old file: {filename}")


def save_media_to_temp_cache(mime_type: str, binary_data: bytes) -> str:
    cache_dir = CACHE_DIR
    delete_old_files_in_cache(cache_dir)

    file_extension = type_to_extension.get(mime_type, guess_extension(mime_type) or '.bin')
    while True:
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(cache_dir, file_name)
        if not os.path.exists(file_path):
            break

    with open(file_path, "wb") as file:
        file.write(binary_data)

    return file_path
