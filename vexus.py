import streamlit as st
import requests
import time

# --- НАСТРОЙКИ SUPABASE ---
# Убедись, что URL заканчивается на .co (БЕЗ "/" в конце)
URL = "https://dqpdfreewxzefsaejmob.supabase.co"
KEY = "sb_publishable_XBWFiWdA9Eg2msn3T04XkQ_oKX69lpG"

st.set_page_config(page_title="Наш Web Мессенджер", page_icon="💬", layout="centered")
st.title("💬 Наш Мессенджер")

if "nickname" not in st.session_state:
    st.session_state.nickname = ""

# --- ОКНО ВХОДА ---
if not st.session_state.nickname:
    st.subheader("Введите ваш никнейм для входу:")
    nick_input = st.text_input("Мой ник...", max_chars=15)
    if st.button("Войти в чат"):
        if nick_input.strip():
            st.session_state.nickname = nick_input.strip()
            st.rerun()
        else:
            st.error("Никнейм не может быть пустым!")

# --- ОКНО ЧАТА ---
else:
    st.write(f"Вы вошли как: **{st.session_state.nickname}**")
    
    if st.button("Выйти из чата"):
        st.session_state.nickname = ""
        st.rerun()

    st.divider()

    # Чистые заголовки для работы с API
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    def send_msg():
        msg_text = st.session_state.msg_input.strip()
        if msg_text:
            try:
                post_url = f"{URL}/rest/v1/messages"
                data = {"sender": st.session_state.nickname, "text": msg_text}
                res = requests.post(post_url, headers=headers, json=data)
                
                # Проверка: если код ответа НЕ 200 и НЕ 201 — выводим ошибку
                if res.status_code not in:
                    st.error(f"Ошибка отправки (Код {res.status_code}): {res.text}")
                else:
                    st.session_state.msg_input = "" # Очищаем поле
            except Exception as e:
                st.error(f"Ошибка отправки: {e}")

    with st.form(key="send_form", clear_on_submit=True):
        st.text_input("Напишите сообщение...", key="msg_input")
        submit_button = st.form_submit_button(label="Отправить", on_click=send_msg)

    st.divider()

    # Загрузка сообщений
    try:
        get_url = f"{URL}/rest/v1/messages?select=*&order=id.desc&limit=50"
        response = requests.get(get_url, headers=headers)
        
        if response.status_code == 200:
            messages = response.json()
            if messages:
                for msg in reversed(messages):
                    st.markdown(f"**[{msg['sender']}]**: {msg['text']}")
            else:
                st.info("Чат пуст. Напишите что-нибудь первым!")
        else:
            st.error(f"Ошибка сервера Supabase (Код {response.status_code}): {response.text}")
            
    except Exception as e:
        st.error(f"Ошибка загрузки сообщений: {e}")

    # Автообновление каждые 3 секунды
    time.sleep(3)
    st.rerun()
