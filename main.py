import os
import base64
import io
import threading
import socket
from socket import AF_INET, SOCK_STREAM

from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkScrollableFrame, CTkImage,
    set_appearance_mode, get_appearance_mode
)
from tkinter import filedialog, END
from PIL import Image

class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        # Константи меню
        self.MENU_MIN_WIDTH = 40
        self.MENU_MAX_WIDTH = 200

        self.geometry('700x500')
        self.title("Better viber and telegram")
        self.username = "User"
        self.themes = [
            {"name": "Dark Blue", "msg_color": "#1f6aa5", "bg_color": "#1a1a1a"},
            {"name": "Green", "msg_color": "#2ecc71", "bg_color": "#1a1a1a"},
            {"name": "Purple", "msg_color": "#9b59b6", "bg_color": "#1a1a1a"},
            {"name": "Red", "msg_color": "#e74c3c", "bg_color": "#1a1a1a"},
            {"name": "Orange", "msg_color": "#f39c12", "bg_color": "#1a1a1a"},
        ]

        self.current_theme_index = 0
        self.current_theme = self.themes[self.current_theme_index]

        # Меню
        self.menu_frame = CTkFrame(self, width=self.MENU_MIN_WIDTH, height=400)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False  # параметр який відслідковує чи відкрите або закрите меню налаштуваннь
        self.speed_animate_menu = 0
        self.menu_widgets = []  # список віджетів, які ми додаємо в меню

        # Кнопка відкриття меню
        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)

        # Статус
        self.status_label = CTkLabel(self, text="🔴 Відключено", text_color="red")
        self.status_label.place(x=10, y=self.winfo_height() - 20)

        # Основне поле чату, там де виводяться повідомлення користувачів
        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=self.menu_frame.winfo_width(), y=0)
        self.chat_field.configure(fg_color=self.current_theme["bg_color"])

        # Поле введення та кнопки
        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.open_img_button = CTkButton(self, text='📂', width=50, height=40, command=self.open_image)

        # Адаптивне розташування
        self.adaptive_ui()

        # Демонстрація (тільки якщо є файл)
        try:
            if os.path.exists('1.jpeg'):
                demo_img = CTkImage(light_image=Image.open('1.jpeg'), size=(300, 300))
                self.add_message("Демонстрація відображення зображення:", img=demo_img)
        except Exception:
            pass

        # Спроба підключитись до сервера
        try:
            self.sock = socket.socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднав(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
            self.status_label.configure(text="🟢 Онлайн", text_color="green")
        except Exception as e:
            # якщо не підключилось — лише показати повідомлення
            self.add_message(f"Не вдалося підключитися до сервера: {e}")
            if hasattr(self, "sock"):
                try:
                    self.sock.close()
                except:
                    pass
                del self.sock

    # ----------------- Меню -----------------
    def toggle_show_menu(self):
        if self.is_show_menu:  # якщо меню відкрите → закриваємо
            self.is_show_menu = False
            self.speed_animate_menu = -20
            self.btn.configure(text='▶️')
            self.show_menu()
        else:  # якщо меню закрите → відкриваємо
            self.is_show_menu = True
            self.speed_animate_menu = 20
            self.btn.configure(text='◀️')
            # Створюємо елементи меню (тільки якщо ще не створені)
            if not self.menu_widgets:
                # Ім'я
                lbl = CTkLabel(self.menu_frame, text='Імʼя')
                lbl.pack(pady=(30, 5))
                self.menu_widgets.append(lbl)

                self.entry_name = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
                self.entry_name.pack(pady=(0, 10))
                self.menu_widgets.append(self.entry_name)

                self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
                self.save_button.pack(pady=(0, 10))
                self.menu_widgets.append(self.save_button)

                self.save_chat_btn = CTkButton(self.menu_frame, text="💾 Зберегти чат", command=self.save_chat_history)
                self.save_chat_btn.pack(pady=5)
                self.menu_widgets.append(self.save_chat_btn)

                self.clear_btn = CTkButton(self.menu_frame, text="🧹 Очистити чат", command=self.clear_chat)
                self.clear_btn.pack(pady=5)
                self.menu_widgets.append(self.clear_btn)

                self.theme_button = CTkButton(self.menu_frame, text="🌓 Тема", command=self.toggle_theme)
                self.theme_button.pack(pady=10)
                self.menu_widgets.append(self.theme_button)

            self.show_menu()

    def show_menu(self):
        # анімація ширини меню
        current = self.menu_frame.winfo_width()
        new_width = current + self.speed_animate_menu
        # обрізка
        if new_width < self.MENU_MIN_WIDTH:
            new_width = self.MENU_MIN_WIDTH
        if new_width > self.MENU_MAX_WIDTH:
            new_width = self.MENU_MAX_WIDTH

        self.menu_frame.configure(width=new_width)

        # продовжити анімацію, якщо потрібно
        if self.is_show_menu and new_width < self.MENU_MAX_WIDTH:
            self.after(10, self.show_menu)
        elif (not self.is_show_menu) and new_width > self.MENU_MIN_WIDTH:
            self.after(10, self.show_menu)
        else:
            # якщо меню закрилося — знищуємо віджети
            if not self.is_show_menu:
                for w in self.menu_widgets:
                    try:
                        w.destroy()
                    except:
                        pass
                self.menu_widgets = []

    def save_name(self):
        if hasattr(self, "entry_name"):
            new_name = self.entry_name.get().strip()
            if new_name:
                self.username = new_name
                self.add_message(f"Ваш новий нік: {self.username}")

    def toggle_theme(self):
        self.current_theme_index += 1
        if self.current_theme_index >= len(self.themes):
            self.current_theme_index = 0

        self.current_theme = self.themes[self.current_theme_index]

        self.add_message(f"🎨 Тема змінена на: {self.current_theme['name']}")
    # ----------------- UI/розміщення -----------------
    def adaptive_ui(self):
        # Оновлюємо розміри і позиції елементів
        menu_w = self.menu_frame.winfo_width() or self.MENU_MIN_WIDTH
        win_w = max(self.winfo_width(), 300)
        win_h = max(self.winfo_height(), 200)

        # Чат займає праву частину
        self.chat_field.place(x=menu_w, y=0)
        self.chat_field.configure(fg_color=self.current_theme["bg_color"])
        self.chat_field.configure(width=win_w - menu_w - 20, height=win_h - 200)

        # Кнопки знизу
        self.send_button.place(x=win_w - 250, y=win_h - 170)
        self.open_img_button.place(x=win_w - 310, y=win_h - 170)
        self.message_entry.place(x=menu_w + 10, y=win_h - 170)
        self.message_entry.configure(width=500)
        # Статус зліва внизу
        try:
            self.status_label.place(x=10, y=win_h - 170)
        except:
            pass
        self.after(100, self.adaptive_ui)
    # ----------------- Робота з повідомленнями -----------------
    def add_message(self, message, img=None):
        # Створюємо рамку повідомлення і потім лейбл
        message_frame = CTkFrame(
            self.chat_field,
            fg_color=self.current_theme["msg_color"],
            corner_radius=6
        )
        message_frame.pack(pady=5, anchor='w', padx=5)
        wrapleng_size = self.winfo_width() - self.menu_frame.winfo_width() - 80
        if img is None:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size,
                     text_color='white', justify='left').pack(padx=10, pady=5)
        else:
            # img очікується як CTkImage
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size,
                     text_color='white', image=img, compound='top',
                     justify='left').pack(padx=10, pady=5)

    def clear_chat(self):
        for widget in self.chat_field.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        self.add_message("🧹 Чат очищено!")

    def save_chat_history(self):
        try:
            with open("chat_history.txt", "w", encoding="utf-8") as f:
                for widget in self.chat_field.winfo_children():
                    # шукаємо CTkLabel всередині кожного message_frame
                    for sub in widget.winfo_children():
                        try:
                            text = sub.cget("text")
                        except Exception:
                            text = None
                        if text:
                            f.write(text + "\n")
            self.add_message("✅ Історію чату збережено у файл chat_history.txt")
        except Exception as e:
            self.add_message(f"Помилка при збереженні історії: {e}")

    def replace_emojis(self, message: str) -> str:
        emoji_map = {
            ":)": "😊",
            ":(": "☹️",
            "<3": "❤️",
            ":D": "😄",
            ";)": "😉"
        }
        for k, v in emoji_map.items():
            message = message.replace(k, v)
        return message

    def send_message(self):
        raw = self.message_entry.get().strip()
        if not raw:
            # нічого не відправляємо
            return
        message = self.replace_emojis(raw)
        self.add_message(f"{self.username}: {message}")

        data = f"TEXT@{self.username}@{message}\n"
        try:
            if hasattr(self, "sock") and self.sock:
                self.sock.sendall(data.encode('utf-8'))
        except Exception:
            # ігноруємо помилку відправки (можна логувати)
            pass
        finally:
            # очищаємо поле вводу
            try:
                self.message_entry.delete(0, END)
            except:
                pass

    # ----------------- Мережа -----------------
    def recv_message(self):
        buffer = ""
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
        except Exception:
            pass
        finally:
            try:
                self.sock.close()
            except:
                pass
            if hasattr(self, "sock"):
                del self.sock
            self.add_message("🔴 Втрачене з'єднання з сервером")
            self.status_label.configure(text="🔴 Відключено", text_color="red")

    def handle_line(self, line: str):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0].upper()

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]
                try:
                    img_data = base64.b64decode(b64_img)
                    pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                    ctk_img = CTkImage(light_image=pil_img, size=(300, 300))
                    self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
                except Exception as e:
                    self.add_message(f"Помилка відображення зображення: {e}")
        else:
            # інші повідомлення — показуємо як є
            self.add_message(line)
    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            try:
                if hasattr(self, "sock") and self.sock:
                    self.sock.sendall(data.encode('utf-8'))
            except Exception:
                pass
            pil = Image.open(file_name).convert("RGBA")
            ctk_img = CTkImage(light_image=pil, size=(300, 300))
            self.add_message(f"{self.username} (локально): {short_name}", img=ctk_img)
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")
win = MainWindow()
win.mainloop()
