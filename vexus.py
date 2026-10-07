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

# --- ФУНКЦИИ ШИФРОВАНИЯ (AES-GCM / Fernet) ---
def generate_key(password: str) -> bytes:
    salt = b'fixed_salt_for_simplicity_123'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_text(text: str, password: str) -> str:
    if not text: return ""
    try:
        key = generate_key(password)
        f = Fernet(key)
        return f.encrypt(text.encode()).decode()
    except:
        return "[Ошибка шифрования]"

def decrypt_text(cipher_text: str, password: str) -> str:
    if not cipher_text: return ""
    try:
        key = generate_key(password)
        f = Fernet(key)
        return f.decrypt(cipher_text.encode()).decode()
    except:
        return "[Зашифрованное сообщение — неверный ключ]"

# --- НАСТРОЙКА ИНТЕРФЕЙСА ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

bg_color = "#182533" if st.session_state.theme == "dark" else "#ffffff"
text_color = "#ffffff" if st.session_state.theme == "dark" else "#000000"
sidebar_color = "#131e2b" if st.session_state.theme == "dark" else "#f1f1f1"
msg_user_color = "#2b5278" if st.session_state.theme == "dark" else "#effdde"
msg_other_color = "#182533" if st.session_state.theme == "dark" else "#f1f5f9"
time_color = "#a2b5c7" if st.session_state.theme == "dark" else "#707070"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_color}; }}
    .chat-bubble {{
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        max-width: 75%;
        display: inline-block;
        font-family: sans-serif;
        position: relative;
    }}
    .my-msg-container {{ text-align: right; width: 100%; }}
    .other-msg-container {{ text-align: left; width: 100%; }}
    .my-msg {{ background-color: {msg_user_color}; color: {text_color}; border-bottom-right-radius: 2px; text-align: left; }}
    .other-msg {{ background-color: {msg_other_color}; color: {text_color}; border-bottom-left-radius: 2px; }}
    .msg-author {{ font-size: 0.8rem; color: #8293a4; margin-bottom: 2px; }}
    .msg-time {{ font-size: 0.7rem; color: {time_color}; text-align: right; margin-top: 5px; }}
    .chat-image {{ max-width: 100%; border-radius: 10px; margin-top: 5px; display: block; }}
    </style>
""", unsafe_allow_html=True)

if "nickname" not in st.session_state: st.session_state.nickname = ""
if "active_chat" not in st.session_state: st.session_state.active_chat = "Общий чат"
if "room_password" not in st.session_state: st.session_state.room_password = "default_secure_pass"

headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

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
    # 1. БОКОВАЯ ПАНЕЛЬ
    with st.sidebar:
        st.subheader(f"👤 @{st.session_state.nickname}")
        
        theme_toggle = st.toggle("🌙 Темная тема", value=(st.session_state.theme == "dark"))
        new_theme = "dark" if theme_toggle else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()
            
        st.divider()
        
        st.markdown("### 🔍 Поиск чатов")
        search_user = st.text_input("Введи ник пользователя:", placeholder="например: ivan").strip().lower()
        
        chats_list = ["Общий чат"]
        if search_user and search_user != st.session_state.nickname:
            private_chat_name = f"🔒 чат: " + "-".join(sorted([st.session_state.nickname, search_user]))
            chats_list.append(private_chat_name)
            
        st.markdown("### 💬 Мои Диалоги")
        for chat in chats_list:
            display_name = "🌍 Общий чат" if chat == "Общий чат" else f"👤 @{search_user} (Приватный)"
            if st.button(display_name, key=f"btn_{chat}", use_container_width=True):
                st.session_state.active_chat = chat
                st.rerun()
                
        st.divider()
        if "🔒" in st.session_state.active_chat:
            st.markdown("### 🔑 Секретный ключ")
            st.session_state.room_password = st.text_input("Пароль шифрования:", value=st.session_state.room_password, type="password")
            st.caption("Ключи шифрования у вас с другом должны совпадать!")

        if st.button("Выйти из аккаунта", use_container_width=True):
            st.session_state.nickname = ""
            st.rerun()

    # 2. ОСНОВНОЕ ОКНО ЧАТА
    display_title = "🌍 Общий чат" if st.session_state.active_chat == "Общий чат" else f"👤 Приватный диалог"
    st.subheader(display_title)

    # Функция отправки
    def send_msg():
        msg_text = st.session_state.msg_input.strip()
        img_file = st.session_state.img_uploader
        
        image_base64 = ""
        
        # Если прикрепили картинку, переводим ее в текст Base64
        if img_file is not None:
            bytes_data = img_file.getvalue()
            image_base64 = base64.b64encode(bytes_data).decode()

        if msg_text or image_base64:
            try:
                # Если чат приватный — шифруем и текст, и картинку
                if "🔒" in st.session_state.active_chat:
                    final_text = encrypt_text(msg_text, st.session_state.room_password) if msg_text else ""
                    final_image = encrypt_text(image_base64, st.session_state.room_password) if image_base64 else ""
                else:
                    final_text = msg_text
                    final_image = image_base64
                    
                post_url = f"{URL}/rest/v1/messages"
                data = {
                    "sender": st.session_state.nickname, 
                    "text": final_text,
                    "image_url": final_image, # Колонку image_url мы используем под Base64 код картинки
                    "sender_room": st.session_state.active_chat
                }
                res = requests.post(post_url, headers=headers, json=data)
                if res.status_code >= 400:
                    st.error(f"Ошибка отправки: {res.text}")
                else:
                    st.session_state.msg_input = ""
            except Exception as e:
                st.error(f"Ошибка: {e}")

    # Интерфейс ввода ТГ стиля (Текст + Картинка под одной кнопкой)
    with st.form(key="send_form", clear_on_submit=True):
        st.text_input("Напишите сообщение...", key="msg_input")
        st.file_uploader("Прикрепить картинку (PNG/JPG)", type=["png", "jpg", "jpeg"], key="img_uploader")
        submit_button = st.form_submit_button(label="Отправить сообщение", on_click=send_msg)

    st.divider()

    # Отображение сообщений
    try:
        get_url = f"{URL}/rest/v1/messages?select=*&order=id.desc&limit=40"
        response = requests.get(get_url, headers=headers)
        
        if response.status_code == 200:
            messages = response.json()
            filtered_messages = [m for m in messages if m.get("sender_room", "Общий чат") == st.session_state.active_chat]

            if filtered_messages:
                for msg in reversed(filtered_messages):
                    raw_text = msg.get('text', '')
                    raw_img = msg.get('image_url', '')
                    
                    # Парсинг времени (перевод из UTC в UTC+3 / Кишинев-Киев для примера, можно настроить +3 часа)
                    # Supabase присылает строку вида "2024-03-31T12:00:00+00:00"
                    try:
                        clean_time_str = msg['created_at'].split('.')[0].replace('T', ' ')
                        utc_time = datetime.strptime(clean_time_str, "%Y-%m-%d %H:%M:%S")
                        local_time = utc_time + timedelta(hours=3) # Меняй цифру под свой часовой пояс
                        formatted_time = local_time.strftime("%H:%M")
                    except:
                        formatted_time = "--:--"

                    # Расшифровка
                    if "🔒" in st.session_state.active_chat:
                        display_text = decrypt_text(raw_text, st.session_state.room_password) if raw_text else ""
                        display_img = decrypt_text(raw_img, st.session_state.room_password) if raw_img else ""
                    else:
                        display_text = raw_text
                        display_img = raw_img

                    is_me = msg['sender'] == st.session_state.nickname
                    container_class = "my-msg-container" if is_me else "other-msg-container"
                    bubble_class = "my-msg" if is_me else "other-msg"
                    
                    # Рендеринг баббла
                    img_html = f'<img src="data:image/png;base64,{display_img}" class="chat-image">' if (display_img and "[Зашифровано" not in display_img) else ""
                    text_html = f'<div>{display_text}</div>' if display_text else ""
                    
                    st.markdown(f"""
                        <div class="{container_class}">
                            <div class="msg-author">@{msg['sender']}</div>
