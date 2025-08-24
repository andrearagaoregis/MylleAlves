# ======================
# IMPORTS
# ======================
import streamlit as st
import requests
import json
import time
import random
import sqlite3
import re
import os
import uuid
from datetime import datetime
from pathlib import Path
from functools import lru_cache
import traceback

# ======================
# STREAMLIT CONFIG
# ======================
st.set_page_config(
    page_title="Mylle Premium",
    page_icon="💋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# optional client config (kept from original)
try:
    st._config.set_option("client.caching", True)
    st._config.set_option("client.showErrorDetails", False)
except Exception:
    # older streamlit versions may not expose _config
    pass

hide_streamlit_style = """
<style>
    #root > div:nth-child(1) > div > div > div > div > section > div {
        padding-top: 0rem;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    div[data-testid="stStatusWidget"] {
        display: none !important;
    }
    #MainMenu {
        display: none !important;
    }
    header {
        display: none !important;
    }
    footer {
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }
    .block-container {
        padding-top: 0rem !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ======================
# CONFIG
# ======================
class Config:
    API_KEY = "AIzaSyDbGIpsR4vmAfy30eEuPjWun3Hdz6xj24U"
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    AUDIO_FILE = "https://github.com/gustapb77/ChatBotHot/raw/refs/heads/main/assets/audio/paloma_audio.mp3"
    AUDIO_DURATION = 7
    IMG_PROFILE = "https://i.ibb.co/3c5k3Vx/mylle-profile.jpg"
    IMG_GALLERY = [
        "https://i.ibb.co/zhNZL4FF/IMG-9198.jpg",
        "https://i.ibb.co/Y4B7CbXf/IMG-9202.jpg",
        "https://i.ibb.co/Fqf0gPPq/IMG-9199.jpg",
    ]
    IMG_HOME_PREVIEWS = [
        "https://i.ibb.co/k2MJg4XC/Save-ClipApp-412457343-378531441368078-7870326395110089440-n.jpg",
        "https://i.ibb.co/MxqKBk1X/Save-ClipApp-481825770-18486618637042608-2702272791254832108-n.jpg",
        "https://i.ibb.co/F4CkkYTL/Save-ClipApp-461241348-1219420546053727-2357827070610318448-n.jpg",
    ]
    LOGO_URL = "https://i.ibb.co/LX7x3tcB/Logo-Golden-Pepper-Letreiro-1.png"
    SOCIALS = {
        "Instagram": "https://instagram.com/",
        "Facebook": "https://facebook.com/",
        "Telegram": "https://t.me/",
        "TikTok": "https://www.tiktok.com/",
    }

# ======================
# PERSISTENT STATE (sqlite wrapper)
# ======================
class PersistentState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        self.conn = sqlite3.connect("persistent_state.db", check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS global_state (
                user_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def save_state(self, user_id, data):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO global_state (user_id, session_data) VALUES (?, ?)",
            (user_id, json.dumps(data)),
        )
        self.conn.commit()

    def load_state(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT session_data FROM global_state WHERE user_id = ?", (user_id,))
        r = cur.fetchone()
        return json.loads(r[0]) if r else None


# ======================
# UTIL: session id / persistent data helpers
# ======================
def get_user_id():
    # keep deterministic per visitor via query param if present, else set a uuid
    if "user_id" not in st.session_state:
        uid = st.experimental_get_query_params().get("uid", [None])[0]
        if not uid:
            uid = str(uuid.uuid4())
            # don't directly mutate query params permanently; it's fine to store in session_state
        st.session_state.user_id = uid
    return st.session_state.user_id


def load_persistent_data():
    user_id = get_user_id()
    db = PersistentState()
    saved = db.load_state(user_id) or {}
    for k, v in saved.items():
        if k not in st.session_state:
            st.session_state[k] = v


def save_persistent_data():
    user_id = get_user_id()
    db = PersistentState()
    persistent_keys = [
        "age_verified",
        "messages",
        "request_count",
        "connection_complete",
        "chat_started",
        "audio_sent",
        "current_page",
        "show_vip_offer",
        "session_id",
        "last_cta_time",
        "greeted",
        "first_response_handled",
    ]
    new_data = {k: st.session_state.get(k) for k in persistent_keys if k in st.session_state}
    old = db.load_state(user_id) or {}
    if new_data != old:
        db.save_state(user_id, new_data)


# ======================
# DATABASE (chat history)
# ======================
class DatabaseService:
    @staticmethod
    def init_db():
        conn = sqlite3.connect("chat_history.db", check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS conversations
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                timestamp DATETIME,
                role TEXT,
                content TEXT)"""
        )
        conn.commit()
        return conn

    @staticmethod
    def save_message(conn, user_id, session_id, role, content):
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO conversations (user_id, session_id, timestamp, role, content) VALUES (?, ?, ?, ?, ?)",
                (user_id, session_id, datetime.now(), role, content),
            )
            conn.commit()
        except sqlite3.Error as e:
            # don't raise to UI, but log
            print("DB save_message error:", e)

    @staticmethod
    def load_messages(conn, user_id, session_id):
        c = conn.cursor()
        c.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? AND session_id = ? ORDER BY timestamp",
            (user_id, session_id),
        )
        return [{"role": r[0], "content": r[1]} for r in c.fetchall()]


# ======================
# CTA Engine & Persona (kept simple)
# ======================
class Persona:
    MYLLE = (
        "[PERFIL MYLLE]\n"
        "- Mulher safada e provocante que adora deixar o cliente com tesão\n"
        "- Linguagem direta, carinhosa e com malícia\n"
        "- Frases curtas, tom íntimo\n"
    )


class CTAEngine:
    @staticmethod
    def should_show_cta(conversation_history: list) -> bool:
        if len(conversation_history) < 2:
            return False
        if "last_cta_time" in st.session_state:
            elapsed = time.time() - st.session_state.last_cta_time
            if elapsed < 120:
                return False
        context = " ".join(
            [
                (m["content"] if not m["content"].startswith('{"text"') else json.loads(m["content"]).get("text", ""))
                .lower()
                for m in conversation_history[-5:]
            ]
        )
        hot_words = [
            "foto",
            "fotos",
            "video",
            "buceta",
            "transar",
            "mostra",
            "ver",
            "quero",
            "gostosa",
        ]
        hot_count = sum(1 for w in hot_words if w in context)
        direct_asks = any(ask in context for ask in ["quero ver", "me manda", "como assinar", "como comprar"])
        return hot_count >= 3 or direct_asks

    @staticmethod
    def generate_response(user_input: str) -> dict:
        u = user_input.lower()
        if any(p in u for p in ["foto", "fotos", "buceta", "peito", "bunda"]):
            return {"text": "tenho fotos bem gostosas, quer ver?", "cta": {"show": True, "label": "Ver Fotos Quentes", "target": "offers"}}
        if any(p in u for p in ["video", "transar", "masturbar"]):
            return {"text": "gravei vídeos bem quentes, vem ver", "cta": {"show": True, "label": "Ver Vídeos Exclusivos", "target": "offers"}}
        return {"text": "quero te mostrar coisas especiais...", "cta": {"show": False}}


# ======================
# API Service (Gemini stub)
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn) -> dict:
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn) -> dict:
        # Small randomized delay to mimic typing
        time.sleep(random.uniform(0.6, 1.6))

        # Build a safe prompt string (avoid f-strings with unescaped braces)
        conversation_history = ChatService.format_conversation_history(st.session_state.get("messages", []))
        api_user_text = (
            Persona.MYLLE
            + "\n\nHistórico da Conversa:\n"
            + conversation_history
            + "\n\nÚltima mensagem do cliente: '"
            + prompt
            + "'\n\nResponda em JSON com o formato:\n"
            + '{\n  "text": "...",\n  "cta": {"show": false}\n}\n'
        )

        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"role": "user", "parts": [{"text": api_user_text}]}],
            "generationConfig": {"temperature": 0.9, "topP": 0.8, "topK": 40},
        }

        try:
            resp = requests.post(Config.API_URL, headers=headers, json=data, timeout=Config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            gemini_response = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as e:
            # fallback to CTAEngine if API fails
            if any(k in prompt.lower() for k in ["foto", "video", "vip", "quero ver", "ver fotos"]):
                return CTAEngine.generate_response(prompt)
            print("ApiService error:", e)
            return {"text": "Erro ao obter resposta, tente novamente mais tarde.", "cta": {"show": False}}

        # try to parse JSON out of the response
        try:
            if "```json" in gemini_response:
                body = gemini_response.split("```json", 1)[1].split("```", 1)[0].strip()
                resposta = json.loads(body)
            else:
                resposta = json.loads(gemini_response)
        except Exception:
            # If parse fails, just return plain text
            return {"text": gemini_response, "cta": {"show": False}}

        if resposta.get("cta", {}).get("show"):
            if not CTAEngine.should_show_cta(st.session_state.get("messages", [])):
                resposta["cta"]["show"] = False
            else:
                st.session_state["last_cta_time"] = time.time()
        return resposta


# ======================
# UI Service
# ======================
class UiService:
    @staticmethod
    def get_chat_audio_player():
        return f"""
        <div style="background: linear-gradient(45deg, #ff66b3, #ff1493); border-radius: 15px; padding: 12px; margin: 5px 0;">
            <audio controls style="width:100%; height:40px;">
                <source src="{Config.AUDIO_FILE}" type="audio/mp3">
            </audio>
        </div>
        """

    @staticmethod
    def show_call_effect():
        LIGANDO_DELAY = 1.2
        ATENDIDA_DELAY = 0.8
        c = st.empty()
        c.markdown(
            """
            <div style="background: linear-gradient(135deg, #1e0033, #3c0066); border-radius: 20px; padding: 30px; max-width: 300px; margin: 0 auto; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 2px solid #ff66b3; text-align: center; color: white;">
              <div style="font-size: 3rem;">📱</div>
              <h3 style="color: #ff66b3; margin-bottom: 5px;">Ligando para Mylle...</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(LIGANDO_DELAY)
        c.markdown(
            """
            <div style="background: linear-gradient(135deg, #1e0033, #3c0066); border-radius: 20px; padding: 30px; max-width: 300px; margin: 0 auto; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 2px solid #4CAF50; text-align: center; color: white;">
              <div style="font-size: 3rem; color: #4CAF50;">✓</div>
              <h3 style="color: #4CAF50; margin-bottom: 5px;">Chamada atendida!</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(ATENDIDA_DELAY)
        c.empty()

    @staticmethod
    def show_custom_typing(container, duration=1.5):
        start = time.time()
        while time.time() - start < duration:
            elapsed = int((time.time() - start) * 3) % 4
            dots = "." * elapsed
            container.markdown(f'<div style="color:#888; font-style:italic;">Digitando{dots}</div>', unsafe_allow_html=True)
            time.sleep(0.25)
        container.empty()

    @staticmethod
    def age_verification():
        st.markdown(
            """
            <style>
            .age-ver {max-width:700px; margin: 2rem auto; padding: 2rem; background: linear-gradient(145deg, #1b5e20, #2e7d32); border-radius: 15px; color: white; text-align:center;}
            .age-photo{width:120px; height:120px; border-radius:50%; object-fit:cover; display:block; margin: 0.5rem auto;}
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="age-ver">
              <h1>🔞 Verificação de Idade</h1>
              <img class="age-photo" src="{Config.IMG_PROFILE}" />
              <p>Este conteúdo é destinado apenas a maiores de 18 anos.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🌶️ Confirmo que sou maior de 18 anos", key="age_checkbox", use_container_width=True):
                st.session_state["age_verified"] = True
                # Important: go directly to profile/home page and skip call animation
                st.session_state["current_page"] = "home"
                st.session_state["connection_complete"] = True
                st.session_state["chat_started"] = False
                save_persistent_data()
                st.experimental_rerun()

    @staticmethod
    def setup_sidebar():
        with st.sidebar:
            st.markdown(
                f"""
                <div style="padding:8px 6px 0 6px; text-align:left;">
                  <img src="{Config.LOGO_URL}" style="max-width:260px; display:block; margin-bottom:6px;" />
                </div>
                <div style="text-align:center;">
                  <img src="{Config.IMG_PROFILE}" style="width:80px; height:80px; border-radius:50%; border:2px solid #4caf50;" />
                  <h3 style="color:white;">Mylle Alves</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown('<h3 style="color:white;">Menu Exclusivo</h3>', unsafe_allow_html=True)
            menu_options = {"Início": "home", "Galeria Privada": "gallery", "Mensagens": "messages", "Ofertas Especiais": "offers"}
            for label, page in menu_options.items():
                if st.button(label, key=f"menu_{page}", use_container_width=True):
                    st.session_state["current_page"] = page
                    save_persistent_data()
                    st.experimental_rerun()

            st.markdown("---")
            st.markdown('<div style="text-align:center; color:#bdbdbd;">© 2024 Mylle Alves<br/>Conteúdo para maiores de 18 anos</div>', unsafe_allow_html=True)


# ======================
# CHAT SERVICE
# ======================
class ChatService:
    @staticmethod
    def initialize_session(conn):
        # load persistent values from DB into session_state
        load_persistent_data()

        # ensure session_id exists
        if "session_id" not in st.session_state or not st.session_state.get("session_id"):
            st.session_state["session_id"] = str(random.randint(100000, 999999))

        # ensure messages list exists (load from DB)
        if "messages" not in st.session_state:
            st.session_state["messages"] = DatabaseService.load_messages(conn, get_user_id(), st.session_state["session_id"])

        # ensure request_count exists
        if "request_count" not in st.session_state:
            st.session_state["request_count"] = len([m for m in st.session_state["messages"] if m.get("role") == "user"])

        # set defaults for other flags
        defaults = {
            "age_verified": False,
            "connection_complete": False,
            "chat_started": False,
            "audio_sent": False,
            "current_page": "home",
            "show_vip_offer": False,
            "last_cta_time": 0,
            "greeted": False,
            "first_response_handled": False,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def format_conversation_history(messages, max_messages=10):
        lines = []
        for msg in messages[-max_messages:]:
            role = "Cliente" if msg.get("role") == "user" else "Mylle"
            content = msg.get("content", "")
            if content == "[ÁUDIO]":
                content = "[Enviou um áudio sensual]"
            else:
                # if stored as JSON string with "text", extract
                if isinstance(content, str) and content.startswith('{"text"'):
                    try:
                        content = json.loads(content).get("text", content)
                    except Exception:
                        pass
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def display_chat_history():
        for idx, msg in enumerate(st.session_state.get("messages", [])[-12:]):
            if msg.get("role") == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f'<div style="background:#dcf8c6; padding:10px; border-radius:10px;">{msg.get("content")}</div>', unsafe_allow_html=True)
            else:
                # assistant
                content = msg.get("content", "")
                # if it's JSON stored (text + cta), try parse
                parsed_text = None
                try:
                    if isinstance(content, str) and content.startswith("{"):
                        parsed = json.loads(content)
                        parsed_text = parsed.get("text", None)
                        cta = parsed.get("cta", {})
                    else:
                        parsed_text = None
                        cta = {}
                except Exception:
                    parsed_text = None
                    cta = {}
                display_text = parsed_text if parsed_text is not None else content
                with st.chat_message("assistant", avatar="💋"):
                    st.markdown(f'<div style="background:#fff; padding:10px; border-radius:10px;">{display_text}</div>', unsafe_allow_html=True)
                    if cta.get("show") and st.button(cta.get("label", "Ver Ofertas"), key=f"cta_{idx}", use_container_width=True):
                        st.session_state["current_page"] = cta.get("target", "offers")
                        save_persistent_data()
                        st.experimental_rerun()

    @staticmethod
    def validate_input(user_input):
        cleaned = re.sub(r"<[^>]*>", "", user_input)
        return cleaned[:500]

    @staticmethod
    def process_user_input(conn):
        ChatService.display_chat_history()

        # initial greeting flow
        if st.session_state.get("chat_started", False) and not st.session_state.get("greeted", False):
            container = st.empty()
            UiService.show_custom_typing(container, duration=1.2)
            first = "oi gostoso 😈 me conta seu nome e onde você mora?"
            st.session_state["messages"].append({"role": "assistant", "content": json.dumps({"text": first, "cta": {"show": False}})})
            DatabaseService.save_message(conn, get_user_id(), st.session_state["session_id"], "assistant", json.dumps({"text": first, "cta": {"show": False}}))
            st.session_state["greeted"] = True
            save_persistent_data()
            st.experimental_rerun()
            return

        user_input = st.chat_input("Escreva sua mensagem aqui", key="chat_input")
        if not user_input:
            return

        cleaned = ChatService.validate_input(user_input)

        if st.session_state.get("request_count", 0) >= Config.MAX_REQUESTS_PER_SESSION:
            st.session_state["messages"].append({"role": "assistant", "content": "Estou ocupada agora, me manda mensagem depois?"})
            DatabaseService.save_message(conn, get_user_id(), st.session_state["session_id"], "assistant", "Estou ocupada agora, me manda mensagem depois?")
            save_persistent_data()
            st.experimental_rerun()
            return

        # save user message
        st.session_state["messages"].append({"role": "user", "content": cleaned})
        DatabaseService.save_message(conn, get_user_id(), st.session_state["session_id"], "user", cleaned)
        st.session_state["request_count"] = st.session_state.get("request_count", 0) + 1

        with st.chat_message("user", avatar="🧑"):
            st.markdown(f'<div style="background:#dcf8c6; padding:10px; border-radius:10px;">{cleaned}</div>', unsafe_allow_html=True)

        # special first-response flow
        if st.session_state.get("greeted", False) and not st.session_state.get("first_response_handled", False):
            # extract possible name
            name_display = "gato"
            try:
                first_token = cleaned.strip().split()[0]
                if first_token.isalpha() and len(first_token) > 1:
                    name_display = first_token.capitalize()
            except Exception:
                pass

            intro = f"ai {name_display}.. que delícia saber de você ❤️ eu sou a Mylle, crio conteúdo bem ousado e íntimo"
            promo = "essa semana tá tudo em promoção pros meus seguidores mais chegadinhos, mas eu conto tudo com carinho e do jeito mais safado pra você 😘"

            container = st.empty()
            UiService.show_custom_typing(container, duration=1.0)
            with st.chat_message("assistant", avatar="💋"):
                st.markdown(f'<div style="background:#fff; padding:10px; border-radius:10px;">{intro}</div>', unsafe_allow_html=True)

            st.session_state["messages"].append({"role": "assistant", "content": json.dumps({"text": intro, "cta": {"show": False}})})
            DatabaseService.save_message(conn, get_user_id(), st.session_state["session_id"], "assistant", json.dumps({"text": intro, "cta": {"show": False}}))

            container = st.empty()
            UiService.show_custom_typing(container, duration=1.0)
            with st.chat_message("assistant", avatar="💋"):
                st.markdown(f'<div style="background:#fff; padding:10px; border-radius:10px;">{promo}</div>', unsafe_allow_html=True)

            st.session_state["messages"].append({"role": "assistant", "content": json.dumps({"text": promo, "cta": {"show": False}})})
            DatabaseService.save_message(conn, get_user_id(), st.session_state["session_id"], "assistant", json.dumps({"text": promo, "cta": {"show": False}}))

            st.session_state["first_response_handled"] = True
            save_persistent_data()
            st.experimental_rerun()
            return

        # normal flow - call API
        container = st.empty()
        UiService.show_custom_typing(container, duration=1.0)
        resposta = ApiService.ask_gemini(cleaned, st.session_state["session_id"], conn)
        if isinstance(resposta, str):
            resposta = {"text": resposta, "cta": {"show": False}}
        elif "text" not in resposta:
            resposta = {"text": str(resposta), "cta": {"show": False}}

        with st.chat_message("assistant", avatar="💋"):
            st.markdown(f'<div style="background:#fff; padding:10px; border-radius:10px;">{resposta["text"]}</div>', unsafe_allow_html=True)
            if resposta.get("cta", {}).get("show"):
                if st.button(resposta["cta"].get("label", "Ver Ofertas"), key=f"cta_action_{time.time()}", use_container_width=True):
                    st.session_state["current_page"] = resposta["cta"].get("target", "offers")
                    save_persistent_data()
                    st.experimental_rerun()

        st.session_state["messages"].append({"role": "assistant", "content": json.dumps(resposta)})
        DatabaseService.save_message(conn, get_user_id(), st.session_state["session_id"], "assistant", json.dumps(resposta))
        save_persistent_data()
        st.experimental_rerun()


# ======================
# PAGES (HOME / GALLERY / OFFERS)
# ======================
class Pages:
    @staticmethod
    def show_home_page(conn):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(Config.IMG_PROFILE, use_column_width=True)
            st.markdown('<div style="text-align:center;"><h3 style="color:#ff66b3;">Mylle Alves</h3><p style="color:#888;">Online agora 💚</p></div>', unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(
                '<div style="background: rgba(255, 102, 179, 0.1); padding: 15px; border-radius: 10px;"><h4>📊 Meu Perfil</h4><p>👙 85-60-90</p><p>📏 1.68m</p><p>🎂 22 anos</p><p>📍 São Paulo</p></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown('<div style="background: linear-gradient(45deg, #ff66b3, #ff1493); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;"><h2>💋 Bem-vindo ao Meu Mundo</h2><p>Conversas quentes e conteúdo exclusivo esperando por você!</p></div>', unsafe_allow_html=True)
            st.markdown("### 🌶️ Prévia do Conteúdo")
            prcols = st.columns(2)
            for i, c in enumerate(prcols):
                if i < len(Config.IMG_HOME_PREVIEWS):
                    with c:
                        st.image(Config.IMG_HOME_PREVIEWS[i], use_column_width=True)
            st.markdown("---")
            if st.button("Iniciar Conversa 🌶️", key="start_from_profile", use_container_width=True):
                st.session_state["chat_started"] = True
                st.session_state["current_page"] = "chat"
                save_persistent_data()
                st.experimental_rerun()

    @staticmethod
    def show_gallery_page(conn):
        st.markdown('<div style="background: rgba(0, 0, 0, 0.06); padding: 15px; border-radius: 10px; margin-bottom: 20px;"><p style="margin:0;">Conteúdo exclusivo disponível</p></div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            with col:
                st.image(Config.IMG_GALLERY[idx], use_column_width=True, caption=f"Preview {idx+1}")
                st.markdown('<div style="text-align:center; color:#ff66b3; margin-top:-10px;">Conteúdo bloqueado</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<div style="text-align:center;"><h4>Desbloqueie acesso completo</h4><p>Assine o plano ideal para você</p></div>', unsafe_allow_html=True)
        if st.button("Voltar ao chat", key="back_from_gallery"):
            st.session_state["current_page"] = "chat"
            save_persistent_data()
            st.experimental_rerun()

    @staticmethod
    def show_offers_page():
        st.markdown('<div style="text-align:center; margin-bottom:18px;"><h2 style="color:#fff;">Ofertas Especiais</h2><p style="color:#cfd8dc;">Confira algumas opções — sem links diretos de pagamento nesta versão.</p></div>', unsafe_allow_html=True)
        plans = [
            {"name": "1 Mês", "price": "R$ 29,90", "benefits": ["Acesso total", "Conteúdo novo diário", "Chat privado"], "tag": "COMUM"},
            {"name": "3 Meses", "price": "R$ 69,90", "benefits": ["25% de desconto", "Bônus: 1 vídeo exclusivo", "Prioridade no chat"], "tag": "MAIS POPULAR"},
            {"name": "1 Ano", "price": "R$ 199,90", "benefits": ["66% de desconto", "Presente surpresa mensal", "Acesso a conteúdos raros"], "tag": "MELHOR CUSTO-BENEFÍCIO"},
        ]
        for plan in plans:
            st.markdown(f'<div style="border:1px solid rgba(255,255,255,0.06); padding:14px; border-radius:12px; margin-bottom:8px;"><div style="display:flex; justify-content:space-between;"><strong>{plan["name"]}</strong><span style="background:#1de9b6;color:#004d40;padding:4px 8px;border-radius:6px;">{plan["tag"]}</span></div><div style="margin-top:6px; font-weight:bold; color:#1de9b6;">{plan["price"]}</div><ul>{"".join(f"<li>{b}</li>" for b in plan["benefits"])}</ul></div>', unsafe_allow_html=True)
        if st.button("Voltar ao chat", key="back_from_offers"):
            st.session_state["current_page"] = "chat"
            save_persistent_data()
            st.experimental_rerun()


# ======================
# MAIN APP
# ======================
def main():
    # ensure DB connection in session
    if "db_conn" not in st.session_state:
        st.session_state["db_conn"] = DatabaseService.init_db()
    conn = st.session_state["db_conn"]

    # Initialize session_state defaults (to avoid NameError/KeyError)
    # load persistent keys if any
    load_persistent_data()
    defaults = {
        "age_verified": False,
        "connection_complete": False,
        "chat_started": False,
        "audio_sent": False,
        "current_page": "home",
        "show_vip_offer": False,
        "last_cta_time": 0,
        "greeted": False,
        "first_response_handled": False,
        "messages": [],
        "request_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Setup sidebar (always visible after age verification)
    if not st.session_state.get("age_verified", False):
        UiService.age_verification()
        st.stop()

    UiService.setup_sidebar()

    # Initialize chat service session (wrapped to show meaningful error on failure)
    try:
        ChatService.initialize_session(conn)
    except Exception as e:
        # Show helpful info and stacktrace in app (redacted error message earlier made debugging hard)
        st.error("Erro ao inicializar sessão do chat. Veja o log abaixo.")
        st.text(traceback.format_exc())
        st.stop()

    # Skip the "calling" animation if connection_complete is already True (we set it at age verification)
    if not st.session_state.get("connection_complete", False):
        UiService.show_call_effect()
        st.session_state["connection_complete"] = True
        save_persistent_data()
        st.experimental_rerun()

    # If chat hasn't started, show profile/start screen (this is the page you wanted after age verification)
    if not st.session_state.get("chat_started", False):
        Pages.show_home_page(conn)
        st.stop()

    # Route pages
    page = st.session_state.get("current_page", "chat")
    if page == "home":
        Pages.show_home_page(conn)
    elif page == "gallery":
        Pages.show_gallery_page(conn)
    elif page == "offers":
        Pages.show_offers_page()
    else:
        # default to chat UI
        UiService.setup_sidebar()
        UiService.show_custom_typing  # noop reference (keeps linter happy)
        ChatService.process_user_input(conn)


if __name__ == "__main__":
    main()
