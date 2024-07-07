import os
import pyaudio
import wave
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import openai

# Load environment variables from .env file
load_dotenv()
client = OpenAI()
# Retrieve API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found in environment variables.")

# Debug print to verify the API key
print(f"Using OpenAI API Key: {openai_api_key[:5]}...{openai_api_key[-5:]}")

class SpeechRecorder:
    def __init__(self):
        self.chunk = 1024  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 1
        self.rate = 16000  # Record at 16000 samples per second
        self.silence_threshold = 500  # Adjust this threshold as needed
        self.silence_duration = 1.75  # Seconds of silence before considering speech finished
        self.audio = pyaudio.PyAudio()
        self.conversation_history = []
        self.noise_levels = []

    def is_silent(self, data):
        """Returns 'True' if below the silence threshold"""
        max_value = np.frombuffer(data, dtype=np.int16).max()
        if not self.noise_levels:  # If noise_levels is empty, we are still calibrating
            self.noise_levels.append(max_value)
        return max_value < self.silence_threshold

    def adjust_silence_threshold(self):
        if self.noise_levels:
            self.silence_threshold = np.mean(self.noise_levels) + 100  # Add buffer to average noise level

    def record(self):
        stream = self.audio.open(format=self.sample_format,
                                 channels=self.channels,
                                 rate=self.rate,
                                 frames_per_buffer=self.chunk,
                                 input=True)

        print("Adjusting for ambient noise...")
        print("Ready to record. Start speaking...")

        file_counter = 0
        calibrating = True

        while True:
            frames = []
            silent_chunks = 0
            is_recording = False

            while True:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                except IOError as e:
                    print(f"Error: {e}")
                    continue

                frames.append(data)

                if calibrating:
                    self.noise_levels.append(np.frombuffer(data, dtype=np.int16).max())
                    if len(self.noise_levels) > 50:  # Collect 50 chunks of ambient noise
                        calibrating = False
                        self.adjust_silence_threshold()
                        print(f"Calibrated silence threshold: {self.silence_threshold}")

                if self.is_silent(data) and not calibrating:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                    is_recording = True

                if is_recording and silent_chunks > (self.silence_duration * self.rate / self.chunk):
                    print(f"Speech chunk {file_counter + 1} finished.")
                    break

            if is_recording:
                file_name = self.save_audio(frames, file_counter)
                user_text = self.process_audio(file_name)
                print(f"User asked: {user_text}")
                self.conversation_history.append({"role": "user", "content": user_text})
                response_text = self.gpt_response()
                print(f"Response: {response_text}")
                self.conversation_history.append({"role": "assistant", "content": response_text})
                file_counter += 1

    def save_audio(self, frames, counter):
        file_name = f"output_{counter}.wav"
        wf = wave.open(file_name, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"Audio saved as {file_name}")
        return file_name

    def process_audio(self, audio_file_path):
        with open(audio_file_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return response.text

    def gpt_response(self):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
            ] + self.conversation_history
        )
        return response.choices[0].message.content

    def close(self):
        self.audio.terminate()

if __name__ == "__main__":
    recorder = SpeechRecorder()
    try:
        recorder.record()
    except KeyboardInterrupt:
        print("Recording stopped by user.")
    finally:
        recorder.close()
