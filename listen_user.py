import time
import pvporcupine
import struct
import pyaudio

class ListenUser:
    def __init__(self,
                 pyAudio,
                 callback_robot,
                 start_wake_word_path="ListenUserFile/rô-bót-ơi_vn_linux_v3_0_0.ppn",
                 stop_wake_word_path="ListenUserFile/Kết-thúc_vn_linux_v3_0_0.ppn",
                 model_path="ListenUserFile/porcupine_params_vn.pv",
                 access_key=""):
        self.start_wake_word_path = start_wake_word_path
        self.stop_wake_word_path = stop_wake_word_path
        self.model_path = model_path
        self.access_key = access_key
        self.start_recording = False
        self.exit_recording = [1]
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=[self.start_wake_word_path],
            model_path=self.model_path
        )
        self.pa = pyAudio
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length)
        self.callback_robot = callback_robot

    def start_recording_func(self):
        # change icon here
        self.callback_robot(True)
        while not self.start_recording:
            if self.exit_recording[0] == 0:
                if self.porcupine is not None:
                    self.porcupine.delete()
                break
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                self.start_recording = True
                break

    def stop_recording_func(self):
        while self.start_recording:
            if self.exit_recording[0] == 0:
                if self.porcupine is not None:
                    self.porcupine.delete()
                break
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                self.start_recording = False
                break
        # change icon here
        self.callback_robot(self.start_recording)

    def stop_when_silence(self):
        self.start_recording = False

    def exit_system(self):
        self.exit_recording[0] = 0
        print(f"Thoát chương trình robot. {self.exit_recording}")
