# ======================
# IMPORTAÇÕES
# ======================
import streamlit as st
import requests
import json
import time
import random
import sqlite3
import re
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional
from collections import defaultdict

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(
    page_title="Mylle Alves Premium",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS (igual ao original)
hide_streamlit_style = """
<style>
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], 
    div[data-testid="stStatusWidget"], #MainMenu, header, footer, 
    .stDeployButton {display: none !important;}
    .block-container {padding-top: 0rem !important;}
    [data.testid="stVerticalBlock"], [data.testid="stHorizontalBlock"] {gap: 0.5rem !important;}
    .stApp {
        margin: 0 !important; 
        padding: 0 !important;
        background: linear-gradient(135deg, #1a0033 0%, #2d004d 50%, #1a0033 100%);
        color: white;
    }
    .stChatMessage {padding: 12px !important; border-radius: 15px !important; margin: 8px 0 !important;}
    .stButton > button {
        transition: all 0.3s ease !important;
        background: linear-gradient(45deg, #ff1493, #9400d3) !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important; 
        box-shadow: 0 4px 8px rgba(255, 20, 147, 0.4) !important;
    }
    .stTextInput > div > div > input {
        background: rgba(255, 102, 179, 0.1) !important;
        color: white !important;
        border: 1px solid #ff66b3 !important;
    }
    .social-buttons {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 15px 0;
    }
    .social-button {
        background: rgba(255, 102, 179, 0.2) !important;
        border: 1px solid #ff66b3 !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
    }
    .social-button:hover {
        background: rgba(255, 102, 179, 0.4) !important;
        transform: scale(1.1) !important;
    }
    .cta-button {
        margin-top: 10px !important;
        background: linear-gradient(45deg, #ff1493, #9400d3) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .cta-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(255, 20, 147, 0.4) !important;
    }
    .audio-message {
        background: rgba(255, 102, 179, 0.15) !important;
        padding: 15px !important;
        border-radius: 15px !important;
        margin: 10px 0 !important;
        border: 1px solid #ff66b3 !important;
        text-align: center !important;
    }
    .audio-icon {
        font-size: 24px !important;
        margin-right: 10px !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ======================
# CONSTANTES E CONFIGURAÇÕES
# ======================
class Config:
    API_KEY = st.secrets.get("API_KEY", "AIzaSyDbGIpsR4vmAfy30eEuPjWun3Hdz6xj24U")
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    CHECKOUT_TARADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACC74F-01EC-4770-B182-B5775AF62A1D"
    CHECKOUT_MOLHADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD1E6-0EFD-4E3E-9F9D-BA0C1A2D7E7A"
    CHECKOUT_SAFADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD395-EE65-458E-9B7E-FED750CC9CA9"
    MAX_REQUESTS_PER_SESSION = 100
    REQUEST_TIMEOUT = 30
    IMG_PROFILE = "https://i.ibb.co/bMynqzMh/BY-Admiregirls-su-Admiregirls-su-156.jpg"
    IMG_PREVIEW = "https://i.ibb.co/fGqCCyHL/preview-exclusive.jpg"
    PACK_IMAGES = {
        "TARADINHA": "https://i.ibb.co/sJJRttzM/BY-Admiregirls-su-Admiregirls-su-033.jpg",
        "MOLHADINHA": "https://i.ibb.co/NnTYdSw6/BY-Admiregirls-su-Admiregirls-su-040.jpg", 
        "SAFADINHA": "https://i.ibb.co/GvqtJ17h/BY-Admiregirls-su-Admiregirls-su-194.jpg"
    }
    IMG_GALLERY = [
        "https://i.ibb.co/VY42ZMST/BY-Admiregirls-su-Admiregirls-su-255.jpg",
        "https://i.ibb.co/Q7s9Zwcr/BY-Admiregirls-su-Admiregirls-su-183.jpg",
        "https://i.ibb.co/0jRMxrFB/BY-Admiregirls-su-Admiregirls-su-271.jpg"
    ]
    SOCIAL_LINKS = {
        "instagram": "https://instagram.com/myllealves",
        "onlyfans": "https://onlyfans.com/myllealves",
        "telegram": "https://t.me/myllealves",
        "twitter": "https://twitter.com/myllealves"
    }
    SOCIAL_ICONS = {
        "instagram": "📸 Instagram",
        "onlyfans": "💎 OnlyFans",
        "telegram": "✈️ Telegram",
        "twitter": "🐦 Twitter"
    }
    AUDIOS = {
        "boa_noite_nao_sou_fake": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Boa%20noite%20-%20N%C3%A3o%20sou%20fake%20n%C3%A3o....mp3",
        "boa_tarde_nao_sou_fake": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Boa%20tarde%20-%20N%C3%A3o%20sou%20fake%20n%C3%A3o....mp3",
        "bom_dia_nao_sou_fake": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Bom%20dia%20-%20n%C3%A3o%20sou%20fake%20n%C3%A3o....mp3",
        "claro_tenho_amostra_gratis": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Claro%20eu%20tenho%20amostra%20gr%C3%A1tis.mp3",
        "o_que_achou_amostras": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/O%20que%20achou%20das%20amostras.mp3",
        "pq_nao_faco_chamada": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Pq%20nao%20fa%C3%A7o%20mais%20chamada.mp3",
        "tenho_conteudos_que_vai_amar": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/eu%20tenho%20uns%20conteudos%20aqui%20que%20vc%20vai%20amar.mp3",
        "esperando_responder": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/vida%20to%20esperando%20voce%20me%20responder%20gatinho.mp3"
    }

SAMPLES_IMAGES = [
    "https://i.ibb.co/MDmGhjnX",
    "https://i.ibb.co/fGD0zvmY",
    "https://i.ibb.co/tSVc9Rz"
]

# ======================
# UTILITÁRIOS DE CONTEXTO E ESTADO
# ======================
class PersistentState:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_db()
        return cls._instance
    def init_db(self):
        self.conn = sqlite3.connect('persistent_state.db', check_same_thread=False)
        self.create_tables()
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_state (
                user_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    def save_state(self, user_id: str, data: Dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO global_state (user_id, session_data)
            VALUES (?, ?)
        ''', (user_id, json.dumps(data)))
        self.conn.commit()
    def load_state(self, user_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT session_data FROM global_state WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

def get_user_id() -> str:
    if 'user_id' not in st.session_state:
        user_id = st.query_params.get('uid', [None])[0]
        if not user_id:
            user_id = str(uuid.uuid4())
            st.query_params['uid'] = user_id
        st.session_state.user_id = user_id
    return st.session_state.user_id

def load_persistent_data() -> None:
    user_id = get_user_id()
    db = PersistentState()
    saved_data = db.load_state(user_id) or {}
    for key, value in saved_data.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_persistent_data() -> None:
    user_id = get_user_id()
    db = PersistentState()
    persistent_keys = [
        'age_verified', 'messages', 'request_count',
        'connection_complete', 'chat_started',
        'current_page', 'session_id', 'last_cta_time', 'preview_shown',
        'conversation_stage', 'lead_name', 'last_interaction_time', 
        'user_info_collected', 'last_user_message_time', 'audio_count', "samples_shown", "input_buffer"
    ]
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    db.save_state(user_id, new_data)

# ======================
# BANCO DE DADOS HISTÓRICO DE CHAT
# ======================
class DatabaseService:
    @staticmethod
    def init_db() -> sqlite3.Connection:
        conn = sqlite3.connect('chat_history.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id TEXT,
                     session_id TEXT,
                     timestamp DATETIME,
                     role TEXT,
                     content TEXT)''')
        conn.commit()
        return conn
    @staticmethod
    def save_message(conn: sqlite3.Connection, user_id: str, session_id: str, role: str, content: str) -> None:
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO conversations (user_id, session_id, timestamp, role, content)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_id, datetime.now(), role, content))
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Erro ao salvar mensagem: {e}")
    @staticmethod
    def load_messages(conn: sqlite3.Connection, user_id: str, session_id: str) -> List[Dict]:
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp
        """, (user_id, session_id))
        return [{"role": row[0], "content": row[1]} for row in c.fetchall()]

# ======================
# PERSONA (NOVO PERFIL)
# ======================
class Persona:
    MYLLE = """
    Eu sou a Mylle, sua criadora de conteúdo premium. Meus packs são feitos pra te deixar maluco de tesão. Adoro provocar, mas aqui comigo é direto ao ponto: não fico enrolando, quero ver você decidir logo e garantir seu acesso! Sempre respondo com carinho e safadeza, e claro, nunca deixo de te perguntar o que mais te deixa doido.
    - Falo sempre em primeira pessoa, nunca em terceira. 
    - Respondo dúvidas de fake/robô mostrando que sou real e mando áudio na hora. 
    - Mostro amostras grátis, mas pra ver o "bão", só comprando o pack... E olha: o acesso chega rapidinho no seu e-mail assim que a compra cai.
    - Sempre termino com uma pergunta safada ou incentivo você a agir.
    - Minhas respostas são curtas e envolventes. 
    """

# ======================
# UTILITÁRIOS PARA MELHORIAS (BUFFER, ANTI-FAKE, AMOSTRA, CTA)
# ======================
def get_buffered_input():
    buffer = st.session_state.get("input_buffer", [])
    now = time.time()
    last = st.session_state.get("last_user_message_time", now)
    user_input = st.chat_input("💬 Digite sua mensagem...", key="chat_input")
    if user_input:
        if now - last < 3:  # Mensagem picada
            buffer.append(user_input)
            st.session_state.input_buffer = buffer
            st.session_state.last_user_message_time = now
            return None
        else:
            if buffer:
                full_msg = " ".join(buffer + [user_input])
                st.session_state.input_buffer = []
                st.session_state.last_user_message_time = now
                return full_msg
            else:
                st.session_state.last_user_message_time = now
                return user_input
    return None

def check_anti_fake(user_input):
    if any(word in user_input.lower() for word in ["fake", "falsa", "bot", "robô", "artificial", "não é real", "é mentira"]):
        msg = random.choice([
            "Eu sou real sim, amor. Olha minha voz pra não restar dúvida 😘",
            "Nada de fake aqui, pode confiar! Ouve meu áudio, só quem é de verdade fala desse jeito...",
            "Aqui é real, viu? Não gosto de mentira, só de safadeza mesmo 😏"
        ])
        hora = datetime.now().hour
        if 5 <= hora < 12:
            audio_key = "bom_dia_nao_sou_fake"
        elif 12 <= hora < 18:
            audio_key = "boa_tarde_nao_sou_fake"
        else:
            audio_key = "boa_noite_nao_sou_fake"
        return {
            "text": msg,
            "audio": audio_key,
            "cta": {"show": False}
        }
    return None

def resposta_para_conversao(user_input):
    if any(word in user_input.lower() for word in ["pack", "conteúdo", "foto", "vídeo", "bão", "nude", "mostrar", "preço", "comprar", "acesso"]):
        return {
            "text": "Quer ver tudo mesmo? Meu conteúdo completo só nos packs VIP, amor. Assim que concluir a compra, você recebe o acesso por e-mail rapidinho. Bora liberar ou vai ficar só na vontade? Qual seu e-mail pra eu já te liberar quando cair?",
            "cta": {"show": True, "label": "🚀 Ver Pacotes VIP", "target": "offers"}
        }
    return None

def show_samples_gallery():
    st.markdown("""
    <div style="background:rgba(255,20,147,0.09);padding:12px;border-radius:11px;text-align:center;">
        <p style="color:#ff66b3;font-weight:bold;">Provinha grátis só pra te deixar com mais vontade...</p>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    for i, col in enumerate(cols):
        with col:
            st.image(SAMPLES_IMAGES[i], use_column_width=True, caption=f"🔥 Amostra #{i+1}")
    st.markdown("""
    <div style="text-align:center;color:#ff66b3;margin-top:6px;">
        <b>Só o proibido mesmo tá nos packs VIP. Bora liberar?</b>
    </div>
    """, unsafe_allow_html=True)

# ======================
# API GEMINI
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn: sqlite3.Connection) -> Dict:
        return ApiService._call_gemini_api(prompt, session_id, conn)
    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn: sqlite3.Connection) -> Dict:
        # Simula delay só se resposta longa (pode ser ajustado)
        response_delay = max(1.5, min(10, len(prompt) * 0.05))
        time.sleep(response_delay)
        conversation_history = ChatService.format_conversation_history(st.session_state.messages)
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{Persona.MYLLE}\n\nHistórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nIMPORTANTE: Responda curto, incentive a comprar, explique que o acesso chega no e-mail, nunca fale em terceira pessoa, sempre termine com pergunta ou incentivo. Use áudios se o contexto pedir, especialmente sobre fake."}]
                }
            ],
            "generationConfig": {
                "temperature": 1.08,
                "topP": 0.93,
                "topK": 40
            }
        }
        try:
            response = requests.post(Config.API_URL, headers=headers, json=data, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            gemini_response = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            try:
                if '```json' in gemini_response:
                    resposta = json.loads(gemini_response.split('```json')[1].split('```')[0].strip())
                else:
                    resposta = json.loads(gemini_response)
                return resposta
            except json.JSONDecodeError:
                return {"text": gemini_response, "cta": {"show": False}}
        except Exception as e:
            st.error(f"Erro: {str(e)}")
            return {"text": "Tive um errinho aqui, mas já volto a te provocar! Manda outra mensagem 💋", "cta": {"show": False}}

# ======================
# UI E CHAT PRINCIPAL
# ======================
class UiService:
    @staticmethod
    def show_audio_player(audio_key: str) -> None:
        if audio_key in Config.AUDIOS:
            st.markdown(f"""
            <div class="audio-message">
                <span class="audio-icon">🎵</span>
                <audio controls autoplay style="width: 100%;">
                    <source src="{Config.AUDIOS[audio_key]}" type="audio/mpeg">
                    Seu navegador não suporta o elemento de áudio.
                </audio>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def show_status_effect(container, status_type: str) -> None:
        status_messages = {"viewed": "Visto", "typing": "Digitando..."}
        message = status_messages[status_type]
        dots = ""
        start_time = time.time()
        duration = 1.2 if status_type == "viewed" else 2.0
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            if status_type == "typing":
                dots = "." * (int(elapsed * 2) % 4)
            container.markdown(f"""
            <div style="color: #888;font-size: 0.8em;padding: 2px 8px;border-radius: 10px;background: rgba(0,0,0,0.05);display: inline-block;margin-left: 10px;vertical-align: middle;font-style: italic;">
                {message}{dots}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)
        container.empty()

    @staticmethod
    def age_verification() -> None:
        st.markdown("""
        <style>
            .age-verification {max-width: 500px;margin: 2rem auto;padding: 2rem;background: linear-gradient(145deg, #1e0033, #3c0066);border-radius: 15px;box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);border: 1px solid rgba(255, 102, 179, 0.2);color: white;text-align: center;}
            .age-icon {font-size: 3rem;color: #ff66b3;margin-bottom: 1rem;}
        </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="age-verification">
            <div class="age-icon">🔞</div>
            <h1 style="color: #ff66b3; margin-bottom: 1rem;">Conteúdo Exclusivo Adulto</h1>
            <p style="margin-bottom: 1.5rem;">Acesso restrito para maiores de 18 anos</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("🔥 Tenho 18 anos ou mais", key="age_checkbox", use_container_width=True, type="primary"):
                st.session_state.age_verified = True
                save_persistent_data()
                st.rerun()

    @staticmethod
    def setup_sidebar() -> None:
        with st.sidebar:
            st.markdown(f"""
            <div class="sidebar-profile">
                <img src="{Config.IMG_PROFILE}" alt="Mylle Alves" style="border-radius:50%;border:3px solid #ff66b3;width:100px;height:100px;object-fit:cover;margin-bottom:10px;">
                <h3 style="color: #ff66b3; margin: 0;">Mylle Alves</h3>
                <p style="color: #aaa; margin: 0; font-size: 0.9em;">Online agora 💚</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            for platform, url in Config.SOCIAL_LINKS.items():
                if st.button(Config.SOCIAL_ICONS[platform], key=f"sidebar_{platform}", use_container_width=True):
                    js = f"window.open('{url}', '_blank');"
                    st.components.v1.html(f"<script>{js}</script>")
            st.markdown("---")
            menu_options = {
                "💋 Início": "home",
                "📸 Preview": "gallery",
                "🎁 Packs VIP": "offers"
            }
            for option, page in menu_options.items():
                if st.button(option, use_container_width=True, key=f"menu_{page}"):
                    st.session_state.current_page = page
                    save_persistent_data()
                    st.rerun()
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; font-size: 0.7em; color: #888;">
                <p>© 2024 Mylle Alves Premium</p>
                <p>Conteúdo adulto exclusivo</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def chat_shortcuts() -> None:
        cols = st.columns(3)
        with cols[0]:
            if st.button("🏠 Início", key="shortcut_home", use_container_width=True):
                st.session_state.current_page = "home"
                save_persistent_data()
                st.rerun()
        with cols[1]:
            if st.button("📸 Preview", key="shortcut_gallery", use_container_width=True):
                st.session_state.current_page = "gallery"
                save_persistent_data()
                st.rerun()
        with cols[2]:
            if st.button("🎁 Packs", key="shortcut_offers", use_container_width=True):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()

# ======================
# CHAT E FLUXO PRINCIPAL
# ======================
class ChatService:
    @staticmethod
    def initialize_session(conn: sqlite3.Connection) -> None:
        load_persistent_data()
        defaults = {
            'age_verified': False,
            'connection_complete': False,
            'chat_started': False,
            'current_page': 'home',
            'last_cta_time': 0,
            'preview_shown': False,
            'session_id': str(random.randint(100000, 999999)),
            'messages': DatabaseService.load_messages(conn, get_user_id(), st.session_state.get('session_id', '')) or [],
            'request_count': len([m for m in st.session_state.get('messages', []) if m["role"] == "user"]),
            'conversation_stage': 'approach',
            'lead_name': None,
            'last_interaction_time': time.time(),
            'user_info_collected': False,
            'last_user_message_time': time.time(),
            'audio_count': 0,
            'samples_shown': False,
            'input_buffer': []
        }
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default
        # Mensagem de abertura
        if len(st.session_state.messages) == 0 and st.session_state.chat_started:
            typing_container = st.empty()
            UiService.show_status_effect(typing_container, "typing")
            typing_container.empty()
            initial_message = {
                "role": "assistant",
                "content": json.dumps({
                    "text": "Oi, já tava esperando você aqui! 😏 Me fala seu nome e de onde é... e já diz: quer foto ou vídeo primeiro?",
                    "cta": {"show": False}
                })
            }
            st.session_state.messages.append(initial_message)
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "assistant",
                json.dumps({
                    "text": initial_message["content"],
                    "cta": {"show": False}
                })
            )

    @staticmethod
    def format_conversation_history(messages: List[Dict], max_messages: int = 10) -> str:
        formatted = []
        for msg in messages[-max_messages:]:
            role = "Cliente" if msg["role"] == "user" else "Mylle"
            content = msg["content"]
            if content.startswith('{"text"'):
                try:
                    content_data = json.loads(content)
                    if isinstance(content_data, dict):
                        content = content_data.get("text", content)
                except:
                    pass
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    @staticmethod
    def display_chat_history() -> None:
        chat_container = st.container()
        with chat_container:
            for idx, msg in enumerate(st.session_state.messages[-12:]):
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="😎"):
                        st.markdown(f"""
                        <div style="background: rgba(255, 102, 179, 0.15);padding: 12px;border-radius: 18px 18px 0 18px;margin: 5px 0;color: white;">
                            {msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    try:
                        content_data = json.loads(msg["content"])
                        if isinstance(content_data, dict):
                            with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                                st.markdown(f"""
                                <div style="background: linear-gradient(45deg, #ff66b3, #ff1493);color: white;padding: 12px;border-radius: 18px 18px 18px 0;margin: 5px 0;">
                                    {content_data.get("text", "")}
                                </div>
                                """, unsafe_allow_html=True)
                                if content_data.get("audio"):
                                    UiService.show_audio_player(content_data["audio"])
                                if content_data.get("cta", {}).get("show") and idx == len(st.session_state.messages[-12:]) - 1:
                                    cta_data = content_data.get("cta", {})
                                    if st.button(cta_data.get("label", "🎁 Ver Conteúdo"),
                                                key=f"cta_button_{hash(msg['content'])}",
                                                use_container_width=True,
                                                type="primary"):
                                        st.session_state.current_page = cta_data.get("target", "offers")
                                        save_persistent_data()
                                        st.rerun()
                    except:
                        with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                            st.markdown(f"""
                            <div style="background: linear-gradient(45deg, #ff66b3, #ff1493);color: white;padding: 12px;border-radius: 18px 18px 18px 0;margin: 5px 0;">
                                {msg["content"]}
                            </div>
                            """, unsafe_allow_html=True)

    @staticmethod
    def process_user_input(conn: sqlite3.Connection) -> None:
        ChatService.display_chat_history()
        # Exibir amostras grátis se for início
        if len(st.session_state.messages) == 2 and not st.session_state.get("samples_shown"):
            show_samples_gallery()
            st.session_state.samples_shown = True
        # Buffer de mensagem picada
        user_input = get_buffered_input()
        if user_input is None:
            return
        # Anti-fake
        anti_fake = check_anti_fake(user_input)
        if anti_fake:
            with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                st.markdown(anti_fake["text"])
                UiService.show_audio_player(anti_fake["audio"])
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(anti_fake)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(anti_fake))
            save_persistent_data()
            return
        # Conversão acelerada e explicação do acesso
        conv = resposta_para_conversao(user_input)
        if conv:
            with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                st.markdown(conv["text"])
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(conv)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(conv))
            save_persistent_data()
            return
        # Fallback para fluxo normal, sempre termina incentivando ou perguntando algo
        resposta = ApiService.ask_gemini(user_input, st.session_state.session_id, conn)
        if isinstance(resposta, str):
            resposta = {"text": resposta, "cta": {"show": False}}
        elif "text" not in resposta:
            resposta = {"text": str(resposta), "cta": {"show": False}}
        perguntas = [
            "O que você quer ver primeiro: fotos ou vídeos? 😏",
            "Me fala seu e-mail pra liberar seu pack rapidinho!",
            "Qual pack você acha que combina mais com você?",
            "Curtiu minha amostra? Quer ver mais?",
            "Me diz: você é mais safado ou romântico?",
            "Conta, já ficou com vontade ou precisa de mais um empurrãozinho?"
        ]
        if not any(q in resposta["text"] for q in perguntas):
            resposta["text"] = resposta["text"].strip() + " " + random.choice(perguntas)
        with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
            st.markdown(resposta["text"])
            if resposta.get("audio"):
                UiService.show_audio_player(resposta["audio"])
                st.session_state.audio_count += 1
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
        DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(resposta))
        save_persistent_data()

# ======================
# PÁGINAS DE NAVEGAÇÃO
# ======================
class NewPages:
    @staticmethod
    def show_home_page() -> None:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e0033, #3c0066);padding: 50px 20px;text-align: center;border-radius: 15px;color: white;margin-bottom: 30px;border: 2px solid #ff66b3;box-shadow: 0 8px 25px rgba(255, 102, 179, 0.2);">
            <h1 style="color: #ff66b3; margin-bottom: 10px;">Mylle Alves</h1>
            <p style="font-size: 1.1em; opacity: 0.9;">Sua especialista em conteúdo adulto premium 🔥</p>
            <p style="font-size: 0.9em; opacity: 0.7; margin-top: 10px;">Aqui eu comando - você obedece 😈</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💬 Iniciar Conversa com Mylle", use_container_width=True, type="primary"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def show_gallery_page() -> None:
        st.markdown("""
        <div style="background: rgba(255, 20, 147, 0.1);padding: 15px;border-radius: 10px;margin-bottom: 20px;text-align: center;">
            <h3 style="color: #ff66b3; margin: 0;">✨ Preview Exclusivo</h3>
            <p style="color: #aaa; margin: 5px 0 0; font-size: 0.9em;">Uma amostra do que te espera nos packs VIP</p>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            with col:
                st.image(Config.IMG_GALLERY[idx % len(Config.IMG_GALLERY)], use_container_width=True, caption=f"💎 Preview #{idx+1}")
                st.markdown("""<div style="text-align:center; color: #ff66b3; margin-top: -10px;">✨ Exclusivo VIP</div>""", unsafe_allow_html=True)
        st.markdown("---")
        show_samples_gallery()
        st.markdown("""
        <div style="text-align: center; margin: 20px 0;">
            <p style="color: #ff66b3; font-style: italic;">"Isso é só uma amostra... imagina o que te espera nos packs completos 😈"</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Quero Ver Tudo Agora", key="vip_button_gallery", use_container_width=True, type="primary"):
            st.session_state.current_page = "offers"
            st.rerun()
        if st.button("💬 Voltar ao Chat", key="back_from_gallery"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def show_offers_page() -> None:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #ff66b3; display: inline-block; padding-bottom: 5px;">
                🎁 Packs VIP Exclusivos
            </h2>
            <p style="color: #aaa; margin-top: 5px;">Escolha como você quer me ver... 😈</p>
        </div>
        """, unsafe_allow_html=True)
        packages = [
            {
                "name": "TARADINHA",
                "price": "R$ 29,99",
                "benefits": ["15 fotos exclusivas", "15 vídeos quentes", "Acesso por 30 dias"],
                "color": "#ff66b3",
                "link": Config.CHECKOUT_TARADINHA,
                "image": Config.PACK_IMAGES["TARADINHA"],
                "tag": "🔥 Mais Popular"
            },
            {
                "name": "MOLHADINHA",
                "price": "R$ 49,99", 
                "benefits": ["25 fotos sensuais", "25 vídeos especiais", "Acesso por 60 dias", "Conteúdo 4K"],
                "color": "#9400d3",
                "link": Config.CHECKOUT_MOLHADINHA,
                "image": Config.PACK_IMAGES["MOLHADINHA"],
                "tag": "💎 Premium"
            },
            {
                "name": "SAFADINHA",
                "price": "R$ 69,99",
                "benefits": ["40 fotos ultra-exclusivas", "40 vídeos premium", "Acesso vitalício", "Conteúdo 4K", "Updates gratuitos"],
                "color": "#ff0066",
                "link": Config.CHECKOUT_SAFADINHA,
                "image": Config.PACK_IMAGES["SAFADINHA"],
                "tag": "👑 VIP"
            }
        ]
        cols = st.columns(3)
        for idx, (col, package) in enumerate(zip(cols, packages)):
            with col:
                st.markdown(f"""
                <div style="background: rgba(30, 0, 51, 0.3);border-radius: 15px;padding: 20px;border: 2px solid {package['color']};min-height: 480px;position: relative;transition: all 0.3s;box-shadow: 0 5px 15px rgba{package['color'].replace('#', '')}20;">
                    <div style="text-align: center; margin-bottom: 15px;">
                        <img src="{package['image']}" style="width: 100%;height: 150px;object-fit: cover;border-radius: 10px;margin-bottom: 15px;">
                        <h3 style="color: {package['color']}; margin: 0 0 5px 0;">{package['name']}</h3>
                        {f'<div style="background: {package["color"]}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.7em; margin-bottom: 8px; display: inline-block;">{package["tag"]}</div>' if package.get('tag') else ''}
                        <div style="font-size: 1.8em; color: {package['color']}; font-weight: bold; margin: 10px 0;">
                            {package['price']}
                        </div>
                    </div>
                    <ul style="padding-left: 20px; text-align: left; margin-bottom: 60px;">
                        {''.join([f'<li style="margin-bottom: 8px; color: #ddd; font-size: 0.9em;">{benefit}</li>' for benefit in package['benefits']])}
                    </ul>
                    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
                        <a href="{package['link']}" target="_blank" style="display: block;background: linear-gradient(45deg, {package['color']}, #ff1493);color: white;text-align: center;padding: 12px;border-radius: 8px;text-decoration: none;font-weight: bold;transition: all 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                            💝 Quero Este Pack!
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; margin: 20px 0;">
            <p style="color: #ff66b3; font-style: italic; font-size: 1.1em;">
                "Não fique só na vontade... escolha seu pack e venha ver TUDO que preparei para você 😈"
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💬 Voltar ao Chat", key="back_from_offers"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

# ======================
# APLICAÇÃO PRINCIPAL
# ======================
def main():
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = DatabaseService.init_db()
    conn = st.session_state.db_conn
    ChatService.initialize_session(conn)
    if not st.session_state.age_verified:
        UiService.age_verification()
        st.stop()
    UiService.setup_sidebar()
    if not st.session_state.connection_complete:
        st.session_state.connection_complete = True
        save_persistent_data()
        st.rerun()
    if not st.session_state.chat_started:
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; margin: 50px 0;">
                <img src="{Config.IMG_PROFILE}" width="140" style="border-radius: 50%; border: 3px solid #ff66b3; box-shadow: 0 5px 15px rgba(255, 102, 179, 0.3);">
                <h2 style="color: #ff66b3; margin-top: 20px;">Mylle Alves</h2>
                <p style="font-size: 1.1em; color: #aaa;">Especialista em conteúdo adulto premium 🔥</p>
                <p style="font-size: 0.9em; color: #666; margin-top: 10px;">Aqui eu comando - você obedece 😈</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("💋 Iniciar Experiência", type="primary", use_container_width=True):
                st.session_state.update({'chat_started': True, 'current_page': 'chat'})
                save_persistent_data()
                st.rerun()
        st.stop()
    if st.session_state.current_page == "home":
        NewPages.show_home_page()
    elif st.session_state.current_page == "gallery":
        NewPages.show_gallery_page()
    elif st.session_state.current_page == "offers":
        NewPages.show_offers_page()
    else:
        UiService.chat_shortcuts()
        ChatService.process_user_input(conn)
    save_persistent_data()

if __name__ == "__main__":
    main()
