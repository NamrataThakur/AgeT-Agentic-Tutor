import os
import tempfile
from typing import Optional
from groq import Groq
from dotenv import load_dotenv
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings

load_dotenv()

class SpeechToText:
    def __init__(self):
        self.stt_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def transcribe(self, audio_data : str) -> str:
        """Convert speech to text using Groq's Whisper model.

        Args:
            audio_data: Audio Data File Path (Bytes -> File is being done in the app.py)

        Returns:
            str: Transcribed text

        Raises:
            ValueError: If the audio file is empty or invalid
            RuntimeError: If the transcription fails
        """

        if not audio_data:
            raise ValueError("Audio Data Cannot Be Empty..!")

        try:
            try:
                # Use the temp file created to do the transcriptions:
                with open(audio_data, "rb") as file:
                    transcriptions = self.stt_client.audio.transcriptions.create(
                        file=file,
                        model=settings.SPEECH_MODEL_NAME,
                        language="en",
                        response_format="text",
                        temperature=0.0,
                    )

                    if not transcriptions:
                        print("Transcription is empty..!")

                    return transcriptions
            finally:
                print("File Processed")

        except Exception as e:
            print("Exception while transcribing audio data : ", str(e))
         

