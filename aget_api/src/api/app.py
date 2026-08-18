from io import BytesIO
import numpy as np
import chainlit as cl
import tempfile
from pathlib import Path
import uuid

import os
import sys
import wave
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.workflow import create_workflow_graph

graph = create_workflow_graph().compile()


@cl.on_chat_start
async def on_chat_start():

    await cl.Message(
        content="Send me a text message or upload an audio file."
    ).send()

    user_id = "namrata"
    interview_id = str(uuid.uuid4())

    cl.user_session.set("user_id",user_id)
    cl.user_session.set("interview_id", interview_id)

    print("USER ID      :", user_id)
    print("INTERVIEW ID :", interview_id)


@cl.on_audio_start
async def on_audio_start():
    print("Audio recording started")

    # New buffer for this recording
    cl.user_session.set("audio_buffer", bytearray())
    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):

    print("Received audio chunk")

    audio = np.frombuffer(chunk.data, dtype=np.int16)

    print(
        "mime:", chunk.mimeType,"| samples:",len(audio),"| min:", audio.min(),"| max:",audio.max(),"| RMS:",
        np.sqrt(np.mean(audio.astype(np.float32) ** 2))
        )

    # Get/create the audio buffer
    audio_buffer = cl.user_session.get("audio_buffer")

    if audio_buffer is None:
        audio_buffer = bytearray()
        cl.user_session.set("audio_buffer", audio_buffer)

    audio_buffer.extend(chunk.data)
    cl.user_session.set("audio_buffer", audio_buffer)


@cl.on_audio_end
async def on_audio_end():
    """Process completed audio input"""

    # Get audio data
    audio_buffer = cl.user_session.get("audio_buffer")
    # audio_buffer.seek(0)
    # audio_data = audio_buffer.read()
    pcm_data = bytes(audio_buffer)

    print("PCM bytes:", len(pcm_data))

    # -----------------------------------------
    # Convert raw PCM -> valid WAV
    # -----------------------------------------

    audio_path = (
        Path("temp_audio")
        / f"{uuid.uuid4()}.wav"
    )

    audio_path.parent.mkdir(exist_ok=True)

    with wave.open(str(audio_path), "wb") as wav_file:

        wav_file.setnchannels(1)      # mono
        wav_file.setsampwidth(2)      # PCM16 = 2 bytes
        wav_file.setframerate(24000)  # Chainlit audio sample rate

        wav_file.writeframes(pcm_data)

    print("Audio file:", audio_path)
    print("PCM bytes:", len(pcm_data))

    # -----------------------------------------
    # Send actual WAV to graph
    # -----------------------------------------

    user_id = cl.user_session.get("user_id")
    interview_id = cl.user_session.get("interview_id")
    
    state = {
            "source": "local",
            "user_id" : user_id,
            "interview_id" : interview_id,
            "raw_input": {
                "modality": "audio",
                "data": str(audio_path),
                "mime_type": "audio/wav",
            },
            }
    
    result = await graph.ainvoke(input=state)

    await cl.Message(
                content=result.get("topic", "No response")
            ).send()

    # Clear buffer
    cl.user_session.set("audio_buffer", None)

@cl.on_message
async def on_message(message: cl.Message):

    # --------------------------------------------------
    # TEXT INPUT
    # --------------------------------------------------
    user_id = cl.user_session.get("user_id")
    interview_id = cl.user_session.get("interview_id")

    print(message.content)

    state = {
        "source": "local",
        "user_id" : user_id,
        "interview_id" : interview_id,
        "raw_input": {
            "modality": "text",
            "data": message.content,
            "mime_type": "text/plain",
        },
    }

    result = await graph.ainvoke(
        input=state)

    await cl.Message(
        content=result.get("topic", "No response")
    ).send()

    return