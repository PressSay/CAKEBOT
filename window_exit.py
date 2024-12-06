import time

import customtkinter
import threading


class ToplevelWindowExit(customtkinter.CTkToplevel):
    def __init__(self, assistant, thread_process_message, model_vision, model_vision_floating_var, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assistant = assistant
        self.thread_process_message = thread_process_message
        self.model_vision = model_vision
        self.model_vision_floating_var = model_vision_floating_var

        self.geometry("360x130")
        self.title("Wislam")
        self.label = customtkinter.CTkLabel(self, text="Do you want to exit?")
        self.label.pack(padx=20, pady=20)
        self.label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

        self.yes_button = customtkinter.CTkButton(self, text="Yes", command=self.exit_f)
        self.yes_button.grid(row=1, column=0, padx=20, pady=10)

        self.no_button = customtkinter.CTkButton(self, text="No", command=self.cancel_f)
        self.no_button.grid(row=1, column=1, padx=20, pady=10)
        self.model_vision.pause_model()

    def exit_f(self):
        thread_reset_model_vision = threading.Thread(target=self.model_vision.quit_model)
        thread_reset_model_vision.start()
        if self.thread_process_message is not None:
            self.thread_process_message.join()
            print("Đã thoát process_message")
        self.assistant.quit_system()
        self.destroy()
        exit()

    def cancel_f(self):
        if self.model_vision_floating_var[0] == 1 or self.model_vision_floating_var[0] == 0:
            self.model_vision.continue_model()
        self.destroy()
