import threading
import queue
import logging
import time
import pyaudio
from text_to_speech_v2 import TextToSpeech
from processer_query import HandlerQuery
from speech_recognition import Recognizer, WaitTimeoutError, UnknownValueError, RequestError, Microphone
# from speech_recognition_offline import RecognizerOff
from listen_user import ListenUser
from pynput import keyboard

logging.basicConfig(level=logging.INFO)


class VoiceAssistant:
    def __init__(self, callback_voice, callback_robot, callback_logging, model_vision, online=True):
        self.recording = False
        self.audio_data = None
        self.listening_thread = None
        self.robot_start_thread = None
        self.robot_end_thread = None
        self.active_thread = None
        self.online = online
        self.model_vision = model_vision
        self.pyAudio = pyaudio.PyAudio()
        self.tts = TextToSpeech(pyAudio=self.pyAudio)
        self.tts.start_tts()
        self.lu = ListenUser(pyAudio=self.pyAudio,callback_robot=callback_robot)
        self.handler = HandlerQuery(self.tts)
        # self.srf = RecognizerOff()
        self.sr = Recognizer()
        self.condition = threading.Condition()
        self.stop_event = threading.Event()
        self.q = queue.Queue()
        self.processed = False
        self.should_exit = False
        self.lock = threading.Lock()
        self.micro_ui = []
        self.callback_voice = callback_voice
        self.callback_logging = callback_logging

    def listen_from_microphone(self):
        if not self.online:
            # self.audio_data = self.srf.run()
            return
        else:
            recognizer = self.sr
            # if len(self.micro_ui) > 3:
            #     self.micro_ui[0].configure(image=self.micro_ui[1])
            with Microphone() as source:
                if self.callback_logging is not None:
                    self.callback_logging("Đang lắng nghe... Hãy nói vào microphone.")
                recognizer.adjust_for_ambient_noise(source)
                self.audio_data = None

                with self.condition:
                    while not self.recording:
                        self.condition.wait()

                if self.should_exit:
                    return
                try:
                    self.tts.stop_current_speak()
                    self.audio_data = recognizer.listen(source)
                except WaitTimeoutError:
                    if self.callback_logging is not None:
                        self.callback_logging("Thời gian chờ quá lâu.")
                # if len(self.micro_ui) > 3:
                #     self.micro_ui[0].configure(image=self.micro_ui[2])
                if self.audio_data is not None:
                    if self.callback_logging is not None:
                        self.callback_logging("Đã thu âm xong.")
                    self.lu.stop_when_silence()

    def process_audio(self):
        text = ""
        if self.online and self.audio_data is not None:
            try:
                text = self.sr.recognize_google(self.audio_data, language="vi-VN")
            except UnknownValueError:
                if self.callback_logging is not None:
                    self.callback_logging("Google Speech Recognition không thể hiểu âm thanh")
            except RequestError as e:
                if self.callback_logging is not None:
                    self.callback_logging(f"Không thể kết nối với Google Speech Recognition service; {e}")
        elif not self.online:
            text = self.audio_data

        if text == "":
            self.callback_logging("Không có dữ liệu âm thanh để xử lý, hãy thử lại.")
            self.tts.speak_text("Không có dữ liệu âm thanh để xử lý, hãy thử lại.")
            return

        text = text.replace("robot ơi", "")

        if self.callback_logging is not None:
            self.callback_logging("Kết quả nhận diện: " + text)
        query = text
        response = self.handler.process_handling(query, self.model_vision)

        if self.callback_voice is not None:
            self.callback_voice(query, response)

        if self.lu.exit_recording[0] == 0:
            return

        debug = False
        if not debug:
            if self.active_thread is not threading.current_thread():  # Avoid joining the current thread
                self.active_thread.join()  # Only join if it's not the current thread
            del self.active_thread
            self.active_thread = None
            # Start new threads
            self.robot_start_thread = threading.Thread(target=self.lu.start_recording_func)
            self.active_thread = threading.Thread(target=self.active)
            self.robot_start_thread.start()
            self.active_thread.start()

    def start_listening(self):
        with self.condition:
            self.recording = True
            self.condition.notify()
        self.stop_event.clear()
        self.robot_end_thread = threading.Thread(target=self.lu.stop_recording_func)
        self.active_thread = threading.Thread(target=self.active)
        self.listening_thread = threading.Thread(target=self.listen_from_microphone)

        # Hên xui nếu nói "robot ơi"(robot_end_thread) lúc luồng listening
        # chưa khởi chạy thì luồng listening sẽ chạy vĩnh viễn
        # (Giải pháp chính là thời gian chờ timeout=5s)
        self.listening_thread.start()
        self.robot_end_thread.start()
        self.active_thread.start()

    def stop_listening(self):
        with self.condition:
            self.recording = False
            self.condition.notify()
        self.stop_event.set()
        # if self.listening_thread is not None and self.listening_thread.is_alive():
            # self.listening_thread.join()
        self.process_audio()

    def active(self):
        with self.lock:
            if self.robot_start_thread is not None:
                self.robot_start_thread.join()
                self.tts.speak_text("tôi đây")
                self.robot_start_thread = None
            if self.robot_end_thread is not None:
                self.robot_end_thread.join()
                self.robot_end_thread = None

        if self.lu.start_recording:
            if not self.recording:
                self.callback_logging("Bắt đầu thu âm...")
                self.start_listening()
        else:
            if self.recording:
                self.callback_logging("Dừng thu âm.")
                self.tts.speak_text("Đợi tôi chút nhé")
                self.stop_listening()

    def quit_system(self):
        self.tts.stop_current_speak()
        self.tts.stop_tts()
        self.lu.exit_system()
        self.should_exit = True
        with self.lock:
            if self.robot_start_thread and self.robot_start_thread.is_alive():
                self.robot_start_thread.join()
            print("Đã thoát robot start")
            if self.robot_end_thread and self.robot_end_thread.is_alive():
                self.robot_end_thread.join()
            print("Đã thoát robot_end")
            if self.listening_thread and self.listening_thread.is_alive():
                self.listening_thread.join()
            print("Đã thoát listening")
            if self.active_thread and self.active_thread.is_alive():
                self.active_thread.join()
            print("Đã thoát active")
            # self.pyAudio.terminate()

    def run_voice(self):
        mic_list = Microphone.list_microphone_names()
        if len(mic_list) == 0:
            return False
        with self.lock:
            self.robot_start_thread = threading.Thread(target=self.lu.start_recording_func)
            self.active_thread = threading.Thread(target=self.active)
            self.robot_start_thread.start()
            self.active_thread.start()
        return True

    def on_release(self, key):
        if key == keyboard.Key.esc:
            logging.info("Thoát chương trình.")
            self.tts.stop_tts()
            self.lu.exit_system()
            self.should_exit = True
            with self.lock:
                if self.robot_start_thread and self.robot_start_thread.is_alive():
                    self.robot_start_thread.join()
                print("Đã thoát robot start")
                if self.robot_end_thread and self.robot_end_thread.is_alive():
                    self.robot_end_thread.join()
                print("Đã thoát robot_end")
                if self.listening_thread and self.listening_thread.is_alive():
                    self.listening_thread.join()
                print("Đã thoát listening")
                if self.active_thread and self.active_thread.is_alive():
                    self.active_thread.join()
                print("Đã thoát active")
            return False

    def run(self):
        logging.info("Nhấn Esc để thoát chương trình.")
        with keyboard.Listener(on_release=self.on_release) as listener:
            with self.lock:
                self.robot_start_thread = threading.Thread(target=self.lu.start_recording_func)
                self.active_thread = threading.Thread(target=self.active)
                self.robot_start_thread.start()
                self.active_thread.start()
            listener.join()

