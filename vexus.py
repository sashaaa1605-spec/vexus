import streamlit as st
import requests
import time
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- НАСТРОЙКИ SUPABASE ---
URL = "https://dqpdfreewxzefsaejmob.supabase.co"
KEY = "sb_publishable_XBWFiWdA9Eg2msn3T04XkQ_oKX69lpG"
# --- ШИФРОВАНИЕ ---
def generate_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'salt_123', iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_text(text: str, password: str) -> str:
    if not text: return ""
    try:
        return Fernet(generate_key(password)).encrypt(text.encode()).decode()
    except:
        return "[Ошибка]"

def decrypt_text(cipher_text: str, password: str) -> str:
    if not cipher_text: return ""
    try:
        return Fernet(generate_key(password)).decrypt(cipher_text.encode()).decode()
    except:
        return "[Зашифровано — неверный ключ]"

# --- ИНТЕРФЕЙС И ТЕМЫ ---
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "nickname" not in st.session_state: st.session_state.nickname = ""
if "active_chat" not in st.session_state: st.session_state.active_chat = "Общий чат"
if "room_password" not in st.session_state: st.session_state.room_password = "default_secure_pass"

headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

# Темы оформления
bg = "#182533" if st.session_state.theme == "dark" else "#ffffff"
tc = "#ffffff" if st.session_state.theme == "dark" else "#000000"
st.markdown(f"<style>.stApp {{background-color: {bg}; color: {tc};}}</style>", unsafe_allow_html=True)

# --- ОКНО ВХОДА ---
if not st.session_state.nickname:
    st.title("💬 vexus v3.0")
    nick_input = st.text_input("Введите ваш никнейм для входа:", max_chars=15)
    if st.button("Войти в мессенджер"):
        if nick_input.strip():
            st.session_state.nickname = nick_input.strip().lower()
            st.rerun()
        else:
            st.error("Никнейм не может быть пустым!")

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
else:
    with st.sidebar:
        st.subheader(f"👤 @{st.session_state.nickname}")
        theme_toggle = st.toggle("🌙 Темная тема", value=(st.session_state.theme == "dark"))
        st.session_state.theme = "dark" if theme_toggle else "light"
        
        st.divider()
        st.markdown("### 🔍 Поиск чатов")
        search_user = st.text_input("Введи ник кента:", placeholder="например: ivan").strip().lower()
        
        chats_list = ["Общий чат"]
        if search_user and search_user != st.session_state.nickname:
            chats_list.append(f"🔒 чат: " + "-".join(sorted([st.session_state.nickname, search_user])))
            
        st.markdown("### 💬 Мои Диалоги")
        for chat in chats_list:
            name = "🌍 Общий чат" if chat == "Общий chat" or chat == "Общий чат" else f"👤 @{search_user} (Приватный)"
            if st.button(name, key=f"b_{chat}", use_container_width=True):
                st.session_state.active_chat = chat
                st.rerun()
                
        st.divider()
        if "🔒" in st.session_state.active_chat:
            st.markdown("### 🔑 Шифрование")
            st.session_state.room_password = st.text_input("Пароль чата:", value=st.session_state.room_password, type="password")
            st.caption("Пароли у вас с другом должны совпадать!")

        if st.button("Выйти из аккаунта", use_container_width=True):
            st.session_state.nickname = ""
            st.rerun()

    st.subheader("🌍 Общий чат" if "🔒" not in st.session_state.active_chat else "👤 Приватный диалог")

    # Функция отправки
    def send_msg():
        msg_text = st.session_state.msg_input.strip()
        img_file = st.session_state.img_uploader
        img_b64 = ""
        
        if img_file is not None:
            img_b64 = base64.b64encode(img_file.getvalue()).decode()

        if msg_text or img_b64:
            try:
                if "🔒" in st.session_state.active_chat:
                    f_text = encrypt_text(msg_text, st.session_state.room_password) if msg_text else ""
                    f_img = encrypt_text(img_b64, st.session_state.room_password) if img_b64 else ""
                else:
                    f_text = msg_text
                    f_img = img_b64
                    
                data = {
                    "sender": st.session_state.nickname, 
                    "text": f_text, 
                    "image_url": f_img, 
                    "sender_room": st.session_state.active_chat
                }
                requests.post(f"{URL}/rest/v1/messages", headers=headers, json=data)
                st.session_state.msg_input = ""
            except:
                pass

    with st.form(key="send_form", clear_on_submit=True):
        st.text_input("Напишите сообщение...", key="msg_input")
        st.file_uploader("Картинка (PNG/JPG)", type=["png", "jpg", "jpeg"], key="img_uploader")
        st.form_submit_button(label="Отправить", on_click=send_msg)

    st.divider()

    # Отображение сообщений
    try:
        res = requests.get(f"{URL}/rest/v1/messages?select=*&order=id.desc&limit=40", headers=headers)
        if res.status_code == 200:
            filtered = [m for m in res.json() if m.get("sender_room", "Общий чат") == st.session_state.active_chat]
            
            for msg in reversed(filtered):
                try:
                    t_part = msg['created_at'].split('.')[0].replace('T', ' ')
                    dt = datetime.strptime(t_part, "%Y-%m-%d %H:%M:%S") + timedelta(hours=3)
                    f_time = dt.strftime("%H:%M")
                except:
                    f_time = "--:--"

                if "🔒" in st.session_state.active_chat:
                    d_text = decrypt_text(msg.get('text', ''), st.session_state.room_password)
                    d_img = decrypt_text(msg.get('image_url', ''), st.session_state.room_password)
                else:
                    d_text = msg.get('text', '')
                    d_img = msg.get('image_url', '')

                # Вывод сообщений элементами Streamlit (чтобы избежать багов с HTML)
                with st.chat_message("user" if msg['sender'] == st.session_state.nickname else "assistant"):
                    st.write(f"**@{msg['sender']}** в {f_time}")
                    if d_text: st.write(d_text)
                    if d_img and "[Зашифровано" not in d_img:
                        st.image(base64.b64decode(img_b64 if 'img_b64' in locals() else d_img.encode()))
        else:
            st.error("Ошибка подключения к базе")
    except:
        pass

    time.sleep(2.5)
    st.rerun()
