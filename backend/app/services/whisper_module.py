import subprocess
import tempfile
import os
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_audio(audio_file_path):
    print("FILE SIZE:", os.path.getsize(audio_file_path)) # Debug - check audio file size
    # Convert webm from browser to wav
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        wav_path = wav_file.name

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", audio_file_path,
                "-ar", "16000",
                "-ac", "1",
                wav_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        segments, info = model.transcribe(wav_path)
        text = " ".join(segment.text for segment in segments)

        return text, info.language, info.language_probability

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)