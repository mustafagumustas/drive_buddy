import os
import pyaudio
import wave
import webrtcvad
from dotenv import load_dotenv
import openai
from google.cloud import texttospeech
import langdetect

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found in environment variables.")

# Debug print to verify the API key
print(f"Using OpenAI API Key: {openai_api_key[:5]}...{openai_api_key[-5:]}")

# Set the API key explicitly
openai.api_key = openai_api_key
    

def record_audio(output_file_path, record_seconds=5):
    chunk = 1024  # Record in chunks of 1024 samples
    format = pyaudio.paInt16  # 16 bits per sample
    channels = 1  # Number of audio channels
    rate = 44100  # Record at 44100 samples per second

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    print("Recording...")

    frames = []

    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(output_file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

def speech_to_text(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcription = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
    return transcription['text']

def gpt_response(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message['content']

def text_to_speech(text, output_file_path):
    """
    Converts text to speech and saves it as an audio file.

    Args:
    text (str): The text to be converted to speech.
    output_file_path (str): The path to save the output audio file.
    """
    
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(language_code = langdetect.detect(text),
                                              ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_file_path, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to file "{output_file_path}"')


# Example usage
record_audio("sound.wav", record_seconds=5)
text = speech_to_text("sound.wav")
print("Transcribed Text:", text)

response_text = gpt_response(text)
print("GPT Response:", response_text)

text_to_speech(response_text, "output.mp3")


