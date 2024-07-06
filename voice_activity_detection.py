import pyaudio
import wave
import numpy as np

class SpeechRecorder:
    def __init__(self):
        self.chunk = 1024  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 1
        self.rate = 16000  # Record at 16000 samples per second
        self.silence_threshold = 500  # Adjust this threshold as needed
        self.silence_duration = 2  # Seconds of silence before considering speech finished
        self.audio = pyaudio.PyAudio()

    def is_silent(self, data):
        """Returns 'True' if below the silence threshold"""
        return np.frombuffer(data, dtype=np.int16).max() < self.silence_threshold

    def record(self):
        stream = self.audio.open(format=self.sample_format,
                                 channels=self.channels,
                                 rate=self.rate,
                                 frames_per_buffer=self.chunk,
                                 input=True)

        print("Adjusting for ambient noise...")
        print("Ready to record. Start speaking...")

        file_counter = 0

        while True:
            frames = []
            silent_chunks = 0
            is_recording = False

            while True:
                data = stream.read(self.chunk)
                frames.append(data)

                if self.is_silent(data):
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                    is_recording = True

                if is_recording and silent_chunks > (self.silence_duration * self.rate / self.chunk):
                    print(f"Speech chunk {file_counter + 1} finished.")
                    break

            if is_recording:
                self.save_audio(frames, file_counter)
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
