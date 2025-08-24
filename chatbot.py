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
    page_title="Mylle Premium",
    page_icon="💋",
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
    # VIP links kept but not used in UI per request (removed from sidebar/offers)
    VIP_LINK = ""
    CHECKOUT_START = "#"
    CHECKOUT_PREMIUM = "#"
    CHECKOUT_EXTREME = "#"
    CHECKOUT_VIP_1MES = "#"
    CHECKOUT_VIP_3MESES = "#"
    CHECKOUT_VIP_1ANO = "#"
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    AUDIO_FILE = "https://github.com/gustapb77/ChatBotHot/raw/refs/heads/main/assets/audio/paloma_audio.mp3"
    AUDIO_DURATION = 7
    # Updated profile image and model name references
    IMG_PROFILE = "https://i.ibb.co/3c5k3Vx/mylle-profile.jpg"  # replace with your desired profile image URL
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
    # Social links to add to sidebar
    SOCIALS = {
        "Instagram": "https://instagram.com/",
        "Facebook": "https://facebook.com/",
        "Telegram": "https://t.me/",
        "TikTok": "https://www.tiktok.com/"
    }

# ======================
# PERSISTÊNCIA DE ESTADO
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
        'connection_complete', 'chat_started', 'audio_sent',
        'current_page', 'show_vip_offer', 'session_id',
        'last_cta_time', 'greeted', 'first_response_handled'
    ]

    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}

    if new_data != saved_data:
        db.save_state(user_id, new_data)

# ======================
# MODELOS DE DADOS
# ======================
class Persona:
    MYLLE = """
    [PERFIL MYLLE]
    - Mulher safada e provocante que adora deixar o cliente com tesão
    - Linguagem direta, carinhosa e com malícia
    - Frases curtas, tom íntimo

    [DIRETRIZES DE RESPOSTA]
    1. Analise o histórico da conversa para entender o contexto
    2. Só ofereça conteúdo quando o clima estiver quente
    3. Use CTAs inteligentes baseados no que o cliente está pedindo

    [EXEMPLOS CONTEXUAIS]
    1. Quando o histórico mostra clima sexual:
    Histórico:
    Cliente: sua buceta é rosinha?
    Mylle: adoro mostrar ela aberta
    Cliente: quero ver
    Resposta: ```json
    {
      "text": "to com fotos da minha buceta escorrendo quer ver?",
      "cta": {
        "show": true,
        "label": "Ver Fotos Quentes",
        "target": "offers"
      }
    }
    ```

    2. Quando o cliente pede algo específico:
    Histórico:
    Cliente: tem video vc transando?
    Resposta: ```json
    {
      "text": "tenho varios videos bem gostosos vem ver",
      "cta": {
        "show": true,
        "label": "Ver Vídeos Exclusivos",
        "target": "offers"
      }
    }
    ```

    3. Quando o contexto não justifica CTA:
    Histórico:
    Cliente: oi
    Mylle: oi gato
    Resposta: ```json
    {
      "text": "eai gostoso",
      "cta": {
        "show": false
      }
    }
    ```
    """

class CTAEngine:
    @staticmethod
    def should_show_cta(conversation_history: list) -> bool:
        """Analisa o contexto para decidir quando mostrar CTA"""
        if len(conversation_history) < 2:
            return False

        # Não mostrar CTA se já teve um recentemente
        if 'last_cta_time' in st.session_state:
            elapsed = time.time() - st.session_state.last_cta_time
            if elapsed < 120:  # 2 minutos de intervalo entre CTAs
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
        """Gera resposta com CTA contextual (fallback)"""
        user_input = user_input.lower()

        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda"]):
            return {
                "text": random.choice([
                    "to com fotos da minha buceta bem aberta quer ver",
                    "minha buceta ta chamando vc nas fotos",
                    "fiz um ensaio novo mostrando tudinho"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Fotos Quentes",
                    "target": "offers"
                }
            }

        elif any(v in user_input for v in ["video", "transar", "masturbar"]):
            return {
                "text": random.choice([
                    "tenho video me masturbando gostoso vem ver",
                    "to me tocando nesse video novo quer ver",
                    "gravei um video especial pra vc"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Vídeos Exclusivos",
                    "target": "offers"
                }
            }

        else:
            return {
                "text": random.choice([
                    "quero te mostrar tudo que eu tenho aqui",
                    "meu privado ta cheio de surpresas pra vc",
                    "vem ver o que eu fiz pensando em voce"
                ]),
                "cta": {
                    "show": False
                }
            }

# ======================
# SERVIÇOS DE BANCO DE DADOS
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
        # Currently we pass prompt through to the API stub. Cache kept.
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn) -> dict:
        delay_time = random.uniform(1, 3)
        time.sleep(delay_time)

        # simulate UI effects
        status_container = st.empty()
        UiService.show_status_effect(status_container, "viewed")
        UiService.show_status_effect(status_container, "typing")

        conversation_history = ChatService.format_conversation_history(st.session_state.messages)

        # build the text to send to the API without using an f-string that contains unescaped braces
        api_user_text = (
            Persona.MYLLE
            + "\n\nHistórico da Conversa:\n"
            + conversation_history
            + "\n\nÚltima mensagem do cliente: '"
            + prompt
            + "'\n\nResponda em JSON com o formato:\n"
            + '{\n  "text": "...",\n  "cta": {"show": false}\n}\n'
        )

        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": api_user_text}]
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
                        st.session_state.last_cta_time = time.time()  # Registrar quando CTA foi mostrado

                return resposta

            except json.JSONDecodeError:
                return {"text": gemini_response, "cta": {"show": False}}

        except Exception as e:
            # Fallback: use CTAEngine fallback response for certain prompts
            if any(k in prompt.lower() for k in ["foto", "video", "vip", "quero ver", "ver fotos"]):
                return CTAEngine.generate_response(prompt)
            st.error(f"Erro na API: {str(e)}")
            return {"text": "Vamos continuar isso mais tarde...", "cta": {"show": False}}

# ======================
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def get_chat_audio_player():
        # kept for compatibility but not used on start as requested
        return f"""
        <div style="
            background: linear-gradient(45deg, #ff66b3, #ff1493);
            border-radius: 15px;
            padding: 12px;
            margin: 5px 0;
        ">
            <audio controls style="width:100%; height:40px;">
                <source src="{Config.AUDIO_FILE}" type="audio/mp3">
            </audio>
        </div>
        """

    @staticmethod
    def show_call_effect():
        LIGANDO_DELAY = 5
        ATENDIDA_DELAY = 3

        call_container = st.empty()
        call_container.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e0033, #3c0066);
            border-radius: 20px;
            padding: 30px;
            max-width: 300px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 2px solid #ff66b3;
            text-align: center;
            color: white;
            animation: pulse-ring 2s infinite;
        ">
            <div style="font-size: 3rem;">📱</div>
            <h3 style="color: #ff66b3; margin-bottom: 5px;">Ligando para Mylle...</h3>
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 15px;">
                <div style="width: 10px; height: 10px; background: #4CAF50; border-radius: 50%;"></div>
                <span style="font-size: 0.9rem;">Online agora</span>
            </div>
        </div>
        <style>
            @keyframes pulse-ring {{
                0% {{ transform: scale(0.95); opacity: 0.8; }}
                50% {{ transform: scale(1.05); opacity: 1; }}
                100% {{ transform: scale(0.95); opacity: 0.8; }}
            }}
        </style>
        """, unsafe_allow_html=True)

        time.sleep(LIGANDO_DELAY)
        call_container.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e0033, #3c0066);
            border-radius: 20px;
            padding: 30px;
            max-width: 300px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 2px solid #4CAF50;
            text-align: center;
            color: white;
        ">
            <div style="font-size: 3rem; color: #4CAF50;">✓</div>
            <h3 style="color: #4CAF50; margin-bottom: 5px;">Chamada atendida!</h3>
            <p style="font-size: 0.9rem; margin:0;">Mylle está te esperando...</p>
        </div>
        """, unsafe_allow_html=True)

        time.sleep(ATENDIDA_DELAY)
        call_container.empty()

    @staticmethod
    def show_status_effect(container, status_type):
        status_messages = {
            "viewed": "Visualizado",
            "typing": "Digitando"
        }

        message = status_messages.get(status_type, "...")
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
    def show_custom_typing(container, duration=3.0):
        # Custom typing indicator for a specific duration (in seconds)
        message = "Digitando"
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            dots = "." * (int(elapsed * 2) % 4)
            container.markdown(f"""
            <div style="
                color: #888;
                font-size: 0.9em;
                padding: 6px 12px;
                border-radius: 12px;
                background: rgba(0,0,0,0.03);
                display: inline-block;
                font-style: italic;
            ">
                {message}{dots}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)
        container.empty()

    @staticmethod
    def show_audio_recording_effect(container):
        message = "Gravando um áudio"
        dots = ""
        start_time = time.time()

        while time.time() - start_time < Config.AUDIO_DURATION:
            elapsed = time.time() - start_time
            dots = "." * (int(elapsed) % 4)

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
                max-width: 700px;
                margin: 2rem auto;
                padding: 2rem;
                background: linear-gradient(145deg, #1b5e20, #2e7d32);
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 102, 179, 0.05);
                color: white;
                text-align: center;
            }
            .age-header {
                display: flex;
                align-items: center;
                gap: 15px;
                justify-content: center;
                margin-bottom: 1rem;
            }
            .age-icon {
                font-size: 3rem;
                color: #ff5722;
            }
            .age-title {
                font-size: 1.8rem;
                font-weight: 700;
                margin: 0;
                color: #fff;
            }
            .age-photo {
                width: 140px;
                height: 140px;
                border-radius: 50%;
                object-fit: cover;
                border: 3px solid rgba(255,255,255,0.12);
                display: block;
                margin: 0.5rem auto 1rem auto;
            }
            .age-text {
                color: #e8f5e9;
            }
            .entry-btn {
                background: linear-gradient(45deg, #ff5722, #ff1493);
                color: white;
                padding: 12px 20px;
                border-radius: 30px;
                text-decoration: none;
                font-weight: bold;
                border: none;
            }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown(f"""
            <div class="age-verification">
                <div class="age-header">
                    <div class="age-icon">🔞</div>
                    <h1 class="age-title">Verificação de Idade</h1>
                </div>
                <img src="{Config.IMG_PROFILE}" alt="perfil" class="age-photo" />
                <div class="age-content">
                    <p class="age-text">Este site contém material explícito destinado exclusivamente a adultos maiores de 18 anos.</p>
                    <p class="age-text">Ao acessar este conteúdo, você declara estar em conformidade com todas as leis locais aplicáveis.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            # Added pepper icon to the entry button label
            if st.button("🌶️ Confirmo que sou maior de 18 anos",
                        key="age_checkbox",
                        use_container_width=True,
                        type="primary"):
                # mark verified and go directly to profile (home) page
                # IMPORTANT CHANGE: set current_page to 'home' and set connection_complete True
                # so the app goes directly to the profile/home page after verification.
                st.session_state.age_verified = True
                st.session_state.current_page = 'home'
                st.session_state.connection_complete = True
                st.session_state.chat_started = False
                save_persistent_data()
                st.rerun()

    @staticmethod
    def setup_sidebar():
        with st.sidebar:
            st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    background: linear-gradient(180deg, #0b3d02 0%, #145214 100%) !important;
                    border-right: 1px solid rgba(255,255,255,0.06) !important;
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    height: 100vh !important;
                    overflow: auto !important;
                    z-index: 999 !important;
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
                    border: 2px solid #4caf50;
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
                    background: rgba(255, 255, 255, 0.03);
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
                .social-btn {
                    display: inline-block;
                    width: 100%;
                    padding: 10px;
                    margin: 6px 0;
                    text-align: center;
                    border-radius: 8px;
                    text-decoration: none;
                    color: white;
                    background: linear-gradient(45deg,#1de9b6,#00c853);
                }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="sidebar-logo-container">
                <img src="{Config.LOGO_URL}" class="sidebar-logo" alt="Logo">
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="sidebar-header">
                <img src="{Config.IMG_PROFILE}" alt="Mylle">
                <h3 style="color: #ffffff; margin-top: 10px;">Mylle Alves</h3>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            # Menu title color changed to white
            st.markdown('<h3 style="color: white; margin-bottom: 8px;">Menu Exclusivo</h3>', unsafe_allow_html=True)

            menu_options = {
                "Início": "home",
                "Galeria Privada": "gallery",
                "Mensagens": "messages",
                "Ofertas Especiais": "offers"
            }

            for option, page in menu_options.items():
                if st.button(option, use_container_width=True, key=f"menu_{page}"):
                    if st.session_state.current_page != page:
                        st.session_state.current_page = page
                        st.session_state.last_action = f"page_change_to_{page}"
                        save_persistent_data()
                        st.rerun()

            st.markdown("---")
            # Removed "Sua Conta" and VIP banners/links as requested (no VIP upsell in sidebar)

            # Social buttons (Instagram, Facebook, Telegram, TikTok)
            st.markdown('<div style="margin-top: 8px;"><strong style="color:#fff;">Redes Sociais</strong></div>', unsafe_allow_html=True)
            for name, link in Config.SOCIALS.items():
                st.markdown(f"""
                <a href="{link}" target="_blank" rel="noopener noreferrer" class="social-btn">{name}</a>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; font-size: 0.7em; color: #bdbdbd;">
                <p>© 2024 Mylle Alves</p>
                <p>Conteúdo para maiores de 18 anos</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def show_gallery_page(conn):
        st.markdown("""
        <div style="
            background: rgba(0, 0, 0, 0.06);
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
                    use_column_width=True,
                    caption=f"Preview {idx+1}"
                )
                st.markdown(f"""
                <div style="
                    text-align: center;
                    font-size: 0.8em;
                    color: #ff66b3;
                    margin-top: -10px;
                ">
                    Conteúdo bloqueado
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="text-align: center;">
            <h4>Desbloqueie acesso completo</h4>
            <p>Assine o plano ideal para você</p>
        </div>
        """, unsafe_allow_html=True)

        # Removed VIP dedicated button as requested
        if st.button("Voltar ao chat", key="back_from_gallery"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def chat_shortcuts():
        cols = st.columns(4)
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
            if st.button("Ofertas", key="shortcut_offers",
                       help="Ver ofertas especiais",
                       use_container_width=True):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()
        # Removed VIP shortcut per request (no VIP in menu)

        st.markdown("""
        <style>
            div[data-testid="stHorizontalBlock"] > div > div > button {
                color: white !important;
                border: 1px solid #1de9b6 !important;
                background: rgba(29, 233, 182, 0.12) !important;
                transition: all 0.3s !important;
                font-size: 0.8rem !important;
            }
            div[data-testid="stHorizontalBlock"] > div > div > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 2px 8px rgba(29, 233, 182, 0.2) !important;
            }
            @media (max-width: 400px) {
                div[data-testid="stHorizontalBlock"] > div > div > button {
                    font-size: 0.7rem !important;
                    padding: 6px 2px !important;
                }
            }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def enhanced_chat_ui(conn):
        # WhatsApp-like green theme + spicy accents
        st.markdown("""
        <style>
            .chat-header {
                background: linear-gradient(90deg, #075e54, #128c7e);
                color: white;
                padding: 12px;
                border-radius: 10px;
                margin-bottom: 12px;
                text-align: left;
                box-shadow: 0 4px 8px rgba(0,0,0,0.06);
            }
            .stAudio {
                border-radius: 20px !important;
                background: rgba(0, 0, 0, 0.03) !important;
                padding: 10px !important;
                margin: 10px 0 !important;
            }
            .user-bubble {
                background: #dcf8c6;
                color: #000;
                padding: 10px;
                border-radius: 18px 18px 4px 18px;
                display: inline-block;
                max-width: 80%;
            }
            .assistant-bubble {
                background: #ffffff;
                color: #000;
                padding: 10px;
                border-radius: 18px 18px 18px 4px;
                display: inline-block;
                max-width: 80%;
                box-shadow: 0 1px 0 rgba(0,0,0,0.06);
            }
            .chat-footer {
                margin-top: 10px;
                color: #bdbdbd;
                text-align: center;
            }
            .sidebar-stats {
                background: rgba(0,0,0,0.03);
                padding: 8px;
                border-radius: 8px;
            }
        </style>
        """, unsafe_allow_html=True)

        UiService.chat_shortcuts()

        st.markdown(f"""
        <div class="chat-header">
            <h2 style="margin:0; font-size:1.2em; display:inline-block;">Chat Privado com Mylle</h2>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.markdown(f"""
        <div class="sidebar-stats" style="margin-bottom:12px;">
            <p style="margin:0; font-size:0.95em; color:#fff;">
                Mensagens hoje: <strong style="color:#c8e6c9;">{st.session_state.request_count}/{Config.MAX_REQUESTS_PER_SESSION}</strong>
            </p>
            <progress value="{st.session_state.request_count}" max="{Config.MAX_REQUESTS_PER_SESSION}" style="width:100%; height:6px;"></progress>
        </div>
        """, unsafe_allow_html=True)

        ChatService.process_user_input(conn)
        save_persistent_data()

        st.markdown("""
        <div class="chat-footer">
            <p>Conversa privada • Suas mensagens são confidenciais</p>
        </div>
        """, unsafe_allow_html=True)

# ======================
# PÁGINAS
# ======================
class NewPages:
    @staticmethod
    def show_home_page(conn):
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(Config.IMG_PROFILE, use_column_width=True)
            st.markdown("""
            <div style="text-align: center; margin-top: 10px;">
                <h3 style="color: #ff66b3;">Mylle Alves</h3>
                <p style="color: #888;">Online agora 💚</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            st.markdown("""
            <div style="
                background: rgba(255, 102, 179, 0.1);
                padding: 15px;
                border-radius: 10px;
            ">
                <h4>📊 Meu Perfil</h4>
                <p>👙 85-60-90</p>
                <p>📏 1.68m</p>
                <p>🎂 22 anos</p>
                <p>📍 São Paulo</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(45deg, #ff66b3, #ff1493);
                padding: 20px;
                border-radius: 10px;
                color: white;
                text-align: center;
                margin-bottom: 20px;
            ">
                <h2>💋 Bem-vindo ao Meu Mundo</h2>
                <p>Conversas quentes e conteúdo exclusivo esperando por você!</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="
                background: rgba(255, 102, 179, 0.1);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            ">
                <h4>🎯 O que você encontra aqui:</h4>
                <p>• 💬 Chat privado comigo</p>
                <p>• 📸 Fotos exclusivas e sensuais</p>
                <p>• 🎥 Vídeos quentes e explícitos</p>
                <p>• 🎁 Conteúdo personalizado</p>
                <p>• 🔞 Experiências únicas</p>
            </div>
            """, unsafe_allow_html=True)

            # Preview images
            st.markdown("### 🌶️ Prévia do Conteúdo")
            preview_cols = st.columns(2)
            for idx, col in enumerate(preview_cols):
                if idx < len(Config.IMG_HOME_PREVIEWS):
                    with col:
                        st.image(Config.IMG_HOME_PREVIEWS[idx], use_column_width=True)

            st.markdown("---")
            # Added start conversation button on profile page
            if st.button("Iniciar Conversa 🌶️", key="start_from_profile", use_container_width=True):
                st.session_state.update({
                    'chat_started': True,
                    'current_page': 'chat',
                    'audio_sent': False
                })
                save_persistent_data()
                st.rerun()

    @staticmethod
    def show_offers_page():
        # Simplified offers page — removed direct checkout links and heavy VIP upsell
        st.markdown("""
        <style>
            .offer-card {
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                padding: 18px;
                margin-bottom: 14px;
                background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(0,0,0,0.02));
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center; margin-bottom: 18px;">
            <h2 style="color: #fff;">Ofertas Especiais</h2>
            <p style="color:#cfd8dc;">Confira algumas opções — sem links diretos de pagamento nesta versão.</p>
        </div>
        """, unsafe_allow_html=True)

        plans = [
            {"name": "1 Mês", "price": "R$ 29,90", "benefits": ["Acesso total", "Conteúdo novo diário", "Chat privado"], "tag": "COMUM"},
            {"name": "3 Meses", "price": "R$ 69,90", "benefits": ["25% de desconto", "Bônus: 1 vídeo exclusivo", "Prioridade no chat"], "tag": "MAIS POPULAR"},
            {"name": "1 Ano", "price": "R$ 199,90", "benefits": ["66% de desconto", "Presente surpresa mensal", "Acesso a conteúdos raros"], "tag": "MELHOR CUSTO-BENEFÍCIO"}
        ]

        for plan in plans:
            with st.container():
                st.markdown(f"""
                <div class="offer-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin:0;">{plan['name']}</h3>
                        {f'<span style="background:#1de9b6;color:#004d40;padding:4px 8px;border-radius:6px;font-weight:bold;">{plan["tag"]}</span>' if plan["tag"] else ''}
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="font-size: 1.4em; color: #1de9b6; font-weight: bold;">{plan['price']}</span>
                    </div>
                    <ul style="padding-left: 20px;">
                        {''.join([f'<li style="margin-bottom: 4px;">{benefit}</li>' for benefit in plan['benefits']])}
                    </ul>
                    <div style="text-align: center; margin-top: 12px;">
                        <button style="background:linear-gradient(45deg,#1de9b6,#00c853); color:#004d40; padding:8px 14px; border-radius:20px; border:none; font-weight:bold;">
                            Quero saber mais
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if st.button("Voltar ao chat", key="back_from_offers"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

# ======================
# APLICAÇÃO PRINCIPAL
# ======================
def main():
    # Updated theme CSS to feel spicier + WhatsApp-like
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b3d02 0%, #145214 100%) !important;
            border-right: 1px solid rgba(255,255,255,0.04) !important;
        }
        .stButton button {
            background: linear-gradient(45deg,#1de9b6,#00c853) !important;
            color: #004d40 !important;
            border: none !important;
            transition: all 0.2s !important;
        }
        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        }
        [data-testid="stChatInput"] {
            background: #fff !important;
            border: 1px solid rgba(0,0,0,0.06) !important;
        }
        div.stButton > button:first-child {
            background: linear-gradient(45deg, #ff1493, #9400d3) !important;
            color: white !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 10px 24px !important;
            font-weight: bold !important;
            transition: all 0.3s !important;
            box-shadow: 0 4px 8px rgba(255, 20, 147, 0.12) !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(255, 20, 147, 0.18) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = DatabaseService.init_db()

    conn = st.session_state.db_conn

    ChatService.initialize_session(conn)

    # If user hasn't verified age, show verification and stop execution
    if not st.session_state.age_verified:
        UiService.age_verification()
        st.stop()

    UiService.setup_sidebar()

    # Only show initial call effect if connection_complete is False.
    # The age_verification() now sets connection_complete = True and current_page = 'home',
    # so after verification users are sent directly to the profile/home page.
    if not st.session_state.connection_complete:
        UiService.show_call_effect()
        st.session_state.connection_complete = True
        save_persistent_data()
        st.rerun()

    # If chat hasn't started yet, show the profile "start conversation" layout.
    if not st.session_state.chat_started:
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown("""
            <div style="text-align: center; margin: 30px 0;">
                <img src="{profile_img}" width="120" style="border-radius: 50%; border: 3px solid #1de9b6;">
                <h2 style="color: #1de9b6; margin-top: 15px;">Mylle Alves</h2>
                <p style="font-size: 1.05em;">Tô pronta pra você, amor...</p>
            </div>
            """.format(profile_img=Config.IMG_PROFILE), unsafe_allow_html=True)

            if st.button("Iniciar Conversa 🌶️", type="primary", use_container_width=True):
                st.session_state.update({
                    'chat_started': True,
                    'current_page': 'chat',
                    'audio_sent': False
                })
                save_persistent_data()
                st.rerun()
        st.stop()

    # Page routing
    if st.session_state.current_page == "home":
        NewPages.show_home_page(conn)
    elif st.session_state.current_page == "gallery":
        UiService.show_gallery_page(conn)
    elif st.session_state.current_page == "offers":
        NewPages.show_offers_page()
    elif st.session_state.get("show_vip_offer", False):
        st.warning("Página VIP em desenvolvimento")
        if st.button("Voltar ao chat"):
            st.session_state.show_vip_offer = False
            save_persistent_data()
            st.rerun()
    else:
        UiService.enhanced_chat_ui(conn)

    save_persistent_data()

if __name__ == "__main__":
    main()
