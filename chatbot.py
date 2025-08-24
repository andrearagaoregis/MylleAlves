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

# Estilos CSS (mantidos)
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
    # Áudios disponíveis
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
    # Links de amostras pedidas (o usuário pediu que fossem adicionadas)
    SAMPLES_PAGE_LINKS = [
        "https://ibb.co/MDmGhjnX",
        "https://ibb.co/fGD0zvmY",
        "https://ibb.co/tSVc9Rz"
    ]

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

    @staticmethod
    def load_recent_messages(conn: sqlite3.Connection, user_id: str, limit: int = 40) -> List[Dict]:
        # Usado para reconstituir o contexto caso a sessão seja resetada
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM conversations 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        rows = c.fetchall()
        rows.reverse()  # voltar na ordem cronológica
        return [{"role": row[0], "content": row[1]} for row in rows]

# ======================
# PERSISTÊNCIA DE ESTADO (SINGLETON)
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

# ======================
# HELPERS DE SESSÃO
# ======================
def get_user_id() -> str:
    if 'user_id' not in st.session_state:
        query_uid = st.experimental_get_query_params().get('uid', [None])[0]
        if not query_uid:
            user_id = str(uuid.uuid4())
            st.experimental_set_query_params(uid=user_id)
        else:
            user_id = query_uid
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
        'user_info_collected', 'last_user_message_time', 'audio_count', 'samples_shown', 'input_buffer'
    ]
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    db.save_state(user_id, new_data)

# ======================
# PERSONA (EM 1ª PESSOA)
# ======================
class PersonaText:
    MYLLE = (
        "Eu sou a Mylle, sua criadora de conteúdo premium. Meus packs são feitos pra te deixar maluco de tesão. "
        "Adoro provocar, mas aqui comigo é direto ao ponto: não fico enrolando, quero ver você decidir logo e garantir seu acesso! "
        "Respondo curto, pergunto o que importa e mando áudio quando preciso provar que sou real. O acesso é enviado pro e-mail depois da compra. "
    )

# ======================
# UTILITÁRIOS PARA MELHORIAS
# ======================
def normalized_text_from_content(content: str) -> str:
    """Se content for JSON string com 'text', retorna o texto; senão retorna content bruto."""
    if isinstance(content, str):
        try:
            obj = json.loads(content)
            if isinstance(obj, dict) and "text" in obj:
                return obj.get("text", "")
        except Exception:
            pass
    return content

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

def show_samples_gallery():
    st.markdown("""
    <div style="background:rgba(255,20,147,0.09);padding:12px;border-radius:11px;text-align:center;">
        <p style="color:#ff66b3;font-weight:bold;">Provinha grátis só pra te deixar com mais vontade...</p>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    for i, col in enumerate(cols):
        with col:
            # Mostramos uma prévia genérica (IMG_PREVIEW) e um link direto à página do ibb.co conforme pedido
            st.image(Config.IMG_PREVIEW, use_column_width=True, caption=f"Amostra #{i+1}")
            st.markdown(f"""<div style="text-align:center;margin-top:6px;"><a href="{Config.SAMPLES_PAGE_LINKS[i]}" target="_blank" style="color:#ff66b3;">Ver amostra #{i+1}</a></div>""", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#ff66b3;margin-top:6px;">
        <b>Só o proibido mesmo tá nos packs VIP. Bora liberar?</b>
    </div>
    """, unsafe_allow_html=True)

# ======================
# BUFFER DE MENSAGENS PICADAS (ANTI-BUG)
# ======================
def get_buffered_input(timeout: float = 2.5) -> Optional[str]:
    """
    Junta mensagens fragmentadas enviadas em sequência rápida (< timeout segundos).
    Retorna None enquanto espera por fragmentos; retorna a mensagem completa assim que considera que está completa.
    """
    if "input_buffer" not in st.session_state:
        st.session_state.input_buffer = []
        st.session_state.buffer_last_time = 0.0

    user_input = st.chat_input("💬 Digite sua mensagem...", key="chat_input")
    if not user_input:
        return None

    now = time.time()
    last_time = st.session_state.get("buffer_last_time", 0.0)

    # Se envio rápido após o anterior, acumula
    if (now - last_time) <= timeout and st.session_state.input_buffer:
        st.session_state.input_buffer.append(user_input)
        st.session_state.buffer_last_time = now
        # aguardamos mais por fragmentos
        return None
    else:
        if st.session_state.input_buffer:
            # juntar buffer + novo input e limpar
            full_msg = " ".join(st.session_state.input_buffer + [user_input])
            st.session_state.input_buffer = []
            st.session_state.buffer_last_time = 0.0
            return full_msg
        else:
            # Sem buffer anterior, iniciar buffer com este input e retornar imediatamente
            st.session_state.buffer_last_time = now
            return user_input

# ======================
# RESPOSTAS RÁPIDAS (ANTI-FAKE E CONVERSÃO)
# ======================
def anti_fake_response(user_input: str) -> Optional[Dict]:
    if any(word in user_input.lower() for word in ["fake", "falsa", "bot", "robô", "artificial", "não é real", "é mentira"]):
        hora = datetime.now().hour
        if 5 <= hora < 12:
            audio = "bom_dia_nao_sou_fake"
        elif 12 <= hora < 18:
            audio = "boa_tarde_nao_sou_fake"
        else:
            audio = "boa_noite_nao_sou_fake"
        return {
            "text": random.choice([
                "Eu sou real sim, amor. Ouve minha voz pra não restar dúvida 😘",
                "Nada de fake aqui, pode confiar. Ouve meu áudio e tenta não delirar... 😏",
                "Sou eu mesma, viu? Quer ouvir pra acreditar? 😘"
            ]),
            "audio": audio,
            "cta": {"show": False}
        }
    return None

def conversion_quick_reply(user_input: str) -> Optional[Dict]:
    if any(word in user_input.lower() for word in ["pack", "packs", "conteúdo", "foto", "vídeo", "bão", "nude", "mostrar", "preço", "comprar", "acesso"]):
        return {
            "text": "Quer ver tudo? Só nos meus packs VIP. Assim que comprar, eu habilito o acesso direto pro seu e-mail. Quer que eu te mostre as opções agora?",
            "cta": {"show": True, "label": "🚀 Ver Packs VIP", "target": "offers"}
        }
    return None

# ======================
# SERVIÇO API (GEMINI) - COM FALLBACK
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=200)
    def ask_gemini(prompt: str, session_id: str, conn: sqlite3.Connection) -> Dict:
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn: sqlite3.Connection) -> Dict:
        # Exibir status curto
        status_container = st.empty()
        try:
            UiService.show_status_effect(status_container, "typing")
        except Exception:
            pass

        conversation_history = ChatService.format_conversation_history(st.session_state.get("messages", []))
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{PersonaText.MYLLE}\n\nHistórico:\n{conversation_history}\n\nÚltima: {prompt}\n\nINSTRUÇÕES: responda curto (1-2 frases), sempre em primeira pessoa, incentive a comprar quando for relevante, explique que o acesso é enviado por e-mail após a compra, e termine com uma pergunta ou call-to-action."}]
                }
            ],
            "generationConfig": {
                "temperature": 1.05,
                "topP": 0.9,
                "topK": 40
            }
        }
        try:
            resp = requests.post(Config.API_URL, headers=headers, json=data, timeout=Config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            gemini_text = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            # tentar parsear JSON se o modelo devolveu
            try:
                if '```json' in gemini_text:
                    parsed = json.loads(gemini_text.split('```json')[1].split('```')[0].strip())
                else:
                    parsed = json.loads(gemini_text)
                return parsed
            except Exception:
                # fallback simples: devolver texto em formato esperado
                return {"text": gemini_text.strip(), "cta": {"show": False}}
        except Exception as e:
            # fallback local: respostas curtas com chamada para conversão
            fallback_texts = [
                "Que delícia... 😏 Quer ver fotos ou vídeos primeiro?",
                "Tá com vontade, né? Posso te mostrar os packs agora e liberar pelo seu e-mail.",
                "Curtiu minha amostra? Se quiser tudo, é só garantir um pack que eu libero por e-mail."
            ]
            return {"text": random.choice(fallback_texts), "cta": {"show": True, "label": "🎁 Ver Conteúdo", "target": "offers"}}
        finally:
            status_container.empty()

# ======================
# UI SERVICE (STATUS, ÁUDIO, SIDEBAR, ETC)
# ======================
class UiService:
    @staticmethod
    def show_status_effect(container, status_type: str) -> None:
        status_messages = {"viewed": "Visto", "typing": "Digitando..."}
        message = status_messages.get(status_type, "...")
        dots = ""
        start_time = time.time()
        duration = 1.0 if status_type == "viewed" else 1.6
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            if status_type == "typing":
                dots = "." * (int(elapsed * 3) % 4)
            container.markdown(f"""
            <div style="color: #888; font-size: 0.8em; padding: 2px 8px; border-radius: 10px; background: rgba(0,0,0,0.05); display:inline-block;">
                {message}{dots}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.25)
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
            <div style="text-align:center;margin:1rem 0;">
                <img src="{Config.IMG_PROFILE}" alt="Mylle Alves" style="border-radius:50%;border:3px solid #ff66b3;width:100px;height:100px;object-fit:cover;margin-bottom:10px;">
                <h3 style="color:#ff66b3;margin:0;">Mylle Alves</h3>
                <p style="color:#aaa;margin:0;font-size:0.9em;">Online agora 💚</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            for platform, url in Config.SOCIAL_LINKS.items():
                if st.button(Config.SOCIAL_ICONS.get(platform, platform), key=f"sidebar_{platform}", use_container_width=True):
                    st.components.v1.html(f"<script>window.open('{url}', '_blank')</script>")
            st.markdown("---")
            menu_options = {"💋 Início": "home", "📸 Preview": "gallery", "🎁 Packs VIP": "offers"}
            for label, page in menu_options.items():
                if st.button(label, key=f"menu_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    save_persistent_data()
                    st.rerun()
            st.markdown("---")
            st.markdown("<div style='text-align:center;color:#888;font-size:0.8em;'>© 2024 Mylle Alves Premium</div>", unsafe_allow_html=True)

# ======================
# CHAT SERVICE (LÓGICA PRINCIPAL)
# ======================
class ChatService:
    @staticmethod
    def initialize_session(conn: sqlite3.Connection) -> None:
        load_persistent_data()
        # garantir session_id persistente
        if 'session_id' not in st.session_state or not st.session_state.get('session_id'):
            st.session_state.session_id = str(random.randint(100000, 999999))
        # defaults
        defaults = {
            'age_verified': False,
            'connection_complete': False,
            'chat_started': False,
            'current_page': 'home',
            'last_cta_time': 0,
            'preview_shown': False,
            'messages': [],
            'request_count': 0,
            'conversation_stage': 'approach',
            'lead_name': None,
            'last_interaction_time': time.time(),
            'user_info_collected': False,
            'last_user_message_time': time.time(),
            'audio_count': 0,
            'samples_shown': False,
            'input_buffer': []
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

        # carregar mensagens da sessão atual
        msgs = DatabaseService.load_messages(conn, get_user_id(), st.session_state.get('session_id', ''))
        if msgs:
            st.session_state.messages = msgs
        else:
            # tentar restaurar contexto recente do DB caso o chat tenha sido resetado
            recent = DatabaseService.load_recent_messages(conn, get_user_id(), limit=60)
            if recent:
                st.session_state.messages = recent
                # marca que restauramos para o usuário entender se quiser
                if not st.session_state.get('connection_complete'):
                    st.session_state.connection_complete = True

        # se conversa estiver vazia e chat_started True, iniciar com mensagem de abertura
        if len(st.session_state.messages) == 0 and st.session_state.chat_started:
            typing = st.empty()
            try:
                UiService.show_status_effect(typing, "typing")
            except Exception:
                pass
            initial_text = "Oi, já tava esperando você aqui! 😏 Me fala seu nome e de onde é... e diz: fotos ou vídeos primeiro?"
            assistant_msg = {"text": initial_text, "cta": {"show": False}}
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(assistant_msg)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(assistant_msg))
            save_persistent_data()

    @staticmethod
    def format_conversation_history(messages: List[Dict], max_messages: int = 10) -> str:
        formatted = []
        for msg in messages[-max_messages:]:
            role = "Cliente" if msg.get("role") == "user" else "Mylle"
            content = normalized_text_from_content(msg.get("content", ""))
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    @staticmethod
    def display_chat_history() -> None:
        # Mostra as últimas mensagens (renderizando JSON de assistant quando aplicável)
        for idx, msg in enumerate(st.session_state.get("messages", [])[-30:]):
            role = msg.get("role")
            raw = msg.get("content", "")
            # tentar parsear JSON
            parsed_text = normalized_text_from_content(raw)
            if role == "user":
                with st.chat_message("user", avatar="😎"):
                    st.markdown(f"""
                    <div style="background: rgba(255, 102, 179, 0.12); padding: 10px; border-radius: 14px; color:white;">
                        {parsed_text}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                try:
                    data = json.loads(raw)
                    text = data.get("text", "")
                    audio = data.get("audio")
                    cta = data.get("cta", {})
                    with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                        st.markdown(f"""
                        <div style="background: linear-gradient(45deg, #ff66b3, #ff1493); padding: 12px; border-radius: 14px; color:white;">
                            {text}
                        </div>
                        """, unsafe_allow_html=True)
                        if audio:
                            show_audio_player(audio)
                        if cta.get("show"):
                            label = cta.get("label", "🎁 Ver Conteúdo")
                            target = cta.get("target", "offers")
                            if st.button(label, key=f"cta_{hash(raw)}", use_container_width=True):
                                st.session_state.current_page = target
                                save_persistent_data()
                                st.rerun()
                except Exception:
                    # fallback: texto simples
                    with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                        st.markdown(f"""
                        <div style="background: linear-gradient(45deg, #ff66b3, #ff1493); padding: 12px; border-radius: 14px; color:white;">
                            {parsed_text}
                        </div>
                        """, unsafe_allow_html=True)

    @staticmethod
    def process_user_input(conn: sqlite3.Connection) -> None:
        # render do histórico
        ChatService.display_chat_history()

        # mostrar amostras no começo, se ainda não mostradas
        if len(st.session_state.get("messages", [])) <= 2 and not st.session_state.get("samples_shown", False):
            show_samples_gallery()
            st.session_state.samples_shown = True

        # coletar input com buffer anti-picadas
        user_input = get_buffered_input()
        if user_input is None:
            return  # aguardando mais fragmentos ou input

        cleaned_input = re.sub(r'<[^>]*>', '', user_input).strip()[:800]
        # limites de requests por sessão
        st.session_state.request_count = st.session_state.get("request_count", 0)
        if st.session_state.request_count >= Config.MAX_REQUESTS_PER_SESSION:
            limit_msg = {"text": "Por hoje chega, gato 😘 Volto amanhã com mais safadeza pra você!", "cta": {"show": False}}
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(limit_msg)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(limit_msg))
            save_persistent_data()
            st.rerun()
            return

        # salvar entrada do usuário
        st.session_state.messages.append({"role": "user", "content": cleaned_input})
        DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "user", cleaned_input)
        st.session_state.request_count += 1
        st.session_state.last_interaction_time = time.time()
        st.session_state.last_user_message_time = time.time()

        # Anti-fake: resposta rápida e áudio
        anti = anti_fake_response(cleaned_input)
        if anti:
            with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                st.markdown(anti["text"])
                show_audio_player(anti["audio"])
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(anti)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(anti))
            save_persistent_data()
            return

        # Conversão rápida + explicação de e-mail
        conv = conversion_quick_reply(cleaned_input)
        if conv:
            with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
                st.markdown(conv["text"])
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(conv)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(conv))
            save_persistent_data()
            # Se CTA visível e o usuário clicar, a navegação é tratada no render de histórico (botão)
            return

        # fallback para API/Gemini
        resposta = ApiService.ask_gemini(cleaned_input, st.session_state.session_id, conn)
        if isinstance(resposta, str):
            resposta = {"text": resposta, "cta": {"show": False}}
        elif "text" not in resposta:
            resposta = {"text": str(resposta), "cta": {"show": False}}

        # garantir que termine com pergunta ou call-to-action curta
        follow_ups = [
            "O que você quer ver primeiro: fotos ou vídeos? 😏",
            "Me fala seu e-mail pra liberar seu pack rapidinho!",
            "Qual pack você acha que combina mais com você?",
            "Curtiu a amostra? Quer ver mais?",
        ]
        if not any(fq in resposta["text"] for fq in follow_ups):
            resposta["text"] = resposta["text"].strip()
            # evitar duplicar pergunta se já houver pontuação
            if not resposta["text"].endswith(("?", "!", "…")):
                resposta["text"] += " "
            resposta["text"] += random.choice(follow_ups)

        # renderizar resposta
        with st.chat_message("assistant", avatar=Config.IMG_PROFILE):
            st.markdown(resposta["text"])
            if resposta.get("audio"):
                show_audio_player(resposta["audio"])
                st.session_state.audio_count = st.session_state.get("audio_count", 0) + 1

        # salvar resposta
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
        DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(resposta))
        save_persistent_data()

# ======================
# NOVAS PAGINAS (HOME / GALERIA / OFFERS)
# ======================
class NewPages:
    @staticmethod
    def show_home_page() -> None:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e0033, #3c0066); padding:50px 20px; text-align:center; border-radius:15px; color:white; margin-bottom:30px; border:2px solid #ff66b3;">
            <h1 style="color:#ff66b3; margin-bottom:10px;">Mylle Alves</h1>
            <p style="font-size:1.1em; opacity:0.9;">Sua especialista em conteúdo adulto premium 🔥</p>
            <p style="font-size:0.9em; opacity:0.7; margin-top:10px;">Aqui eu comando - você obedece 😈</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💬 Iniciar Conversa com Mylle", use_container_width=True, type="primary"):
            st.session_state.current_page = "chat"
            st.session_state.chat_started = True
            save_persistent_data()
            st.rerun()

    @staticmethod
    def show_gallery_page() -> None:
        st.markdown("""
        <div style="background: rgba(255, 20, 147, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align:center;">
            <h3 style="color:#ff66b3; margin:0;">✨ Preview Exclusivo</h3>
            <p style="color:#aaa; margin-top:5px; font-size:0.9em;">Uma amostra do que te espera nos packs VIP</p>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            with col:
                st.image(Config.IMG_GALLERY[idx % len(Config.IMG_GALLERY)], use_column_width=True, caption=f"💎 Preview #{idx+1}")
                st.markdown("<div style='text-align:center;color:#ff66b3;margin-top:-10px;'>✨ Exclusivo VIP</div>", unsafe_allow_html=True)
        st.markdown("---")
        show_samples_gallery()
        if st.button("🚀 Quero Ver Tudo Agora", key="vip_button_gallery", use_container_width=True, type="primary"):
            st.session_state.current_page = "offers"
            save_persistent_data()
            st.rerun()
        if st.button("💬 Voltar ao Chat", key="back_from_gallery"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def show_offers_page() -> None:
        st.markdown("""
        <div style="text-align:center;margin-bottom:30px;">
            <h2 style="color:#ff66b3; display:inline-block;">🎁 Packs VIP Exclusivos</h2>
            <p style="color:#aaa; margin-top:5px;">Escolha como você quer me ver... 😈</p>
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
        for idx, (col, pack) in enumerate(zip(cols, packages)):
            with col:
                st.markdown(f"""
                <div style="background: rgba(30,0,51,0.3); border-radius:15px; padding:20px; border:2px solid {pack['color']}; min-height:480px; position:relative;">
                    <img src="{pack['image']}" style="width:100%; height:150px; object-fit:cover; border-radius:10px; margin-bottom:12px;">
                    <h3 style="color:{pack['color']}; margin:6px 0;">{pack['name']}</h3>
                    <div style="font-size:1.6em; color:{pack['color']}; font-weight:bold; margin:8px 0;">{pack['price']}</div>
                    <ul style="padding-left:20px; text-align:left;">
                        {''.join([f'<li style="color:#ddd;margin-bottom:6px;">{b}</li>' for b in pack['benefits']])}
                    </ul>
                    <div style="position:absolute; bottom:20px; left:20px; right:20px;">
                        <a href="{pack['link']}" target="_blank" style="display:block; background: linear-gradient(45deg, {pack['color']}, #ff1493); color:white; padding:12px; border-radius:8px; text-align:center; text-decoration:none; font-weight:bold;">💝 Quero Este Pack!</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        if st.button("💬 Voltar ao Chat", key="back_from_offers"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

# ======================
# APLICATIVO (MAIN)
# ======================
def main():
    # DB init
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = DatabaseService.init_db()
    conn = st.session_state.db_conn

    # inicialização de sessão e carregamento de dados persistentes
    ChatService.initialize_session(conn)

    # exigir verificação de idade
    if not st.session_state.get("age_verified", False):
        UiService.age_verification()
        st.stop()

    UiService.setup_sidebar()

    # Se primeira conexão, executar pequeno efeito (controlado por flag)
    if not st.session_state.get("connection_complete", False):
        try:
            container = st.empty()
            UiService.show_status_effect(container, "viewed")
            UiService.show_status_effect(container, "typing")
        except Exception:
            pass
        st.session_state.connection_complete = True
        save_persistent_data()
        # não rerun imediatamente para evitar loop

    # se chat não iniciado, mostrar cartão inicial
    if not st.session_state.get("chat_started", False):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align:center;margin:50px 0;">
                <img src="{Config.IMG_PROFILE}" width="140" style="border-radius:50%; border:3px solid #ff66b3;">
                <h2 style="color:#ff66b3; margin-top:20px;">Mylle Alves</h2>
                <p style="color:#aaa; margin:0.2rem 0;">Especialista em conteúdo adulto premium 🔥</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("💋 Iniciar Experiência", type="primary", use_container_width=True):
                st.session_state.chat_started = True
                st.session_state.current_page = "chat"
                save_persistent_data()
                st.rerun()
        st.stop()

    # rotas de páginas
    page = st.session_state.get("current_page", "chat")
    if page == "home":
        NewPages.show_home_page()
    elif page == "gallery":
        NewPages.show_gallery_page()
    elif page == "offers":
        NewPages.show_offers_page()
    else:
        # UI de chat curto e processamento
        ChatService.display_chat_history()
        ChatService.process_user_input(conn)

    save_persistent_data()

if __name__ == "__main__":
    main()
