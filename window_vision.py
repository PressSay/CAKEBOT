import time

import customtkinter
import threading
from PIL import Image


class ToplevelWindowModelVision(customtkinter.CTkToplevel):

    HEIGHT = 500
    WIDTH = 500

    def __init__(self, model_vision, model_vision_floating_var, toggle_floating_vision, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry(f"{ToplevelWindowModelVision.HEIGHT}x{ToplevelWindowModelVision.WIDTH}")

        self.title("Wislam")
        self.model_vision = model_vision
        self.model_vision_floating_var = model_vision_floating_var
        self.toggle_floating_vision = toggle_floating_vision

        thread_reset_model_vision = threading.Thread(target=self.model_vision.reset_model,
                                                     args=(self.callback_vision_func,))
        thread_reset_model_vision.daemon = True  # Cho phép luồng dừng khi đóng cửa sổ
        thread_reset_model_vision.start()

        self.model_vision_ui = customtkinter.CTkLabel(master=self, text="", corner_radius=5,
                                                      fg_color=["white", "black"])
        self.img_convert = Image.open("Resource/Images/camera-photo-icon-1507034122.png").resize((640, 480))
        self.model_vision_imgtk = customtkinter.CTkImage(
            self.img_convert, size=(self.model_vision_ui.winfo_width(), self.model_vision_ui.winfo_height()))
        self.model_vision_ui.configure(image=self.model_vision_imgtk, width=500, height=500)
        self.model_vision_ui.pack(side="top", padx=20, pady=20, fill="both", expand=True)
        self.model_vision_ui.bind("<Configure>", self.resize_event)

        self.protocol("WM_DELETE_WINDOW", self.exit_f)
        self.first_load = True

    def callback_vision_func(self, img):
        self.img_convert = Image.fromarray(img)
        if self.img_convert is None:
            return
        self.after(16, self.update_image)

    def update_image(self):
        if self.model_vision_imgtk is not None and self.img_convert is not None:
            self.model_vision_imgtk.configure(light_image=self.img_convert, dark_image=self.img_convert)

    def resize_event(self, event):
        if not self.img_convert or self.model_vision_imgtk is None:
            return
        self.after(60,
                   self.model_vision_imgtk.configure(size=(self.model_vision_ui.winfo_width(),
                                                           self.model_vision_ui.winfo_height())))

    def exit_f(self):
        self.model_vision_imgtk = None
        if self.model_vision.exist_system[0] != 0:
            print("Out window_vision")
            self.toggle_floating_vision()
        self.destroy()
