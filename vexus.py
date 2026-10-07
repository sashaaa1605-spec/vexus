import streamlit as st
from supabase import create_client, Client
import time

# --- НАЛАШТУВАННЯ SUPABASE ---
URL = "https://dqpdfreewxzefsaejmob.supabase.co/rest/v1/"
KEY = "sb_publishable_XBWFiWdA9Eg2msn3T04XkQ_oKX69lpG"

@st.cache_resource
def get_supabase_client():
    return create_client(URL, KEY)

supabase = get_supabase_client()

st.set_page_config(page_title="vexus Web", page_icon="💬", layout="centered")
st.title("💬 vexus")

if "nickname" not in st.session_state:
    st.session_state.nickname = ""

# --- ВІКНО ВХОДУ ---
if not st.session_state.nickname:
    st.subheader("введите ваш никнейм:")
    nick_input = st.text_input("Мій нік...", max_chars=15)
    if st.button("Увійти в чат"):
        if nick_input.strip():
            st.session_state.nickname = nick_input.strip()
            st.rerun()
        else:
            st.error("никнейи не может быть пустым")

# --- ВІКНО ЧАТУ ---
else:
    st.write(f"вы зашли как: **{st.session_state.nickname}**")
    
    if st.button("выйти из  чата"):
        st.session_state.nickname = ""
        st.rerun()

    st.divider()

    def send_msg():
        msg_text = st.session_state.msg_input.strip()
        if msg_text:
            try:
                supabase.table("messages").insert({"sender": st.session_state.nickname, "text": msg_text}).execute()
                st.session_state.msg_input = ""
            except Exception as e:
                st.error(f"Помилка відправки: {e}")

    with st.form(key="send_form", clear_on_submit=True):
        st.text_input("напишите сообщение", key="msg_input")
        submit_button = st.form_submit_button(label="Надіслати", on_click=send_msg)

    st.divider()

    try:
        response = supabase.table("messages").select("*").order("id", desc=True).limit(50).execute()
        messages = response.data
        
        if messages:
            for msg in reversed(messages):
                st.markdown(f"**[{msg['sender']}]**: {msg['text']}")
        else:
            st.info("Чат порожній. Напишіть щось першим!")
            
    except Exception as e:
        st.error(f"Помилка завантаження повідомлень: {e}")

    time.sleep(3)
    st.rerun()
