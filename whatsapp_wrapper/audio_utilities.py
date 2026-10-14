import os
import shutil
import subprocess

import ffmpeg_downloader as ffdl


def get_ffmpeg_path() -> str:
    # Prefer an ffmpeg on PATH, then one installed with `ffdl install`.
    path = shutil.which('ffmpeg') or ffdl.ffmpeg_path
    if not path:
        raise RuntimeError("ffmpeg not found. Install it on the system or run `ffdl install`.")
    return path


def convert_audio(input_file_path: str, output_file_path: str):
    # ffmpeg detects the input format from the content, so any audio WhatsApp sends (ogg/opus, aac, amr, mp4,
    # mpeg) is supported, and the output format is taken from the output file extension.
    if os.path.splitext(input_file_path)[1].lower() == os.path.splitext(output_file_path)[1].lower():
        raise ValueError("Input and output formats are the same")

    subprocess.run(
        [get_ffmpeg_path(), '-y', '-loglevel', 'error', '-i', input_file_path, '-vn', output_file_path],
        check=True,
    )


def convert_audio_to_mp3(input_file_path: str) -> str:
    if input_file_path.lower().endswith('.mp3'):
        return input_file_path
    output_file_path = os.path.splitext(input_file_path)[0] + '.mp3'
    convert_audio(input_file_path, output_file_path)
    return output_file_path


def convert_ogg_to_mp3(ogg_file_path: str) -> str:
    return convert_audio_to_mp3(ogg_file_path)
