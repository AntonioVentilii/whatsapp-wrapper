from pydub import AudioSegment


def convert_audio(input_file_path: str, output_file_path: str):
    input_format = input_file_path.split('.')[-1]
    output_format = output_file_path.split('.')[-1]

    if input_format == output_format:
        raise ValueError("Input and output formats are the same")

    if input_format == 'mp3':
        audio = AudioSegment.from_mp3(input_file_path)
    elif input_format == 'ogg':
        audio = AudioSegment.from_ogg(input_file_path)
    elif input_format == 'opus':
        audio = AudioSegment.from_file(input_file_path, codec='opus')
    elif input_format == 'wav':
        audio = AudioSegment.from_wav(input_file_path)
    elif input_format == 'flac':
        audio = AudioSegment.from_file(input_file_path, 'flac')
    else:
        raise ValueError("Unsupported input format")

    audio.export(output_file_path, format=output_format)


def convert_audio_to_mp3(input_file_path: str) -> str:
    output_file_path = input_file_path.split('.')[0] + '.mp3'
    convert_audio(input_file_path, output_file_path)
    return output_file_path


def convert_ogg_to_mp3(ogg_file_path: str):
    mp3_file_path = ogg_file_path.split('.')[0] + '.mp3'
    convert_audio(ogg_file_path, mp3_file_path)
