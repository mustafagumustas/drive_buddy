import pyaudio
import webrtcvad
import collections
import openai
import os
from dotenv import load_dotenv
from threading import Thread
import time
import io
import wave
client = openai.OpenAI()
# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("No OpenAI API key found in environment variables.")


def recognize_speech_from_mic():
    """Capture audio from the microphone and convert it to text using OpenAI API."""
    # Set up audio recording parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = 5

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print("Listening...")

    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    # Stop recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Convert audio data to bytes
    audio_data = b''.join(frames)

    # Convert bytes data to audio file
    audio_file = io.BytesIO(audio_data)
    audio_file.name = "audio.wav"

    # Send audio to OpenAI Whisper API
    # response = client.audio.transcriptions.create()

    return audio_file # response # removed the response, api excepts only audio file

def main():
    response = recognize_speech_from_mic()
    
    if "text" in response:
        print("You said: {}".format(response["text"]))
    else:
        print("Error: {}".format(response))

if __name__ == "__main__":
    main()
