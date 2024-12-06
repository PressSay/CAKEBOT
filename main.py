import threading
import customtkinter
from voice_assistant_v3 import VoiceAssistant
from model_vision import YOLOWebcamDetector
from PIL import Image
import platform
from window_exit import ToplevelWindowExit
from window_vision import ToplevelWindowModelVision

app_logo = customtkinter.CTkImage(light_image=Image.open("Resource/Images/GUI.png"),
                                  size=(50, 50))

customtkinter.set_appearance_mode("Light")
customtkinter.set_default_color_theme("blue")


def change_appearance_mode_event(new_appearance_mode: str):
    customtkinter.set_appearance_mode(new_appearance_mode)


class InputFrame(customtkinter.CTkFrame):
    def __init__(self, master, scrollable_frames, tabview, model_vision):
        super().__init__(master)
        self.assistant = VoiceAssistant(self.callback_assistant, self.callback_robot,
                                        self.callback_logging_assistant, model_vision)
        self.scrollable_frames = scrollable_frames
        self.tabview = tabview
        self.model_vision = model_vision

        self.loading_label_assistant = None
        self.thread_process_message = None

        self.grid_columnconfigure(0, weight=1)
        self.message_counter = 1
        self.entry = customtkinter.CTkEntry(self, placeholder_text="Type a message")
        self.entry.grid(row=1, column=0, columnspan=1, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.main_button_1 = customtkinter.CTkButton(master=self, text="Send", fg_color="transparent", border_width=2,
                                                     text_color=("gray10", "#DCE4EE"), command=self.send_message)
        self.main_button_1.grid(row=1, column=1, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.micro_icon = customtkinter.CTkImage(
            light_image=Image.open("Resource/Images/microphone.png"),
            dark_image=Image.open("Resource/Images/microphone.png"),
            size=(20, 20))
        self.micro_icon_active = customtkinter.CTkImage(
            light_image=Image.open("Resource/Images/microphone_active.png"),
            dark_image=Image.open("Resource/Images/microphone_active.png"),
            size=(20, 20))
        self.listen_button = customtkinter.CTkButton(self, text="", image=self.micro_icon, command=self.micro_func)
        self.listen_button.grid(row=1, column=2, padx=(20, 10), pady=(20, 20), sticky="nsew")

    def send_message(self):
        message = self.entry.get()
        if len(message) > 0:
            self.entry.delete(0, len(message))
            # self.send_message_widget(self.tabview.tab(self.tabview.get()), message + "\n", self.message_counter)
            self.send_message_widget(self.scrollable_frames[self.tabview.get()], message + "\n", self.message_counter)
            self.message_counter = self.message_counter + 1

            # Process here
            loading_label = customtkinter.CTkLabel(self.scrollable_frames[self.tabview.get()],
                                                   text="Đang soạn tin...", width=840,
                                                   font=customtkinter.CTkFont(size=14), text_color="gray", anchor="w")
            loading_label.grid(row=self.message_counter, column=1, columnspan=2, padx=(10, 10), sticky="nsew")
            self.main_button_1.configure(state="disabled")
            # # Xử lý tin nhắn trong một thread riêng để không chặn giao diện
            self.thread_process_message = threading.Thread(target=self.process_message, args=(message, loading_label))
            self.thread_process_message.start()

    def micro_func(self):
        succeeded = self.assistant.run_voice()
        # if succeeded:
        #     print("Thu âm bằng giao diện thành công")

    def callback_robot(self, toggle_listen_user):
        if toggle_listen_user:
            # print("toggle listen user: True")
            self.listen_button.configure(image=self.micro_icon_active)
            self.listen_button.configure(state="disabled")
        else:
            # print("toggle listen user: False")
            self.listen_button.configure(image=self.micro_icon)
            self.listen_button.configure(state="normal")

    def callback_assistant(self, query, response):
        def create_query_widget():
            self.send_message_widget(
                self.scrollable_frames[self.tabview.get()],
                query + "\n", self.message_counter)
            self.message_counter = self.message_counter + 1

        def create_response_widget():
            self.recv_message_widget(self.scrollable_frames[self.tabview.get()],
                                     response + "\n", self.message_counter, "red")
            self.message_counter = self.message_counter + 1

        if self.loading_label_assistant is not None:
            # print("Destoy loading_label")
            self.loading_label_assistant.destroy()
            self.loading_label_assistant = None
        self.after(90,
                   lambda: create_query_widget())
        self.after(100,
                   lambda: create_response_widget())
        self.after(110,
                   lambda: self.main_button_1.configure(state="normal"))

    def callback_logging_assistant(self, text):
        if self.loading_label_assistant is None:
            self.loading_label_assistant = (customtkinter.CTkLabel
                                            (self.scrollable_frames[self.tabview.get()],
                                             text=text, width=840,
                                             font=customtkinter.CTkFont(size=14), text_color="gray", anchor="w"))
            self.loading_label_assistant.grid(row=self.message_counter, column=1, columnspan=2, padx=(10, 10),
                                              sticky="nsew")
        else:
            self.loading_label_assistant.configure(text=text)

    @staticmethod
    def send_message_widget(root, message, message_counter):
        sent_message = customtkinter.CTkLabel(root, text="", width=840,
                                              font=customtkinter.CTkFont(size=14),
                                              text_color=("gray10", "#DCE4EE"), anchor="e", wraplength=700)
        if isinstance(message, str):
            sent_message.configure(text=message + "\n")
        else:
            sent_message.configure(image=message)
        sent_message.grid(row=message_counter, column=1, columnspan=2, padx=(10, 10), sticky="nsew")

    @staticmethod
    def recv_message_widget(root, message, message_counter, color):
        received_message = customtkinter.CTkLabel(root, text="", width=840,
                                                  font=customtkinter.CTkFont(size=14),
                                                  text_color=color, anchor="w", wraplength=700)
        if isinstance(message, str):
            received_message.configure(text=message + "\n")
        else:
            received_message.configure(image=message)
        received_message.grid(row=message_counter, column=1, columnspan=2, padx=(10, 10), sticky="nsew")

    def process_message(self, message, loading_label):
        # Xử lý tin nhắn tại đây

        response = self.assistant.handler.process_handling(message, self.model_vision)
        # Xóa nhãn đang tải
        loading_label.destroy()
        # Hiển thị phản hồi
        self.recv_message_widget(self.scrollable_frames[self.tabview.get()],
                                 response + "\n", self.message_counter, "red")
        self.message_counter = self.message_counter + 1
        self.main_button_1.configure(state="normal")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.model_vision = YOLOWebcamDetector()

        self.users = None
        self.sent_message = None
        self.received_message = None
        self.name = None

        self.chat_counter = 2
        self.resizable(width=False, height=True)
        self.title("Wislam")
        self.geometry(f"{1100}x{570}")

        self.grid_columnconfigure(1, weight=1)
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=7, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo = customtkinter.CTkLabel(self.sidebar_frame, image=app_logo, text="",
                                           font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Chats",
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=1, column=0, padx=20)
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Clear Chat", command=self.clear_chat)
        self.sidebar_button_1.grid(row=2, column=0, padx=20, pady=10)

        self.model_vision_floating_var = [1]
        self.model_vision_floating = customtkinter.CTkButton(self.sidebar_frame,
                                                             text="Floating Vision",
                                                             command=self.toggle_floating_vision)
        self.model_vision_floating.grid(row=5, column=0, padx=20, pady=10)

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_options = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                   values=["Light", "Dark", "System"],
                                                                   command=change_appearance_mode_event)
        self.appearance_mode_options.grid(row=6, column=0, padx=20, pady=(10, 10))

        self.exit_button = customtkinter.CTkButton(self.sidebar_frame, text="Exit", hover_color="Red",
                                                   command=self.exit_app)
        self.exit_button.grid(row=7, column=0, padx=20, pady=10)

        self.tabview_width = 250
        self.tabview_height = 490
        self.scrollable_frames = {}
        self.tabview = customtkinter.CTkTabview(
            master=self, width=self.tabview_width, height=self.tabview_height,
            command=lambda: self.bind_scroll_events(self.tabview, self.scrollable_frames))
        self.tabview.grid(row=0, column=1, columnspan=4, padx=(20, 10), pady=(10, 0), sticky="nsew")

        self.tabview.add("All")  # add tab at the end
        self.tabview.set("All")  # set currently visible tab

        scrollable_frame_tab1 = customtkinter.CTkScrollableFrame(self.tabview.tab("All"))
        scrollable_frame_tab1.pack(expand=True, fill="both")
        self.scrollable_frames["All"] = scrollable_frame_tab1  # Lưu khung cuộn vào từ điển
        self.bind_scroll_events(self.tabview, self.scrollable_frames)

        self.input_frame = InputFrame(self, self.scrollable_frames, self.tabview, self.model_vision)
        self.input_frame.grid(row=3, column=1, columnspan=4, sticky="nsew")
        self.input_frame.configure(fg_color="transparent")

        self.model_vision_imgtk = customtkinter.CTkImage(
            light_image=Image.open(
                "/home/lpq/Downloads/HinhAnhThamKhao/camera-photo-icon-1507034122.png").resize((240, 240)),
            dark_image=Image.open(
                "/home/lpq/Downloads/HinhAnhThamKhao/camera-photo-icon-1507034122.png").resize((240, 240)),
            size=(240, 240)
        )
        self.model_vision_ui = customtkinter.CTkLabel(master=self, text="", image=self.model_vision_imgtk)
        self.model_vision_ui.place(relx=0.30, rely=0.28, anchor="center")

        # set default values
        name_dialog = customtkinter.CTkInputDialog(text="What is your name:", title="Gemini_Advanced")
        name = name_dialog.get_input()
        self.appearance_mode_options.set("Light")
        if name == "":
            print("exit program")
            exit()
        self.set_name(name=name)
        self.toplevel_window = None
        self.toplevel_vision = None

        self.model_vision.run_model(self.callback_vision_func)

    def toggle_floating_vision(self):
        if self.model_vision_floating_var[0] == 1:
            self.model_vision_floating_var[0] = 0
            self.model_vision_ui.place_forget()
            if self.toplevel_vision is None or not self.toplevel_vision.winfo_exists():
                self.toplevel_vision = ToplevelWindowModelVision(
                    self.model_vision, self.model_vision_floating_var, self.toggle_floating_vision,
                    self)
                self.toplevel_vision.focus()
            else:
                self.toplevel_vision.focus()
            self.model_vision_floating.configure(state="disabled")
        elif self.model_vision_floating_var[0] == 0:
            self.model_vision_floating_var[0] = 1
            thread_reset_model_vision = threading.Thread(target=self.model_vision.reset_model,
                                                         args=(self.callback_vision_func,))
            thread_reset_model_vision.start()
            self.model_vision_ui.place(relx=0.30, rely=0.28, anchor="center")
            self.model_vision_floating.configure(state="normal")

    def callback_vision_func(self, img):
        img_convert = Image.fromarray(img).resize((240, 240))
        self.after(33,
                   lambda: self.model_vision_imgtk.configure(dark_image=img_convert, light_image=img_convert)
                   if self.model_vision_imgtk is not None else None)

    def exit_app(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindowExit(
                self.input_frame.assistant, self.input_frame.thread_process_message,
                self.model_vision, self.model_vision_floating_var, self)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

    def set_name(self, name):
        self.name = name
        self.logo_label.configure(text=name)

    def clear_chat(self):
        current_tab = self.tabview.get()  # Lấy tên tab hiện tại
        if current_tab in self.scrollable_frames:
            scrollable_frame = self.scrollable_frames[current_tab]
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

    @staticmethod
    def on_mousewheel(_, scrollable_frame, direction):
        scrollable_frame._parent_canvas.yview_scroll(direction, "units")

    def bind_scroll_events(self, tabview, scrollable_frames):
        current_tab = tabview.get()  # Lấy tab hiện tại
        scrollable_frame = scrollable_frames[current_tab]  # Tìm khung cuộn tương ứng với tab
        if platform.system() == 'Linux':
            # Ràng buộc cuộn chuột cho Linux
            scrollable_frame.bind_all("<Button-4>", lambda event: self.on_mousewheel(event, scrollable_frame, -1))
            scrollable_frame.bind_all("<Button-5>", lambda event: self.on_mousewheel(event, scrollable_frame, 1))
        else:
            # Ràng buộc cuộn chuột cho các hệ điều hành khác
            scrollable_frame.bind_all("<MouseWheel>", lambda event: self.on_mousewheel(event,
                                                                                       scrollable_frame,
                                                                                       -1 if event.delta > 0 else 1))


if __name__ == "__main__":
    app = App()
    app.mainloop()
