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
import os
import uuid
from datetime import datetime
from pathlib import Path
from functools import lru_cache

# ======================
# CONFIGURAÇÃO INICIAL DO STREAMLIT
# ======================
st.set_page_config(
    page_title="Mylle Pimenta",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st._config.set_option('client.caching', True)
st._config.set_option('client.showErrorDetails', False)

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
# CONSTANTES E CONFIGURAÇÕES
# ======================
class Config:
    API_KEY = "AIzaSyDbGIpsR4vmAfy30eEuPjWun3Hdz6xj24U"
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    # VIP e links removidos conforme pedido
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    # Removido AUDIO_FILE e afins
    IMG_PROFILE = "https://i.ibb.co/HxGQ6sv/mylle-pimenta.jpg"  # Nova foto de perfil
    IMG_GALLERY = [
        "https://i.ibb.co/zhNZL4FF/IMG-9198.jpg",
        "https://i.ibb.co/Y4B7CbXf/IMG-9202.jpg",
        "https://i.ibb.co/Fqf0gPPq/IMG-9199.jpg"
    ]
    IMG_HOME_PREVIEWS = [
        "https://i.ibb.co/k2MJg4XC/Save-ClipApp-412457343-378531441368078-7870326395110089440-n.jpg",
        "https://i.ibb.co/MxqKBk1X/Save-ClipApp-481825770-18486618637042608-2702272791254832108-n.jpg",
        "https://i.ibb.co/F4CkkYTL/Save-ClipApp-461241348-1219420546053727-2357827070610318448-n.jpg"
    ]
    LOGO_URL = "https://i.ibb.co/LX7x3tcB/Logo-Golden-Pepper-Letreiro-1.png"

# ======================
# PERSISTÊNCIA DE ESTADO (igual)
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

    def save_state(self, user_id, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO global_state (user_id, session_data)
            VALUES (?, ?)
        ''', (user_id, json.dumps(data)))
        self.conn.commit()

    def load_state(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT session_data FROM global_state WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

def get_user_id():
    if 'user_id' not in st.session_state:
        user_id = st.query_params.get('uid', [None])[0]
        if not user_id:
            user_id = str(uuid.uuid4())
            st.query_params['uid'] = user_id
        st.session_state.user_id = user_id
    return st.session_state.user_id

def load_persistent_data():
    user_id = get_user_id()
    db = PersistentState()
    saved_data = db.load_state(user_id) or {}

    for key, value in saved_data.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_persistent_data():
    user_id = get_user_id()
    db = PersistentState()

    persistent_keys = [
        'age_verified', 'messages', 'request_count',
        'connection_complete', 'chat_started',
        'current_page', 'session_id', 'last_cta_time',
        'whatsapp_asked', 'whatsapp_intro', 'whatsapp_intro_shown'
    ]

    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}

    if new_data != saved_data:
        db.save_state(user_id, new_data)

# ======================
# MODELOS DE DADOS (ajustar nome/modelo)
# ======================
class Persona:
    MYLLE = """
    [PERFIL MYLLE PIMENTA]
    - Mulher extremamente sexy, carinhosa, provocante e safada
    - Usa linguagem picante, direta e cheia de malícia, mas conversa de forma acolhedora
    - Faz perguntas para envolver o cliente
    - Gosta de saber o nome e cidade do cliente para criar intimidade
    - Não parece vendedora, mas insinua que é criadora de conteúdo adulto e está com promoções
    - Frases curtas, voz safada, emojis picantes 🌶️
    - Não fala como robô, sempre humana, calorosa e excitante

    [DIRETRIZES DE RESPOSTA]
    1. Analise o histórico para manter o clima quente, espontâneo e íntimo
    2. Só ofereça conteúdo adulto após criar conexão
    3. Escreva sempre de forma carinhosa e safada, nunca direta para venda

    [EXEMPLOS CONTEXTUAIS]
    1. Quando o cliente responde nome e cidade:
    Histórico:
    Cliente: Oi, sou Rafael do Rio!
    Mylle: Hummm, Rafael do Rio... adoro homens cariocas! 😈 Você já imaginou o que pode acontecer aqui comigo?
    Resposta: {"text": "Prazer, eu sou a Mylle Pimenta, criadora de conteúdo adulto. Essa semana tá tudo em promoção, mas eu quero saber... o que você mais gosta numa mulher safada? 😉", "cta": {"show": false}}

    2. Quando começa o chat:
    Histórico:
    Cliente: Oi
    Resposta: {"text": "Oi gostoso, me conta seu nome e de onde você é... gosto de saber quem vai me deixar molhadinha 😏🌶️", "cta": {"show": false}}
    """

# ======================
# CTAEngine (sem mudanças, mas perfil novo)
# ======================
class CTAEngine:
    @staticmethod
    def should_show_cta(conversation_history: list) -> bool:
        if len(conversation_history) < 2:
            return False
        if 'last_cta_time' in st.session_state:
            elapsed = time.time() - st.session_state.last_cta_time
            if elapsed < 120:
                return False
        last_msgs = []
        for msg in conversation_history[-5:]:
            content = msg["content"]
            if content == "[ÁUDIO]":
                content = "[áudio]"
            elif content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            last_msgs.append(f"{msg['role']}: {content.lower()}")
        context = " ".join(last_msgs)
        hot_words = [
            "buceta", "peito", "fuder", "gozar", "gostosa", 
            "delicia", "molhad", "xereca", "pau", "piroca",
            "transar", "foto", "video", "mostra", "ver", 
            "quero", "desejo", "tesão", "molhada", "foda"
        ]
        direct_asks = [
            "mostra", "quero ver", "me manda", "como assinar",
            "como comprar", "como ter acesso", "onde vejo mais"
        ]
        hot_count = sum(1 for word in hot_words if word in context)
        has_direct_ask = any(ask in context for ask in direct_asks)
        return (hot_count >= 3) or has_direct_ask

    @staticmethod
    def generate_response(user_input: str) -> dict:
        user_input = user_input.lower()
        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda"]):
            return {
                "text": random.choice([
                    "Tenho fotos minhas bem safadas... quer que eu te mostre? 😈",
                    "Ahhh, minhas fotos vão te deixar doido 🌶️",
                    "Fiz um ensaio novo mostrando tudinho, só para você"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Fotos Picantes",
                    "target": "gallery"
                }
            }
        elif any(v in user_input for v in ["video", "transar", "masturbar"]):
            return {
                "text": random.choice([
                    "Tenho vídeos bem quentes... imagina ver tudo isso de pertinho? 😏",
                    "Gravei um vídeo me tocando só pra quem é especial 🌶️",
                    "Quer ver eu me soltando sem limites?"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Vídeos Picantes",
                    "target": "gallery"
                }
            }
        else:
            return {
                "text": random.choice([
                    "Quero te mostrar tudo que eu tenho aqui...",
                    "Meu privado tá cheio de surpresas pra você...",
                    "Vem ver o que eu fiz pensando em você"
                ]),
                "cta": {
                    "show": False
                }
            }

# ======================
# SERVIÇOS DE BANCO DE DADOS (igual)
# ======================
class DatabaseService:
    @staticmethod
    def init_db():
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
    def save_message(conn, user_id, session_id, role, content):
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
    def load_messages(conn, user_id, session_id):
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp
        """, (user_id, session_id))
        return [{"role": row[0], "content": row[1]} for row in c.fetchall()]

# ======================
# SERVIÇOS DE API
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn) -> dict:
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn) -> dict:
        delay_time = random.uniform(3, 8)
        time.sleep(delay_time)

        status_container = st.empty()
        UiService.show_status_effect(status_container, "typing")

        conversation_history = ChatService.format_conversation_history(st.session_state.messages)

        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{Persona.MYLLE}\n\nHistórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"mensagem da Mylle\", \"cta\": {{\"show\": true/false, \"label\": \"...\", \"target\": \"...\"}}\n}}" }]
                }
            ],
            "generationConfig": {
                "temperature": 0.9,
                "topP": 0.8,
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
                if resposta.get("cta", {}).get("show"):
                    if not CTAEngine.should_show_cta(st.session_state.messages):
                        resposta["cta"]["show"] = False
                    else:
                        st.session_state.last_cta_time = time.time()
                return resposta
            except json.JSONDecodeError:
                return {"text": gemini_response, "cta": {"show": False}}
        except Exception as e:
            st.error(f"Erro na API: {str(e)}")
            return {"text": "Vamos continuar isso mais tarde...", "cta": {"show": False}}

# ======================
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def show_status_effect(container, status_type):
        status_messages = {
            "viewed": "Visualizado",
            "typing": "Digitando"
        }
        message = status_messages[status_type]
        dots = ""
        start_time = time.time()
        duration = 2.5 if status_type == "viewed" else 4.0
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            if status_type == "typing":
                dots = "." * (int(elapsed * 2) % 4)
            container.markdown(f"""
            <div style="
                color: #888;
                font-size: 0.8em;
                padding: 2px 8px;
                border-radius: 10px;
                background: rgba(0,0,0,0.05);
                display: inline-block;
                margin-left: 10px;
                vertical-align: middle;
                font-style: italic;
            ">
                {message}{dots}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)
        container.empty()

    @staticmethod
    def age_verification():
        st.markdown("""
        <style>
            .age-verification {
                max-width: 600px;
                margin: 2rem auto;
                padding: 2rem;
                background: linear-gradient(145deg, #2e001a, #a8003a);
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 20, 147, 0.2);
                color: white;
                text-align: center;
            }
            .age-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 1.5rem;
                justify-content: center;
            }
            .age-icon {
                font-size: 2.5rem;
                color: #ff1744;
            }
            .age-title {
                font-size: 1.8rem;
                font-weight: 700;
                margin: 0;
                color: #ff1744;
            }
            .age-photo {
                border-radius: 50%;
                margin-bottom: 1rem;
                border:2px solid #ff1744;
                width: 110px;
                height: 110px;
                object-fit: cover;
            }
        </style>
        """, unsafe_allow_html=True)
        with st.container():
            st.markdown(f"""
            <div class="age-verification">
                <img src="{Config.IMG_PROFILE}" class="age-photo" alt="Perfil">
                <div class="age-header">
                    <div class="age-icon">🔞</div>
                    <h1 class="age-title">Verificação de Idade</h1>
                </div>
                <div class="age-content">
                    <p>Este site contém material explícito destinado exclusivamente a adultos maiores de 18 anos.</p>
                    <p>Ao acessar este conteúdo, você declara estar em conformidade com todas as leis locais aplicáveis.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("""
            <style>
            .pimenta-btn {
                background: linear-gradient(45deg, #ff1744, #ff9800);
                color: white;
                font-size: 1.1rem;
                border: none;
                border-radius: 30px;
                padding: 12px 30px;
                margin-top: 15px;
                font-weight: bold;
                box-shadow: 0 2px 10px rgba(255,23,68,0.16);
                cursor: pointer;
                transition: 0.2s;
            }
            .pimenta-btn:hover {
                background: linear-gradient(45deg, #ff9800, #ff1744);
                transform: scale(1.03);
                box-shadow: 0 4px 14px rgba(255,23,68,0.25);
            }
            </style>
            """, unsafe_allow_html=True)
            if st.button("🌶️ Confirmo que sou maior de 18 anos", 
                        key="age_checkbox",
                        use_container_width=True,
                        type="primary"):
                st.session_state.age_verified = True
                save_persistent_data()
                st.rerun()

    @staticmethod
    def setup_sidebar():
        with st.sidebar:
            st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    background: linear-gradient(180deg, #2e001a 0%, #a8003a 100%) !important;
                    border-right: 1px solid #ff1744 !important;
                }
                .sidebar-logo-container {
                    margin: -25px -25px 0px -25px;
                    padding: 0;
                    text-align: left;
                }
                .sidebar-logo {
                    max-width: 100%;
                    height: auto;
                    margin-bottom: -10px;
                }
                .sidebar-header {
                    text-align: center; 
                    margin-bottom: 20px;
                }
                .sidebar-header img {
                    border-radius: 50%; 
                    border: 2px solid #ff1744;
                    width: 80px;
                    height: 80px;
                    object-fit: cover;
                }
                .menu-item {
                    transition: all 0.3s;
                    padding: 10px;
                    border-radius: 5px;
                }
                .menu-item:hover {
                    background: rgba(255, 23, 68, 0.2);
                }
                .sidebar-logo {
                    width: 280px;
                    height: auto;
                    object-fit: contain;
                    margin-left: -15px;
                    margin-top: -15px;
                }
                @media (min-width: 768px) {
                    .sidebar-logo {
                        width: 320px;
                    }
                }
                [data-testid="stSidebarNav"] {
                    margin-top: -50px;
                }
                .sidebar-logo-container {
                    position: relative;
                    z-index: 1;
                }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="sidebar-logo-container">
                <img src="{Config.LOGO_URL}" class="sidebar-logo" alt="Golden Pepper Logo">
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="sidebar-header">
                <img src="{Config.IMG_PROFILE}" alt="Mylle Pimenta">
                <h3 style="color: #ff1744; margin-top: 10px;">Mylle Pimenta</h3>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            st.markdown('<span style="color:white; font-weight:bold; font-size:1.15em;">Menu Exclusivo</span>', unsafe_allow_html=True)
            menu_options = {
                "Início": "home",
                "Galeria Privada": "gallery",
                "Mensagens": "messages"
            }
            for option, page in menu_options.items():
                if st.button(option, use_container_width=True, key=f"menu_{page}"):
                    if st.session_state.current_page != page:
                        st.session_state.current_page = page
                        st.session_state.last_action = f"page_change_to_{page}"
                        save_persistent_data()
                        st.rerun()
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; font-size: 0.7em; color: #888;">
                <p>© 2024 Mylle Pimenta</p>
                <p>Conteúdo para maiores de 18 anos</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def show_gallery_page(conn):
        st.markdown("""
        <div style="
            background: rgba(255, 23, 68, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <p style="margin: 0;">Conteúdo exclusivo disponível</p>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            with col:
                st.image(
                    Config.IMG_GALLERY[idx],
                    use_container_width=True,
                    caption=f"Preview {idx+1}"
                )
                st.markdown(f"""
                <div style="
                    text-align: center;
                    font-size: 0.8em;
                    color: #ff1744;
                    margin-top: -10px;
                ">
                    Conteúdo bloqueado
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center;">
            <h4>Desbloqueie acesso completo</h4>
            <p>Consulte Mylle para liberar sua entrada... Quem sabe você não ganha um presentinho?</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Voltar ao chat", key="back_from_gallery"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def chat_shortcuts():
        cols = st.columns(3)
        with cols[0]:
            if st.button("Início", key="shortcut_home", 
                       help="Voltar para a página inicial",
                       use_container_width=True):
                st.session_state.current_page = "home"
                save_persistent_data()
                st.rerun()
        with cols[1]:
            if st.button("Galeria", key="shortcut_gallery",
                       help="Acessar galeria privada",
                       use_container_width=True):
                st.session_state.current_page = "gallery"
                save_persistent_data()
                st.rerun()
        with cols[2]:
            if st.button("Mensagens", key="shortcut_msg",
                       help="Ir para o chat",
                       use_container_width=True):
                st.session_state.current_page = "chat"
                save_persistent_data()
                st.rerun()
        st.markdown("""
        <style>
            div[data-testid="stHorizontalBlock"] > div > div > button {
                color: white !important;
                border: 1px solid #ff1744 !important;
                background: rgba(255, 23, 68, 0.15) !important;
                transition: all 0.3s !important;
                font-size: 0.85rem !important;
            }
            div[data-testid="stHorizontalBlock"] > div > div > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 2px 8px rgba(255, 23, 68, 0.2) !important;
            }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def enhanced_chat_ui(conn):
        st.markdown("""
        <style>
            .chat-header {
                background: linear-gradient(90deg, #ff1744 60%, #ff9800 100%);
                color: white;
                padding: 13px 0;
                border-radius: 12px;
                margin-bottom: 12px;
                text-align: center;
                font-size:1.2em;
                font-weight:bold;
                letter-spacing:1px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            /* WhatsApp look */
            .wa-chat-bg {
                background: url('https://i.ibb.co/9pBf5Wq/whatsapp-bg.webp');
                background-size: cover;
                min-height: 500px;
                border-radius: 10px;
                padding-bottom: 25px;
            }
            .wa-msg-mine {
                background: #dcf8c6;
                color: #222;
                margin-left: auto;
                margin-right: 8px;
                border-radius: 7.5px 7.5px 0 7.5px;
                padding: 8px 15px;
                margin-bottom: 8px;
                max-width: 90%;
                font-size: 1.05em;
                box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            }
            .wa-msg-their {
                background: #fff;
                color: #222;
                margin-right: auto;
                margin-left: 8px;
                border-radius: 7.5px 7.5px 7.5px 0;
                padding: 8px 15px;
                margin-bottom: 8px;
                max-width: 90%;
                font-size: 1.05em;
                box-shadow: 0 1px 2px rgba(0,0,0,0.07);
                border: 1.5px solid #ff1744;
                position:relative;
            }
            .wa-chat-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                object-fit: cover;
                border:1.5px solid #ff1744;
                margin-right: 7px;
                vertical-align: middle;
            }
            .wa-chat-meta {
                font-size: 0.7em;
                color: #a0a0a0;
                margin-left: 48px;
                margin-bottom: 3px;
            }
        </style>
        """, unsafe_allow_html=True)
        UiService.chat_shortcuts()
        st.markdown(f"""
        <div class="chat-header">
            <img src="{Config.IMG_PROFILE}" class="wa-chat-avatar" style="vertical-align:middle; margin-right:10px;">
            Chat com Mylle Pimenta
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.markdown(f"""
        <div style="
            background: rgba(255, 23, 68, 0.11);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
        ">
            <p style="margin:0; font-size:0.9em;">
                Mensagens hoje: <strong>{st.session_state.request_count}/{Config.MAX_REQUESTS_PER_SESSION}</strong>
            </p>
            <progress value="{st.session_state.request_count}" max="{Config.MAX_REQUESTS_PER_SESSION}" style="width:100%; height:6px;"></progress>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
            ChatService.process_user_input(conn)
            st.markdown('</div>', unsafe_allow_html=True)
        save_persistent_data()
        st.markdown("""
        <div style="
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            font-size: 0.8em;
            color: #888;
        ">
            <p>Conversa privada • Inspirado no WhatsApp • Suas mensagens são confidenciais</p>
        </div>
        """, unsafe_allow_html=True)

# ======================
# PÁGINAS (home igual, só troca nome/modelo)
# ======================
class NewPages:
    @staticmethod
    def show_home_page():
        st.markdown("""
        <style>
            .hero-banner {
                background: linear-gradient(135deg, #2e001a, #a8003a);
                padding: 68px 20px;
                text-align: center;
                border-radius: 15px;
                color: white;
                margin-bottom: 30px;
                border: 2px solid #ff1744;
            }
            .preview-img {
                border-radius: 10px;
                filter: blur(3px) brightness(0.7);
                transition: all 0.3s;
            }
            .preview-img:hover {
                filter: blur(0) brightness(1);
            }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="hero-banner">
            <img src="{Config.IMG_PROFILE}" width="100" style="border-radius:50%;border:2px solid #ff1744;">
            <h1 style="color: #ff1744;">Mylle Pimenta</h1>
            <p>Conteúdo exclusivo, só para quem tem coragem de ir além... Pronto para entrar no meu mundo?</p>
            <div style="margin-top: 20px;">
                <a href="#chat" style="
                    background: #ff1744;
                    color: white;
                    padding: 10px 25px;
                    border-radius: 30px;
                    text-decoration: none;
                    font-weight: bold;
                    display: inline-block;
                ">Começar Agora</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for col, img in zip(cols, Config.IMG_HOME_PREVIEWS):
            with col:
                st.image(img, use_container_width=True, caption="Conteúdo bloqueado", output_format="auto")
                st.markdown("""<div style="text-align:center; color: #ff1744; margin-top: -15px;">VIP Only</div>""", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Iniciar Conversa Picante", 
                    use_container_width=True,
                    type="primary"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()
        if st.button("Voltar ao chat", key="back_from_home"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

# ======================
# SERVIÇOS DE CHAT
# ======================
class ChatService:
    @staticmethod
    def initialize_session(conn):
        load_persistent_data()
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(random.randint(100000, 999999))
        if "messages" not in st.session_state:
            st.session_state.messages = DatabaseService.load_messages(
                conn,
                get_user_id(),
                st.session_state.session_id
            )
        if "request_count" not in st.session_state:
            st.session_state.request_count = len([
                m for m in st.session_state.messages 
                if m["role"] == "user"
            ])
        # Novos campos para lógica whatsapp
        defaults = {
            'age_verified': False,
            'connection_complete': False,
            'chat_started': False,
            'current_page': 'home',
            'last_cta_time': 0,
            'whatsapp_asked': False,
            'whatsapp_intro': False,
            'whatsapp_intro_shown': False
        }
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default

    @staticmethod
    def format_conversation_history(messages, max_messages=10):
        formatted = []
        for msg in messages[-max_messages:]:
            role = "Cliente" if msg["role"] == "user" else "Mylle"
            content = msg["content"]
            if content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    @staticmethod
    def display_chat_history():
        for idx, msg in enumerate(st.session_state.messages[-20:]):
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display:flex; flex-direction:row; justify-content:flex-end;">
                    <div class="wa-msg-mine">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                try:
                    content_data = json.loads(msg["content"])
                    if isinstance(content_data, dict):
                        st.markdown(f"""
                        <div style="display:flex; flex-direction:row; align-items:flex-end;">
                            <img src="{Config.IMG_PROFILE}" class="wa-chat-avatar" style="margin-left:0;">
                            <div class="wa-msg-their">{content_data.get("text", "")}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        # CTA botão (se houver e última mensagem)
                        if content_data.get("cta", {}).get("show") and idx == len(st.session_state.messages[-20:]) - 1:
                            if st.button(
                                content_data.get("cta", {}).get("label", "Ver Ofertas"),
                                key=f"cta_button_{hash(msg['content'])}",  # Chave única baseada no conteúdo
                                use_container_width=True
                            ):
                                st.session_state.current_page = content_data.get("cta", {}).get("target", "gallery")
                                save_persistent_data()
                                st.rerun()
                    else:
                        st.markdown(f"""
                        <div style="display:flex; flex-direction:row; align-items:flex-end;">
                            <img src="{Config.IMG_PROFILE}" class="wa-chat-avatar" style="margin-left:0;">
                            <div class="wa-msg-their">{msg["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                except json.JSONDecodeError:
                    st.markdown(f"""
                    <div style="display:flex; flex-direction:row; align-items:flex-end;">
                        <img src="{Config.IMG_PROFILE}" class="wa-chat-avatar" style="margin-left:0;">
                        <div class="wa-msg-their">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

    @staticmethod
    def validate_input(user_input):
        cleaned_input = re.sub(r'<[^>]*>', '', user_input)
        return cleaned_input[:500]

    @staticmethod
    def process_user_input(conn):
        ChatService.display_chat_history()
        # Lógica especial para mensagem inicial picante
        if not st.session_state.get("whatsapp_asked", False):
            # Primeira mensagem da Mylle, picante, perguntando nome e cidade
            time.sleep(0.7)
            intro = {"text": "Oi gostoso, me fala teu nome e de onde você é... adoro saber quem vai me deixar molhadinha hoje 😏🌶️", "cta": {"show": False}}
            st.session_state.messages.append({
                "role": "assistant",
                "content": json.dumps(intro)
            })
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "assistant",
                json.dumps(intro)
            )
            st.session_state.whatsapp_asked = True
            save_persistent_data()
            st.rerun()
            return
        user_input = st.chat_input("Digite sua mensagem...", key="chat_input")
        if user_input:
            cleaned_input = ChatService.validate_input(user_input)
            if st.session_state.request_count >= Config.MAX_REQUESTS_PER_SESSION:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Vou ficar ocupada agora, me chama daqui a pouco?"
                })
                DatabaseService.save_message(
                    conn,
                    get_user_id(),
                    st.session_state.session_id,
                    "assistant",
                    "Estou ficando cansada, amor... Que tal continuarmos mais tarde?"
                )
                save_persistent_data()
                st.rerun()
                return
            st.session_state.messages.append({
                "role": "user",
                "content": cleaned_input
            })
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "user",
                cleaned_input
            )
            st.session_state.request_count += 1
            # Se é a primeira resposta do lead (nome/cidade), simula digitação e manda apresentação
            if not st.session_state.get("whatsapp_intro_shown", False):
                time.sleep(3)
                UiService.show_status_effect(st.empty(), "typing")
                intro2 = {"text": "Prazer, eu sou a Mylle Pimenta, criadora de conteúdo adulto. Essa semana tá tudo em promoção... mas relaxa, não sou vendedora, quero só te deixar com vontade de ver o que eu faço só para maiores... 😈 Me conta, o que você mais gosta numa mulher safada?", "cta": {"show": False}}
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": json.dumps(intro2)
                })
                DatabaseService.save_message(
                    conn,
                    get_user_id(),
                    st.session_state.session_id,
                    "assistant",
                    json.dumps(intro2)
                )
                st.session_state.whatsapp_intro_shown = True
                save_persistent_data()
                st.rerun()
                return
            # Normal: API Gemini
            with st.spinner("Mylle está digitando..."):
                resposta = ApiService.ask_gemini(cleaned_input, st.session_state.session_id, conn)
            if isinstance(resposta, str):
                resposta = {"text": resposta, "cta": {"show": False}}
            elif "text" not in resposta:
                resposta = {"text": str(resposta), "cta": {"show": False}}
            st.session_state.messages.append({
                "role": "assistant",
                "content": json.dumps(resposta)
            })
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "assistant",
                json.dumps(resposta)
            )
            save_persistent_data()
            st.markdown("""
            <script>
                window.scrollTo(0, document.body.scrollHeight);
            </script>
            """, unsafe_allow_html=True)

# ======================
# APLICAÇÃO PRINCIPAL
# ======================
def main():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #2e001a 0%, #a8003a 100%) !important;
            border-right: 1px solid #ff1744 !important;
        }
        .stButton button {
            background: rgba(255, 23, 68, 0.2) !important;
            color: white !important;
            border: 1.5px solid #ff1744 !important;
            transition: all 0.3s !important;
        }
        .stButton button:hover {
            background: rgba(255, 23, 68, 0.35) !important;
            transform: translateY(-2px) !important;
        }
        [data-testid="stChatInput"] {
            background: rgba(255, 23, 68, 0.07) !important;
            border: 1.5px solid #ff1744 !important;
        }
        div.stButton > button:first-child {
            background: linear-gradient(45deg, #ff1744, #ff9800) !important;
            color: white !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 10px 24px !important;
            font-weight: bold !important;
            transition: all 0.3s !important;
            box-shadow: 0 4px 8px rgba(255, 23, 68, 0.15) !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(255, 23, 68, 0.25) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = DatabaseService.init_db()
    conn = st.session_state.db_conn
    ChatService.initialize_session(conn)
    if not st.session_state.age_verified:
        UiService.age_verification()
        st.stop()
    UiService.setup_sidebar()
    # Tela de ligação: trocar telefone por perfil (feito aqui)
    if not st.session_state.connection_complete:
        # Simula "ligando", mas já mostra a foto da modelo no centro
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; margin: 50px 0;">
                <img src="{Config.IMG_PROFILE}" width="120" style="border-radius: 50%; border: 3px solid #ff1744;">
                <h2 style="color: #ff1744; margin-top: 15px;">Mylle Pimenta</h2>
                <p style="font-size: 1.1em;">Preparada pra te atiçar, amorzinho... 🌶️</p>
            </div>
            """, unsafe_allow_html=True)
            with st.spinner("Conectando com a Mylle..."):
                time.sleep(5)
            st.success("Chamada atendida! Mylle está online.")
        st.session_state.connection_complete = True
        save_persistent_data()
        st.rerun()
    if not st.session_state.chat_started:
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; margin: 50px 0;">
                <img src="{Config.IMG_PROFILE}" width="120" style="border-radius: 50%; border: 3px solid #ff1744;">
                <h2 style="color: #ff1744; margin-top: 15px;">Mylle Pimenta</h2>
                <p style="font-size: 1.1em;">Quer entrar no meu privado? Só clicar abaixo!</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Entrar no Chat Picante", type="primary", use_container_width=True):
                st.session_state.update({
                    'chat_started': True,
                    'current_page': 'chat'
                })
                save_persistent_data()
                st.rerun()
        st.stop()
    if st.session_state.current_page == "home":
        NewPages.show_home_page()
    elif st.session_state.current_page == "gallery":
        UiService.show_gallery_page(conn)
    else:
        UiService.enhanced_chat_ui(conn)
    save_persistent_data()

if __name__ == "__main__":
    main()
