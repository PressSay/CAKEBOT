import time
from PIL import ImageFont, ImageDraw, Image
import cv2
from ultralytics import YOLO
from text_to_speech_v2 import TextToSpeech
import constant_variable_v2 as const_var
import threading
import logging
import numpy as np
logging.getLogger("ultralytics").setLevel(logging.ERROR)


class YOLOWebcamDetector:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.models = [
            # YOLO("/home/lpq/Projects/LuanVan/Vision/Tan Hue Vien New/yolov8n.pt"),
            YOLO("/home/lpq/Projects/LuanVan/Vision/Yolo/BanhConLai/V8/runs/detect/train/weights/best.pt"),
            YOLO('/home/lpq/Projects/LuanVan/Vision/Yolo/BanhPia/V8/runs/detect/train/weights/best.pt')
        ]
        for i in range(len(self.models)):
            self.models[i].to('cuda')
        self.classNames = [
            # const_var.GENERIC_CLASSES_NAME,
            const_var.BANH_CON_LAI_NAME,
            const_var.BANH_PIA_CLASSES_NAME]
        self.classFlags = [{class_name: False for class_name in self.classNames[0]},
                           {class_name: False for class_name in self.classNames[1]}]
        self.classCounters = [{class_name: 0 for class_name in self.classNames[0]},
                              {class_name: 0 for class_name in self.classNames[1]}]
        self.frames_to_check = 15
        self.max_frames = 30
        self.decay_rate = 5
        self.exist_system = [1]
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        self.img = None
        self.lock = threading.Lock()
        self.threading_vision = None
        self.threading_floating_window = None

    def speak_text(self, command):
        self.tts.speak_text(command)

    def process_results(self, results, class_names, i):
        detected_classes = set()
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = round(float(box.conf[0]) * 100, 2)
                if confidence <= 70:
                    continue
                cls = int(box.cls[0])
                # if i == 0 and class_names[cls] != "người":
                #     continue
                text = f"{class_names[cls]} {confidence}%"
                cv2.rectangle(self.img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                pil_img = Image.fromarray(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_img)
                draw.text((x1, y1), text, font=self.font, fill=(255, 0, 0))
                self.img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                detected_classes.add(class_names[cls])
        with self.lock:
            for class_name in self.classNames[i]:
                if class_name in detected_classes:
                    self.classCounters[i][class_name] = min(self.classCounters[i][class_name] + 1, self.max_frames)
                else:
                    self.classCounters[i][class_name] = max(self.classCounters[i][class_name] - self.decay_rate, 0)

                if self.classCounters[i][class_name] >= self.frames_to_check and not self.classFlags[i][class_name]:
                    # if class_name == "người":
                    #     self.speak_text("Xin chào bạn, tôi có thể giúp gì cho bạn")
                    # elif i == 1:
                    #     self.speak_text(f"Tôi đoán đây là {class_name}, bạn muốn tìm hiểu thêm không")
                    self.classFlags[i][class_name] = True
                elif self.classCounters[i][class_name] < self.frames_to_check:
                    self.classFlags[i][class_name] = False

    def run_detection(self):
        while True:
            success, self.img = self.cap.read()
            if not success:
                print("Lỗi: Không thể lấy hình ảnh từ webcam.")
                break

            for i in range(len(self.models)):
                results = self.models[i](self.img, stream=True)
                self.process_results(results, self.classNames[i], i)

    def stop(self):
        self.cap.release()

    def restart_camera(self):
        # Restart the camera by creating a new VideoCapture instance
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

    def floating_window(self, callback):
        while True:
            if self.exist_system[0] == 0:
                self.stop()
                break
            if self.img is not None and self.exist_system[0] == 1:
                b, g, r = cv2.split(self.img)
                img_merge = cv2.merge((r, g, b))
                callback(img_merge)
            if self.exist_system[0] == 2:
                time.sleep(1/30)

    def run_model(self, callback):
        self.threading_vision = threading.Thread(target=self.run_detection)
        self.threading_floating_window = threading.Thread(target=self.floating_window, args=(callback,))
        self.threading_vision.start()
        self.threading_floating_window.start()

    def quit_model(self):
        self.exist_system[0] = 0
        self.threading_floating_window.join()
        self.threading_vision.join()

    def reset_model(self, callback):
        self.exist_system[0] = 0
        self.threading_floating_window.join()
        self.threading_vision.join()
        self.continue_model()
        self.restart_camera()
        self.run_model(callback)

    def pause_model(self):
        self.exist_system[0] = 2

    def continue_model(self):
        self.exist_system[0] = 1
