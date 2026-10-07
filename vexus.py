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
    try: return Fernet(generate_key(password)).decrypt(cipher_text.encode()).decode()
    except: return "[Зашифровано — неверный ключ]"

# --- СЕССИЯ И ДИЗАЙН ---
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "nickname" not in st.session_state: st.session_state.nickname = ""
if "active_chat" not in st.session_state: st.session_state.active_chat = "Общий чат"
if "room_password" not in st.session_state: st.session_state.room_password = "default_secure_pass"
if "edit_profile" not in st.session_state: st.session_state.edit_profile = False

headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

bg = "#182533" if st.session_state.theme == "dark" else "#ffffff"
tc = "#ffffff" if st.session_state.theme == "dark" else "#000000"
st.markdown(f"<style>.stApp {{background-color: {bg}; color: {tc};}}</style>", unsafe_allow_html=True)

# --- ФУНКЦИИ ПРОФИЛЕЙ ---
def get_profile(nickname):
    try:
        res = requests.get(f"{URL}/rest/v1/profiles?nickname=eq.{nickname}", headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
    except: pass
    return None

# --- ОКНО ВХОДА И РЕГИСТРАЦИИ ---
if not st.session_state.nickname:
    st.title("💬 Vexus v4.0 — Вход")
    
    st.markdown("### 🔑 Авторизация через Gmail / Почту")
    email_input = st.text_input("Введите ваш Gmail:", placeholder="yourname@gmail.com").strip().lower()
    nick_input = st.text_input("Придумайте ваш никнейм в Vexus (только буквы/цифры):", max_chars=15).strip().lower()
    
    if st.button("Войти / Зарегистрироваться", use_container_width=True):
        if not email_input or not nick_input:
            st.error("Заполните все поля!")
        elif "@" not in email_input:
            st.error("Введите корректный Gmail адрес!")
        else:
            # Проверяем, существует ли уже профиль
            try:
                res_email = requests.get(f"{URL}/rest/v1/profiles?email=eq.{email_input}", headers=headers).json()
                res_nick = requests.get(f"{URL}/rest/v1/profiles?nickname=eq.{nick_input}", headers=headers).json()
                
                if res_email:
                    # Почта есть, проверяем совпадает ли ник
                    if res_email[0]['nickname'] == nick_input:
                        st.session_state.user_email = email_input
                        st.session_state.nickname = nick_input
                        st.success("Успешный вход!")
                        st.rerun()
                    else:
                        st.error("Этот Gmail уже привязан к другому никнейму!")
                else:
                    if res_nick:
                        st.error("Этот никнейм уже занят!")
                    else:
                        # Создаем новый аккаунт
                        new_user = {"email": email_input, "nickname": nick_input}
                        requests.post(f"{URL}/rest/v1/profiles", headers=headers, json=new_user)
                        st.session_state.user_email = email_input
                        st.session_state.nickname = nick_input
                        st.success("Регистрация успешна!")
                        st.rerun()
            except Exception as e:
                st.error(f"Ошибка базы: {e}")

# --- ГЛАВНЫЙ ИНТЕРФЕЙС VEXUS ---
else:
    my_prof = get_profile(st.session_state.nickname) or {}
    
    with st.sidebar:
        st.title("💬 Vexus")
        
        # Рендеринг кастомного профиля в сайдбаре
        if my_prof.get("banner_b64"):
            st.image(base64.b64decode(my_prof["banner_b64"]), use_container_width=True)
        if my_prof.get("avatar_b64"):
            st.image(base64.b64decode(my_prof["avatar_b64"]), width=80)
            
        st.subheader(f"👤 @{st.session_state.nickname}")
        st.caption(f"Status: {my_prof.get('status_text', 'No status')}")
        
        if st.button("⚙️ Настроить профиль", use_container_width=True):
            st.session_state.edit_profile = not st.session_state.edit_profile
            
        theme_toggle = st.toggle("🌙 Темная тема", value=(st.session_state.theme == "dark"))
        st.session_state.theme = "dark" if theme_toggle else "light"
        
        st.divider()
        st.markdown("### 🔍 Поиск кентов")
        search_user = st.text_input("Введи ник кента:", placeholder="например: ivan").strip().lower()
        
        chats_list = ["Общий чат"]
        if search_user and search_user != st.session_state.nickname:
            private_room_id = "🔒-" + "-".join(sorted([st.session_state.nickname, search_user]))
            chats_list.append(private_room_id)
            
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
            if new_ava:
                up_data["avatar_b64"] = base64.b64encode(new_ava.getvalue()).decode()
            if new_banner:
                up_data["banner_b64"] = base64.b64encode(new_banner.getvalue()).decode()
                
            requests.patch(f"{URL}/rest/v1/profiles?nickname=eq.{st.session_state.nickname}", headers=headers, json=up_data)
            st.success("Профиль обновлен!")
            st.session_state.edit_profile = False
            st.rerun()

    # --- ОКНО ЧАТА ---
    else:
        # Если мы в приватном чате, покажем профиль кента вверху чата!
        if "🔒-" in st.session_state.active_chat:
            st.subheader(f"👤 Приватный диалог с @{search_user}")
            kent_prof = get_profile(search_user)
            if kent_prof:
                st.caption(f"ℹ️ Статус кента: {kent_prof.get('status_text', 'Нет статуса')}")
                if kent_prof.get("avatar_b64"):
                    st.image(base64.b64decode(kent_prof["avatar_b64"]), width=40)
        else:
            st.subheader("🌍 Общая лента сообщений Vexus")

        # Функция отправки сообщения
        def send_msg():
            msg_text = st.session_state.msg_input.strip()
            img_file = st.session_state.img_uploader
            img_b64 = ""
            
            if img_file is not None:
                img_b64 = base64.b64encode(img_file.getvalue()).decode()

            if msg_text or img_b64:
                try:
                    if "🔒-" in st.session_state.active_chat:
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
                except: pass

        with st.form(key="send_form", clear_on_submit=True):
            st.text_input("Напишите сообщение...", key="msg_input")
            st.file_uploader("Картинка в чат", type=["png", "jpg", "jpeg"], key="img_uploader")
            st.form_submit_button(label="Отправить", on_click=send_msg)

        st.divider()

        # Отображение сообщений
        try:
            res = requests.get(f"{URL}/rest/v1/messages?select=*&order=id.desc&limit=30", headers=headers)
            if res.status_code == 200:
                filtered = [m for m in res.json() if m.get("sender_room", "Общий чат") == st.session_state.active_chat]
                
                for msg in reversed(filtered):
                    d_text = msg.get('text', '')
                    d_img = msg.get('image_url', '')

