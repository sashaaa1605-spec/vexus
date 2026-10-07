import streamlit as st
import requests
import time
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- НАСТРОЙКИ SUPABASE ---
URL = "https://dqpdfreewxzefsaejmob.supabase.co"
KEY = "sb_publishable_XBWFiWdA9Eg2msn3T04XkQ_oKX69lpG"

# --- ФУНКЦИИ ШИФРОВАНИЯ (AES-GCM / Fernet) ---
def generate_key(password: str) -> bytes:
    # Создаем криптографический ключ на основе пароля чата
    salt = b'fixed_salt_for_simplicity_123' # В реальных системах соль уникальна
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
        return "[Зашифрованное сообщение — неверный ключ комнаты]"

# --- НАСТРОЙКА ИНТЕРФЕЙСА ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Кастомные стили для дизайна в стиле Telegram (поддержка тем)
bg_color = "#182533" if st.session_state.theme == "dark" else "#ffffff"
text_color = "#ffffff" if st.session_state.theme == "dark" else "#000000"
sidebar_color = "#131e2b" if st.session_state.theme == "dark" else "#f1f1f1"
msg_user_color = "#2b5278" if st.session_state.theme == "dark" else "#effdde"
msg_other_color = "#182533" if st.session_state.theme == "dark" else "#f1f5f9"

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
    }}
    .my-msg-container {{ text-align: right; width: 100%; }}
    .other-msg-container {{ text-align: left; width: 100%; }}
    .my-msg {{ background-color: {msg_user_color}; color: {text_color}; border-bottom-right-radius: 2px; text-align: left; }}
    .other-msg {{ background-color: {msg_other_color}; color: {text_color}; border-bottom-left-radius: 2px; }}
    .msg-author {{ font-size: 0.8rem; color: #8293a4; margin-bottom: 2px; }}
    </style>
""", unsafe_allow_html=True)

# Инициализация сессии
if "nickname" not in st.session_state: st.session_state.nickname = ""
if "active_chat" not in st.session_state: st.session_state.active_chat = "Общий чат"
if "room_password" not in st.session_state: st.session_state.room_password = "default_secure_pass"

headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

# --- ОКНО ВХОДА ---
if not st.session_state.nickname:
    st.title("💬 ТГ Мессенджер v2.0")
    with st.get_compiler_canvas() if hasattr(st, 'get_compiler_canvas') else st.container():
        nick_input = st.text_input("Введите ваш никнейм для входа:", max_chars=15)
        if st.button("Войти в мессенджер"):
            if nick_input.strip():
                st.session_state.nickname = nick_input.strip().lower()
                st.rerun()
            else:
                st.error("Никнейм не может быть пустым!")

# --- ГЛАВНЫЙ ИНТЕРФЕЙС (ТГ СТИЛЬ) ---
else:
    # 1. БОКОВАЯ ПАНЕЛЬ (Сайдбар как список чатов в ТГ)
    with st.sidebar:
        st.subheader(f"👤 @{st.session_state.nickname}")
        
        # Переключатель темы
        theme_toggle = st.toggle("🌙 Темная тема", value=(st.session_state.theme == "dark"))
        new_theme = "dark" if theme_toggle else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()
            
        st.divider()
        
        # Поиск людей / Создание чатов
        st.markdown("### 🔍 Поиск чатов")
        search_user = st.text_input("Введи ник кента:", placeholder="например: ivan").strip().lower()
        
        chats_list = ["Общий чат"]
        if search_user and search_user != st.session_state.nickname:
            # Создаем уникальное имя чата для двоих (сортируем ники по алфавиту)
            private_chat_name = f"🔒 чат: " + "-".join(sorted([st.session_state.nickname, search_user]))
            chats_list.append(private_chat_name)
            
        # Кнопки выбора чата
        st.markdown("### 💬 Мои Диалоги")
        for chat in chats_list:
            display_name = "🌍 Общий чат" if chat == "Общий чат" else f"👤 @{search_user} (Приватный)"
            if st.button(display_name, key=f"btn_{chat}", use_container_width=True):
                st.session_state.active_chat = chat
                st.rerun()
                
        st.divider()
        # Ключ шифрования для комнат
        if "🔒" in st.session_state.active_chat:
            st.markdown("### 🔑 Секретный ключ")
            st.session_state.room_password = st.text_input(
                "Пароль шифрования чата:", 
                value=st.session_state.room_password, 
                type="password"
            )
            st.caption("У тебя и у кента этот пароль должен быть ОДИНАКОВЫМ, иначе сообщения не расшифруются.")

        if st.button("Выйти из аккаунта", use_container_width=True):
            st.session_state.nickname = ""
            st.rerun()

    # 2. ОСНОВНОЕ ОКНО ЧАТА
    display_title = "🌍 Общий чат" if st.session_state.active_chat == "Общий chat" else f"👤 Приватный диалог"
    st.subheader(display_title)
    st.caption(f"ID комнаты: {st.session_state.active_chat}")

    # Форма отправки сообщения
    def send_msg():
        msg_text = st.session_state.msg_input.strip()
        if msg_text:
            try:
                # Если чат приватный — шифруем текст перед отправкой в базу данных
                if "🔒" in st.session_state.active_chat:
                    final_text = encrypt_text(msg_text, st.session_state.room_password)
                else:
                    final_text = msg_text
                    
                post_url = f"{URL}/rest/v1/messages"
                # Записываем в колонку text зашифрованное сообщение, а в sender_room — id чата
                data = {
                    "sender": st.session_state.nickname, 
                    "text": final_text,
                    "sender_room": st.session_state.active_chat # Добавим фильтр по комнатам
                }
                res = requests.post(post_url, headers=headers, json=data)
                if res.status_code >= 400:
                    st.error(f"Ошибка отправки: {res.text}")
                else:
                    st.session_state.msg_input = ""
            except Exception as e:
                st.error(f"Ошибка: {e}")

    with st.form(key="send_form", clear_on_submit=True):
        st.text_input("Напишите сообщение...", key="msg_input")
        st.form_submit_button(label="Отправить", on_click=send_msg)

    st.divider()

    # Отображение сообщений
    try:
        get_url = f"{URL}/rest/v1/messages?select=*&order=id.desc&limit=60"
        response = requests.get(get_url, headers=headers)
        
        if response.status_code == 200:
            messages = response.json()
            # Фильтруем сообщения, которые принадлежат текущему чату
            # (если в базе нет колонки sender_room, мы временно фильтруем по логике кода, но лучше сделать SQL)
            filtered_messages = []
            for m in messages:
                # Старые сообщения без комнат отправляем в общий чат, новые — строго по комнатам
                room = m.get("sender_room", "Общий чат")
                if room == st.session_state.active_chat:
                    filtered_messages.append(m)

            if filtered_messages:
                for msg in reversed(filtered_messages):
                    raw_text = msg['text']
                    
                    # Если чат зашифрован — расшифровываем текст перед показом на экране
                    if "🔒" in st.session_state.active_chat:
                        display_text = decrypt_text(raw_text, st.session_state.room_password)
                    else:
                        display_text = raw_text

                    # Отрендерим красивые бабблы сообщений а-ля Telegram
                    is_me = msg['sender'] == st.session_state.nickname
                    container_class = "my-msg-container" if is_me else "other-msg-container"
                    bubble_class = "my-msg" if is_me else "other-msg"
                    
                    st.markdown(f"""
                        <div class="{container_class}">
                            <div class="msg-author">@{msg['sender']}</div>
                            <div class="chat-bubble {bubble_class}">{display_text}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Здесь пока нет сообщений...")
        else:
            st.error(f"Ошибка базы: {response.text}")
            
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")

    # Автообновление экрана
    time.sleep(2.5)
    st.rerun()
