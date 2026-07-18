import io
import re
import threading
import socket
import os
import base64

from socket import AF_INET, SOCK_STREAM

from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkScrollableFrame, CTkImage,
    set_appearance_mode, get_appearance_mode
)

from tkinter import filedialog
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        self.MENU_MIN_WIDTH = 40
        self.MENU_MAX_WIDTH = 200

        self.geometry("700x500")
        self.title("Better viber and telegram")
        self.username = "User"

        self.menu_frame = CTkFrame(self, width=self.MENU_MIN_WIDTH, height=400)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False
        self.speed_animate_menu = 0
        self.menu_widgets = []

        self.btn = CTkButton(self, text='>', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)

        self.status_label = CTkLabel(self, text="🔴 Відключено", text_color="red")
        self.status_label.place(x=10, y=470)

        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=self.menu_frame.winfo_width(), y=0)

        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.open_img_button = CTkButton(self, text='📁', width=50, height=40, command=self.open_image)

        self.adaptive_ui()

        try:
            self.sock = socket.socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            threading.Thread(target=self.recv_message, daemon=True).start()
            self.status_label.configure(text="🟢 Онлайн", text_color="green")
        except Exception as e:
            self.add_message(f"Не вдалося підключитися: {e}")
            if hasattr(self, "sock"):
                self.sock.close()
                del self.sock

    def toggle_show_menu(self):
        self.is_show_menu = not self.is_show_menu
        self.speed_animate_menu = 20 if self.is_show_menu else -20
        self.btn.configure(text='◀' if self.is_show_menu else '▶')
        self.show_menu()

    def show_menu(self):
        current = self.menu_frame.winfo_width()
        new_width = current + self.speed_animate_menu

        new_width = max(self.MENU_MIN_WIDTH, min(self.MENU_MAX_WIDTH, new_width))
        self.menu_frame.configure(width=new_width)

        if (self.is_show_menu and new_width < self.MENU_MAX_WIDTH) or \
           (not self.is_show_menu and new_width > self.MENU_MIN_WIDTH):
            self.after(10, self.show_menu)

    def adaptive_ui(self):
        menu_w = self.menu_frame.winfo_width()
        win_w = self.winfo_width()
        win_h = self.winfo_height()

        self.chat_field.place(x=menu_w, y=0)
        self.chat_field.configure(width=win_w - menu_w - 20, height=win_h - 120)

        self.message_entry.place(x=menu_w + 10, y=win_h - 100)
        self.message_entry.configure(width=max(100, win_w - menu_w - 120))
        self.send_button.place(x=win_w - 90, y=win_h - 100)
        self.open_img_button.place(x=win_w - 150, y=win_h - 100)

        self.after(100, self.adaptive_ui)

    def add_message(self, message, img=None):
        frame = CTkFrame(self.chat_field)
        frame.pack(pady=5, anchor='w', padx=5)

        if img:
            CTkLabel(frame, text=message, image=img, compound='top').pack()
        else:
            CTkLabel(frame, text=message).pack()

    def replace_emoji(self, message: str) -> str:
        emoji_map = {
            ":)": "😂",
            ":(": "😞",
            "<3": "❤️",
            ":D": "😀",
            ";)": "😉"
        }
        for k, v in emoji_map.items():
            message = message.replace(k, v)
        return message

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return

        message = self.replace_emoji(message)
        self.add_message(f"{self.username}: {message}")

        if hasattr(self, "sock"):
            try:
                self.sock.send(f"TEXT@{self.username}@{message}\n".encode("utf-8"))
            except Exception as e:
                print(e)

        self.message_entry.delete(0, "end")

    def recv_message(self):
        buffer = ""
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break

                buffer += chunk.decode("utf-8", errors="ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.after(0, lambda l=line: self.handle_line(l.strip()))

        except Exception as e:
            print("Recv error:", e)

        finally:
            if hasattr(self, "sock"):
                self.sock.close()
                del self.sock
                self.after(0, lambda: self.add_message("🔴 Відключено"))

    def handle_line(self, line: str):
        if not line:
            return

        parts = line.split("@", 3)

        if parts[0] == "TEXT" and len(parts) >= 3:
            self.add_message(f"{parts[1]}: {parts[2]}")

        elif parts[0] == "IMAGE" and len(parts) >= 4:
            try:
                img_data = base64.b64decode(parts[3])
                img = Image.open(io.BytesIO(img_data))

                ctk_img = CTkImage(light_image=img, size=(200, 200))

                if not hasattr(self, "images"):
                    self.images = []
                self.images.append(ctk_img)

                self.add_message(f"{parts[1]} надіслав фото", img=ctk_img)

            except Exception as e:
                self.add_message(f"Помилка: {e}")

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return

        try:
            with open(file_name, 'rb') as f:
                data = base64.b64encode(f.read()).decode()

            name = os.path.basename(file_name)

            if hasattr(self, "sock"):
                self.sock.send(f"IMAGE@{self.username}@{name}@{data}\n".encode())

            img = Image.open(file_name)
            ctk_img = CTkImage(light_image=img, size=(200, 200))
            self.add_message(f"{self.username}: {name}", img=ctk_img)

        except Exception as e:
            self.add_message(f"Помилка: {e}")


win = MainWindow()
win.mainloop()