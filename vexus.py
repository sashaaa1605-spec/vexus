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

# --- ШИФРОВАНИЕ ---
def generate_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'salt_123', iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_text(text: str, password: str) -> str:
    if not text: return ""
    try: return Fernet(generate_key(password)).encrypt(text.encode()).decode()
    except: return "[Ошибка]"

def decrypt_text(cipher_text: str, password: str) -> str:
    if not cipher_text: return ""
    try:
        if cipher_text.startswith("gAAAAA"):
            return Fernet(generate_key(password)).decrypt(cipher_text.encode()).decode()
        return cipher_text
    except: return "[Зашифровано — неверный ключ]"

# --- СЕССИЯ И ДИЗАЙН ---
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "nickname" not in st.session_state: st.session_state.nickname = ""
if "active_chat" not in st.session_state: st.session_state.active_chat = "Общий чат"
if "room_password" not in st.session_state: st.session_state.room_password = "default_secure_pass"
if "edit_profile" not in st.session_state: st.session_state.edit_profile = False

headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

# Красивые стили для бабблов сообщений (как в ТГ)
bg = "#182533" if st.session_state.theme == "dark" else "#ffffff"
tc = "#ffffff" if st.session_state.theme == "dark" else "#000000"
msg_self = "#2b5278" if st.session_state.theme == "dark" else "#effdde"
msg_other = "#202b36" if st.session_state.theme == "dark" else "#f1f5f9"

st.markdown(f"""
    <style>
    .stApp {{background-color: {bg}; color: {tc};}}
    .msg-box {{
        display: flex;
        align-items: flex-start;
        margin: 8px 0;
        padding: 8px 12px;
        border-radius: 12px;
        max-width: 85%;
        font-family: sans-serif;
    }}
    .msg-left {{ background-color: {msg_other}; margin-right: auto; }}
    .msg-right {{ background-color: {msg_self}; margin-left: auto; flex-direction: row-reverse; }}
    .msg-avatar {{
        width: 35px;
        height: 35px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 8px;
    }}
    .msg-body {{ display: flex; flex-direction: column; }}
    .msg-author {{ font-weight: bold; font-size: 0.85rem; color: #5288c1; margin-bottom: 2px; }}
    .msg-text {{ font-size: 0.95rem; line-height: 1.3; }}
    .chat-img {{ max-width: 100%; border-radius: 8px; margin-top: 5px; display: block; }}
    </style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ПРОФИЛЕЙ ---
def get_profile(nickname):
    try:
        res = requests.get(f"{URL}/rest/v1/profiles?nickname=eq.{nickname}", headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()
    except: pass
    return {}

def get_all_profiles_cached():
    try:
        res = requests.get(f"{URL}/rest/v1/profiles", headers=headers)
        if res.status_code == 200:
            return {p['nickname']: p.get('avatar_b64', '') for p in res.json() if 'nickname' in p}
    except: pass
    return {}

# --- ОКНО ВХОДА ---
if not st.session_state.nickname:
    st.title("💬 Vexus — Вход")
    email_input = st.text_input("Введите ваш Gmail:", placeholder="yourname@gmail.com").strip().lower()
    nick_input = st.text_input("Придумайте ваш никнейм в Vexus:", max_chars=15).strip().lower()
    
    if st.button("Войти / Зарегистрироваться", use_container_width=True):
        if not email_input or not nick_input: st.error("Заполните все поля!")
        elif "@" not in email_input: st.error("Введите корректный Gmail адрес!")
        else:
            try:
                res_email = requests.get(f"{URL}/rest/v1/profiles?email=eq.{email_input}", headers=headers).json()
                res_nick = requests.get(f"{URL}/rest/v1/profiles?nickname=eq.{nick_input}", headers=headers).json()
                existing_user = res_email if (isinstance(res_email, list) and len(res_email) > 0) else None
                
                if existing_user:
                    if existing_user.get('nickname') == nick_input:
                        st.session_state.user_email = email_input
                        st.session_state.nickname = nick_input
                        st.success("Успешный вход!")
                        st.rerun()
                    else: st.error("Этот Gmail уже привязан к другому никнейму!")
                else:
                    if res_nick and len(res_nick) > 0: st.error("Этот никнейм уже занят!")
                    else:
                        new_user = {"email": email_input, "nickname": nick_input}
                        requests.post(f"{URL}/rest/v1/profiles", headers=headers, json=new_user)
                        st.session_state.user_email = email_input
                        st.session_state.nickname = nick_input
                        st.success("Регистрация Успешна!")
                        st.rerun()
            except Exception as e: st.error(f"Ошибка авторизации: {e}")

# --- ГЛАВНЫЙ ИНТЕРФЕЙС VEXUS ---
else:
    my_prof = get_profile(st.session_state.nickname)
    
    with st.sidebar:
        st.title("💬 Vexus")
        if my_prof.get("banner_b64"): st.image(base64.b64decode(my_prof["banner_b64"]), use_container_width=True)
        if my_prof.get("avatar_b64"): st.image(base64.b64decode(my_prof["avatar_b64"]), width=80)
        st.subheader(f"👤 @{st.session_state.nickname}")
        st.caption(f"Status: {my_prof.get('status_text', 'No status')}")
        
        if st.button("⚙️ Настроить профиль", use_container_width=True):
            st.session_state.edit_profile = not st.session_state.edit_profile
            st.rerun()
            
        theme_toggle = st.toggle("🌙 Темная тема", value=(st.session_state.theme == "dark"))
        st.session_state.theme = "dark" if theme_toggle else "light"
        st.divider()
        
        st.markdown("### 🔍 Поиск кентов")
        search_user = st.text_input("Введи ник кента:", placeholder="например: ivan").strip().lower()
        chats_list = ["Общий чат"]
        if search_user and search_user != st.session_state.nickname:
            chats_list.append("🔒-" + "-".join(sorted([st.session_state.nickname, search_user])))
            
        st.markdown("### 💬 Мои Диалоги")
        for chat in chats_list:
            name = "🌍 Общий чат" if chat == "Общий чат" else f"👤 @{search_user} (Приватный)"
            if st.button(name, key=f"b_{chat}", use_container_width=True):
                st.session_state.active_chat = chat
                st.rerun()
                
        st.divider()
        if "🔒-" in st.session_state.active_chat:
            st.markdown("### 🔑 Шифрование")
            st.session_state.room_password = st.text_input("Пароль чата:", value=st.session_state.room_password, type="password")
        if st.button("Выйти из аккаунта", use_container_width=True):
            st.session_state.nickname = ""
            st.session_state.user_email = ""
            st.rerun()

    # --- ОКНО НАСТРОЙКИ ПРОФИЛЯ ---
    if st.session_state.edit_profile:
        st.subheader("⚙️ Кастомизация профиля Vexus")
        new_status = st.text_input("Твой статус:", value=my_prof.get("status_text", ""))
        new_ava = st.file_uploader("Загрузить аватарку (PNG/JPG):", type=["png", "jpg"])
        new_banner = st.file_uploader("Загрузить баннер профиля:", type=["png", "jpg"])
        
        if st.button("Сохранить изменения профиля"):
            up_data = {"status_text": new_status}
            if new_ava: up_data["avatar_b64"] = base64.b64encode(new_ava.getvalue()).decode()
            if new_banner: up_data["banner_b64"] = base64.b64encode(new_banner.getvalue()).decode()
            requests.patch(f"{URL}/rest/v1/profiles?nickname=eq.{st.session_state.nickname}", headers=headers, json=up_data)
            st.success("Профиль обновлен!")
            st.session_state.edit_profile = False
            st.rerun()

    # --- ОКНО ЧАТА ---
    else:
        is_private = "🔒-" in st.session_state.active_chat
        st.subheader("🌍 Общая лента Vexus" if not is_private else f"👤 Приватный диалог с @{search_user}")
        if is_private:
            kent_prof = get_profile(search_user)
            if kent_prof.get("status_text"): st.caption(f"ℹ️ Status: {kent_prof.get('status_text')}")

        def send_msg():
            msg_text = st.session_state.msg_input.strip()
            img_file = st.session_state.img_uploader
            img_b64 = base64.b64encode(img_file.getvalue()).decode() if img_file is not None else ""
            if msg_text or img_b64:
                f_text = encrypt_text(msg_text, st.session_state.room_password) if is_private else msg_text
                f_img = encrypt_text(img_b64, st.session_state.room_password) if is_private else img_b64
                data = {"sender": st.session_state.nickname, "text": f_text, "image_url": f_img, "sender_room": st.session_state.active_chat}
                requests.post(f"{URL}/rest/v1/messages", headers=headers, json=data)
                st.session_state.msg_input = ""

        with st.form(key="send_form", clear_on_submit=True):
            st.text_input("Напишите сообщение...", key="msg_input")
            st.file_uploader("Картинка в чат", type=["png", "jpg", "jpeg"], key="img_uploader")
            st.form_submit_button(label="Отправить", on_click=send_msg)

        st.divider()

        # Кэш аватарок для быстрой прогрузки
        avatar_cache = get_all_profiles_cached()

        # Рендеринг красивых сообщений
