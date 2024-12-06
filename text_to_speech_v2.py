import threading
from gtts import gTTS
import os
import tempfile
import wave
import pyaudio
from io import BytesIO
from pydub import AudioSegment
import queue

class TextToSpeech:
    def __init__(self, pyAudio, lang='vi'):
        self.lang = lang
        self.p = pyAudio
        self.thread_speak_current = None
        self.have_new_stream = False
        self.is_start_tts = False
        self.is_use_stop_current_speak = False
        self.queue = queue.Queue()

    def stop_current_speak(self):
        self.is_use_stop_current_speak = True
        self.have_new_stream = True
        while not self.queue.empty():
            self.queue.get()
        self.is_use_stop_current_speak = False

    def stop_tts(self):
        self.is_start_tts = False

    def start_tts(self):
        self.is_start_tts = True
        self.thread_speak_current = threading.Thread(target=self.play_audio)
        self.thread_speak_current.start()

    def speak_text(self, text):
        self.have_new_stream = False
        self.queue_sound(text)

    def callback(self, in_data, frame_count, time_info, status, wf):
        data = wf.readframes(frame_count)
        return (data, pyaudio.paContinue)

    def queue_sound(self, text):
        tts = gTTS(text=text, lang=self.lang, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            mp3_file_path = temp_audio.name
            tts.save(mp3_file_path)
        sound = AudioSegment.from_mp3(mp3_file_path)
        buffer = BytesIO()
        sound.export(buffer, format="wav")
        buffer.seek(0)
        self.queue.put(buffer)
        os.remove(mp3_file_path)

    def play_audio(self):
        while self.is_start_tts:
            if self.queue.empty():
                pass
            buffer = self.queue.get()  # Dấu ngoặc phải có
            wf = wave.open(buffer, 'rb')  # Mở wave từ buffer
            stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                                 channels=wf.getnchannels(),
                                 rate=wf.getframerate(),
                                 output=True,
                                 stream_callback=lambda in_data, frame_count, time_info, status: self.callback(in_data,
                                                                                                               frame_count,
                                                                                                               time_info,
                                                                                                               status,
                                                                                                               wf))
            stream.start_stream()
            while stream.is_active() and not self.have_new_stream:
                pass
            stream.stop_stream()
            stream.close()
            wf.close()
        print("kết thúc")
        self.thread_speak_current = None  # Đảm bảo reset thread sau khi hoàn thành