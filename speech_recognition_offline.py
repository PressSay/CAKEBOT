import sounddevice as sd
import numpy as np
import webrtcvad
from transformers import pipeline
import tempfile
import os
import threading
from queue import Queue, Empty
import soundfile as sf
import time


class RecognizerOff:
    def __init__(self):
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
        self.RAM_DIR = '/mnt/ramdisk'  # Directory mounted on tmpfs
        self.sample_rate = 16000  # Use 16 kHz sample rate
        self.frame_duration = 30  # Frame duration in ms (30ms)
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)  # Convert duration to samples
        self.channels = 1  # Mono channel
        self.speaking_lock = threading.Lock()
        self.speaking = False
        self.q = Queue()
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)
        self.transcriber = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3", device=-1)
        self.text = ""
        self.stop_recording = False

    def process_queue(self):
        time_render = 1 / 30
        current_time = time.time()

        while not self.stop_recording:
            time.sleep(time_render)
            now = time.time()
            interval_time = now - current_time
            if interval_time >= time_render:
                try:
                    while not self.q.empty():
                        task = self.q.get_nowait()
                        task.start()
                        task.join()  # Wait for the transcription thread to finish
                        self.stop_recording = True
                        break
                except Empty:
                    pass  # Handle the empty queue exception more gracefully

    def callback(self, indata, _, __, status):
        if status:
            print(f"Audio input error: {status}")

        # Convert input data to 16-bit PCM format for VAD
        raw_frame = indata[:, 0].copy()  # Get mono audio channel
        raw_frame = (raw_frame * 32767).astype(np.int16)  # Scale to int16 range

        # Check if there's speech detected in this frame
        is_speech = self.vad.is_speech(raw_frame.tobytes(), self.sample_rate)

        with self.speaking_lock:
            if is_speech:
                self.speaking = True
                transcribe_thread = threading.Thread(target=self.record_until_silent)
                self.q.put(transcribe_thread)
            else:
                self.speaking = False

    def record_until_silent(self):
        block_duration = 1  # Duration of each block to capture
        audio_frames = []
        print("Recording...")

        # Continuously record audio in blocks until silence is detected
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='int16') as stream:
            while self.speaking:
                audio_chunk, overflowed = stream.read(int(block_duration * self.sample_rate))
                audio_frames.append(audio_chunk)

        # Combine all recorded audio frames
        audio_data = np.concatenate(audio_frames, axis=0)

        # Save the recorded audio to a temporary file
        with tempfile.NamedTemporaryFile(dir=self.RAM_DIR, suffix=".wav", delete=False) as temp_wav_file:
            temp_filename = temp_wav_file.name
            sf.write(temp_filename, audio_data, self.sample_rate)

        print("Đã thu âm xong.")
        # Transcribe the audio
        self.text = self.transcriber(temp_filename)["text"]

        # Optionally, remove the temporary file after transcription
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    def detect_speech(self):
        with sd.InputStream(callback=self.callback, channels=self.channels,
                            samplerate=self.sample_rate, blocksize=self.frame_size):
            print("Đang lắng nghe... Hãy nói vào microphone.")
            try:
                while not self.stop_recording:
                    # time out set here
                    # print("Thời gian chờ quá lâu.")
                    sd.sleep(1000)
            except KeyboardInterrupt:
                print("Stopped.")

    def run(self):
        # Start listening for speech
        process_queue_thread = threading.Thread(target=self.process_queue, args=())
        process_queue_thread.start()
        self.detect_speech()  # Start detecting speech
        process_queue_thread.join()
        return self.text
