import customtkinter as ctk
from supabase import create_client, Client
import threading
import time

# --- НАЛАШТУВАННЯ SUPABASE ---
URL = "https://dqpdfreewxzefsaejmob.supabase.co/rest/v1/"
KEY = "sb_publishable_XBWFiWdA9Eg2msn3T04XkQ_oKX69lpG"
supabase: Client = create_client(URL, KEY)

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("vexus")
        self.geometry("450x600")
        ctk.set_appearance_mode("dark")
        
        self.nickname = ""
        self.last_message_id = 0
        
        # Вікно входу для нікнейму
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(fill="both", expand=True, padx=20,专padx=20, pady=20)
        
        self.lbl = ctk.CTkLabel(self.login_frame, text="Введіть ваш нікнейм:", font=("Arial", 16))
        self.lbl.pack(pady=20)
        
        self.entry_nick = ctk.CTkEntry(self.login_frame, placeholder_text="Мій нік...", width=200)
        self.entry_nick.pack(pady=10)
        
        self.btn_login = ctk.CTkButton(self.login_frame, text="Увійти в чат", command=self.start_chat)
        self.btn_login.pack(pady=20)
        
        # Головне вікно чату (спочатку приховане)
        self.chat_frame = ctk.CTkFrame(self)
        
        self.txt_area = ctk.CTkTextbox(self.chat_frame, width=400, height=450, state="disabled", font=("Arial", 14))
        self.txt_area.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.input_frame = ctk.CTkFrame(self.chat_frame)
        self.input_frame.pack(padx=10, pady=5, fill="x")
        
        self.entry_msg = ctk.CTkEntry(self.input_frame, placeholder_text="Напишіть повідомлення...", width=300)
        self.entry_msg.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_msg.bind("<Return>", lambda event: self.send_message())
        
        self.btn_send = ctk.CTkButton(self.input_frame, text="=>", width=50, command=self.send_message)
        self.btn_send.pack(side="right", padx=5)

    def start_chat(self):
        nick = self.entry_nick.get().strip()
        if nick:
            self.nickname = nick
            self.login_frame.pack_forget()
            self.chat_frame.pack(fill="both", expand=True)
            
            # Запуск фонового потоку для оновлення повідомлень
            threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self):
        msg_text = self.entry_msg.get().strip()
        if msg_text:
            self.entry_msg.delete(0, "end")
            # Відправка в базу даних Supabase
            try:
                supabase.table("messages").insert({"sender": self.nickname, "text": msg_text}).execute()
            except Exception as e:
                print("Помилка відправки:", e)

    def receive_messages(self):
        while True:
            try:
                # Запитуємо нові повідомлення, які мають ID більше, ніж ми вже бачили
                response = supabase.table("messages").select("*").gt("id", self.last_message_id).order("id").execute()
                data = response.data
                
                if data:
                    self.txt_area.configure(state="normal")
                    for msg in data:
                        self.txt_area.insert("end", f"[{msg['sender']}]: {msg['text']}\n")
                        self.last_message_id = msg['id']
                    self.txt_area.configure(state="disabled")
                    self.txt_area.see("end") # Прокрутка вниз
            except Exception as e:
                print("Помилка отримання:", e)
                
            time.sleep(1) # Перевірка оновлень щосекунди

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
