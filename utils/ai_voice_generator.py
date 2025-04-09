from TTS.api import TTS
import re
# Initialize the TTS model for CPU
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", gpu=False)


def generate_voice(text, videoTitle):
    # Remove emojis and special characters
    text = re.sub(r'[^\w\s.,!?\'\"]', '', text)

    # Generate speech and save to a file
    output_path = f"temp/{videoTitle}.wav"
    tts.tts_to_file(text=text, file_path=output_path)

    print(f"Audio saved to {output_path}")
    return output_path


