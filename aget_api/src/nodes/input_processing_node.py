import os
import sys
from pathlib import Path
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from modules.speech_to_text import SpeechToText
from graph.state import AgentState

class InputProcessingNode:
    def __init__(self):
        self.speech_to_text_processing = SpeechToText()

    async def execute(self, state: AgentState) -> dict:

        raw_input = state["raw_input"]
        modality = raw_input["modality"]
        input_data = raw_input["data"]

        if modality == "audio":
            content = await self.speech_to_text_processing.transcribe(audio_data=input_data)

        elif modality == "text":
            content = input_data

        else:
            raise ValueError(f"Unsupported input type: {modality}")

        return {
            "user_input" : content,
        }