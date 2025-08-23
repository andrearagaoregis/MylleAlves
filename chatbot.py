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

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(
    page_title="Mylle Alves Premium",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
hide_streamlit_style = """
<style>
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], 
    div[data-testid="stStatusWidget"], #MainMenu, header, footer, 
    .stDeployButton {display: none !important;}
    .block-container {padding-top: 0rem !important;}
    [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {gap: 0.5rem !important;}
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
    MAX_REQUESTS_PER_SESSION = 50
    REQUEST_TIMEOUT = 30
    AUDIO_FILE = "https://github.com/gustapb77/ChatBotHot/raw/refs/heads/main/assets/audio/paloma_audio.mp3"
    AUDIO_DURATION = 7
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
    LOGO_URL = "https://i.ibb.co/LX7x3tcB/Logo-Golden-Pepper-Letreiro-1.png"

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
        'connection_complete', 'chat_started', 'audio_sent',
        'current_page', 'session_id', 'last_cta_time', 'preview_shown'
    ]
    
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    db.save_state(user_id, new_data)

# ======================
# MODELOS DE DADOS
# ======================
class Persona:
    MYLLE = """
    [PERFIL MYLLE ALVES]
    - Garota sensual, carinhosa e extremamente safadinha
    - Adora flertar e criar conexões íntimas
    - Linguagem casual, divertida e cheia de malícia
    - Respostas curtas, diretas e envolventes
    - Foca em criar desejo naturalmente, não em vender

    [PERSONALIDADE]
    - Idade: 22 anos
    - Estilo: sensual e descontraída
    - Personalidade: brincalhona, ousada e carinhosa
    - Gosta: de conversas picantes, elogios e criar intimidade

    [DIRETRIZES DE RESPOSTA]
    1. Seja natural e espontânea como uma garota real
    2. Use emojis e linguagem casual
    3. Foque em flertar e criar conexão emocional
    4. Respostas curtas (1-2 frases no máximo)
    5. Seja safadinha mas carinhosa
    6. Só mostre conteúdo quando o clima esquentar naturalmente

    [EXEMPLOS]
    Cliente: oi
    Resposta: Oi, gato! 😏 Tava esperando você...

    Cliente: como vc tá?
    Resposta: Agora melhor, vindo conversar comigo 😈

    Cliente: quero ver vc
    Resposta: E eu quero te mostrar... mas só pra quem merece 😏
    """

class CTAEngine:
    @staticmethod
    def should_show_cta(conversation_history: List[Dict]) -> bool:
        if len(conversation_history) < 3:
            return False

        if 'last_cta_time' in st.session_state:
            elapsed = time.time() - st.session_state.last_cta_time
            if elapsed < 180:
                return False

        last_msgs = []
        for msg in conversation_history[-6:]:
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
            "quero", "tesão", "molhada", "foda", "nude",
            "seios", "bunda", "rabuda", "gostosa", "gata"
        ]
        
        direct_asks = [
            "mostra", "quero ver", "me manda", "como assinar",
            "como comprar", "como ter acesso", "onde vejo más",
            "quero comprar", "quero conteúdo"
        ]
        
        hot_count = sum(1 for word in hot_words if word in context)
        has_direct_ask = any(ask in context for ask in direct_asks)
        
        return (hot_count >= 3) or has_direct_ask

    @staticmethod
    def should_show_preview() -> bool:
        if 'preview_shown' in st.session_state and st.session_state.preview_shown:
            return False
            
        if random.random() < 0.25:
            st.session_state.preview_shown = True
            save_persistent_data()
            return True
        return False

    @staticmethod
    def generate_response(user_input: str) -> Dict:
        user_input = user_input.lower()
        
        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda", "nude", "nua"]):
            return {
                "text": random.choice([
                    "Ah, quer me ver? 😈 Tenho umas fotinhas bem quentes...",
                    "Minhas fotos são bem ousadas, hein... 😏",
                    "Eu adoro tirar fotos... especialmente as mais picantes 🔥"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Minhas Fotos",
                    "target": "offers"
                }
            }
        
        elif any(v in user_input for v in ["video", "transar", "masturbar", "sexy"]):
            return {
                "text": random.choice([
                    "Meus vídeos são bem quentes... 😈",
                    "Gravei uns vídeos bem ousados...",
                    "Nos meus vídeos eu solto a imaginação 😏"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Meus Vídeos",
                    "target": "offers"
                }
            }
        
        else:
            return {
                "text": random.choice([
                    "Que delícia conversar com você... 😏",
                    "Você me deixa com tesão... 😈",
                    "Adoro quando você fala assim... 🔥"
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
# SERVIÇOS DE API
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn: sqlite3.Connection) -> Dict:
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn: sqlite3.Connection) -> Dict:
        delay_time = random.uniform(1.0, 3.0)
        time.sleep(delay_time)
        
        status_container = st.empty()
        UiService.show_status_effect(status_container, "viewed")
        UiService.show_status_effect(status_container, "typing")
        
        conversation_history = ChatService.format_conversation_history(st.session_state.messages)
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{Persona.MYLLE}\n\nHistórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"sua resposta\",\n  \"cta\": {{\n    \"show\": true/false,\n    \"label\": \"texto do botão\",\n    \"target\": \"página\"\n  }}\n}}"}]
                }
            ],
            "generationConfig": {
                "temperature": 1.0,
                "topP": 0.9,
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
                
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: {str(e)}")
            return CTAEngine.generate_response(prompt)
        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
            return CTAEngine.generate_response(prompt)

# ======================
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def get_chat_audio_player() -> str:
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
    def show_preview_image() -> None:
        st.markdown(f"""
        <div style="
            text-align: center;
            margin: 15px 0;
            padding: 10px;
            background: rgba(255, 102, 179, 0.1);
            border-radius: 10px;
            border: 1px solid #ff66b3;
        ">
            <img src="{Config.IMG_PREVIEW}" style="
                width: 100%;
                max-width: 300px;
                border-radius: 10px;
                margin-bottom: 10px;
            ">
            <p style="color: #ff66b3; font-style: italic; margin: 0;">
                Uma prévia do que você pode ver... 😈
            </p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_call_effect() -> None:
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
        ">
            <div style="font-size: 3rem;">💋</div>
            <h3 style="color: #ff66b3; margin-bottom: 5px;">Chamando Mylle...</h3>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(2)
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
            <div style="font-size: 3rem; color: #4CAF50;">🔥</div>
            <h3 style="color: #4CAF50; margin-bottom: 5px;">Mylle conectada!</h3>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(1.5)
        call_container.empty()

    @staticmethod
    def show_status_effect(container, status_type: str) -> None:
        status_messages = {"viewed": "Visto", "typing": "Digitando"}
        message = status_messages[status_type]
        dots = ""
        start_time = time.time()
        duration = 1.5 if status_type == "viewed" else 2.0
        
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
    def show_audio_recording_effect(container) -> None:
        message = "Enviando áudio"
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
    def age_verification() -> None:
        st.markdown("""
        <style>
            .age-verification {
                max-width: 500px;
                margin: 2rem auto;
                padding: 2rem;
                background: linear-gradient(145deg, #1e0033, #3c0066);
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 102, 179, 0.2);
                color: white;
                text-align: center;
            }
            .age-icon {
                font-size: 3rem;
                color: #ff66b3;
                margin-bottom: 1rem;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="age-verification">
            <div class="age-icon">🔞</div>
            <h1 style="color: #ff66b3; margin-bottom: 1rem;">Acesso Restrito</h1>
            <p>Este conteúdo é exclusivo para maiores de 18 anos</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("💖 Tenho 18 anos ou mais", 
                        key="age_checkbox",
                        use_container_width=True,
                        type="primary"):
                st.session_state.age_verified = True
                save_persistent_data()
                st.rerun()

    @staticmethod
    def setup_sidebar() -> None:
        with st.sidebar:
            st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    background: linear-gradient(180deg, #1a0033 0%, #2d004d 100%) !important;
                    border-right: 1px solid #ff66b3 !important;
                }
                .sidebar-logo {
                    width: 250px;
                    height: auto;
                    margin: 0 auto;
                    display: block;
                }
                .sidebar-profile {
                    text-align: center;
                    margin: 1rem 0;
                }
                .sidebar-profile img {
                    border-radius: 50%;
                    border: 3px solid #ff66b3;
                    width: 100px;
                    height: 100px;
                    object-fit: cover;
                    margin-bottom: 10px;
                }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="sidebar-profile">
                <img src="{Config.IMG_PROFILE}" alt="Mylle Alves">
                <h3 style="color: #ff66b3; margin: 0;">Mylle Alves</h3>
                <p style="color: #aaa; margin: 0; font-size: 0.9em;">Online agora 💚</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            menu_options = {
                "💋 Início": "home",
                "📸 Galeria": "gallery",
                "🎁 Conteúdo": "offers"
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
    def show_gallery_page() -> None:
        st.markdown("""
        <div style="
            background: rgba(255, 20, 147, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h3 style="color: #ff66b3; margin: 0;">Minha Galeria Exclusiva</h3>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            with col:
                st.image(Config.IMG_GALLERY[idx % len(Config.IMG_GALLERY)], 
                        use_container_width=True, 
                        caption=f"Preview #{idx+1}")
                st.markdown("""<div style="text-align:center; color: #ff66b3; margin-top: -10px;">💝 Conteúdo especial</div>""", 
                          unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button("🎁 Ver Conteúdo Completo", key="vip_button_gallery", use_container_width=True, type="primary"):
            st.session_state.current_page = "offers"
            st.rerun()
        
        if st.button("💬 Voltar ao chat", key="back_from_gallery"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def chat_shortcuts() -> None:
        cols = st.columns(3)
        with cols[0]:
            if st.button("🏠", key="shortcut_home", use_container_width=True, help="Início"):
                st.session_state.current_page = "home"
                save_persistent_data()
                st.rerun()
        with cols[1]:
            if st.button("📸", key="shortcut_gallery", use_container_width=True, help="Galeria"):
                st.session_state.current_page = "gallery"
                save_persistent_data()
                st.rerun()
        with cols[2]:
            if st.button("🎁", key="shortcut_offers", use_container_width=True, help="Conteúdo"):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()

    @staticmethod
    def enhanced_chat_ui(conn: sqlite3.Connection) -> None:
        st.markdown("""
        <style>
            .chat-header {
                background: linear-gradient(90deg, #ff66b3, #ff1493);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(255, 102, 179, 0.3);
            }
        </style>
        """, unsafe_allow_html=True)
        
        UiService.chat_shortcuts()
        
        st.markdown(f"""
        <div class="chat-header">
            <h2 style="margin:0; font-size:1.5em;">💋 Chat com Mylle</h2>
            <p style="margin:5px 0 0; font-size:0.9em; opacity:0.8;">Conectada e pronta para você</p>
        </div>
        """, unsafe_allow_html=True)
        
        ChatService.process_user_input(conn)
        save_persistent_data()

# ======================
# PÁGINAS
# ======================
class NewPages:
    @staticmethod
    def show_home_page() -> None:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e0033, #3c0066);
            padding: 50px 20px;
            text-align: center;
            border-radius: 15px;
            color: white;
            margin-bottom: 30px;
            border: 2px solid #ff66b3;
            box-shadow: 0 8px 25px rgba(255, 102, 179, 0.2);
        ">
            <h1 style="color: #ff66b3; margin-bottom: 10px;">Mylle Alves</h1>
            <p style="font-size: 1.1em; opacity: 0.9;">Sua garota premium para momentos picantes 🔥</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💬 Iniciar Conversa com Mylle", use_container_width=True, type="primary"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

    @staticmethod
    def show_offers_page() -> None:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #ff66b3; display: inline-block; padding-bottom: 5px;">
                🎁 Meu Conteúdo Exclusivo
            </h2>
            <p style="color: #aaa; margin-top: 5px;">Escolha seu pacote preferido</p>
        </div>
        """, unsafe_allow_html=True)

        packages = [
            {
                "name": "TARADINHA",
                "price": "R$ 29,99",
                "benefits": ["15 fotos exclusivas", "15 vídeos quentes", "Acesso por 30 dias"],
                "color": "#ff66b3",
                "link": Config.CHECKOUT_TARADINHA,
                "image": Config.PACK_IMAGES["TARADINHA"]
            },
            {
                "name": "MOLHADINHA",
                "price": "R$ 49,99", 
                "benefits": ["25 fotos sensuais", "25 vídeos especiais", "Acesso por 60 dias"],
                "color": "#9400d3",
                "link": Config.CHECKOUT_MOLHADINHA,
                "image": Config.PACK_IMAGES["MOLHADINHA"]
            },
            {
                "name": "SAFADINHA",
                "price": "R$ 69,99",
                "benefits": ["40 fotos ultra-exclusivas", "40 vídeos premium", "Acesso vitalício"],
                "color": "#ff0066",
                "link": Config.CHECKOUT_SAFADINHA,
                "image": Config.PACK_IMAGES["SAFADINHA"]
            }
        ]

        cols = st.columns(3)
        for idx, (col, package) in enumerate(zip(cols, packages)):
            with col:
                st.markdown(f"""
                <div style="
                    background: rgba(30, 0, 51, 0.3);
                    border-radius: 15px;
                    padding: 20px;
                    border: 2px solid {package['color']};
                    min-height: 450px;
                    position: relative;
                    transition: all 0.3s;
                    box-shadow: 0 5px 15px rgba{package['color'].replace('#', '')}20;
                ">
                    <div style="text-align: center; margin-bottom: 15px;">
                        <img src="{package['image']}" style="
                            width: 100%;
                            height: 150px;
                            object-fit: cover;
                            border-radius: 10px;
                            margin-bottom: 15px;
                        ">
                        <h3 style="color: {package['color']}; margin: 0 0 10px 0;">{package['name']}</h3>
                        <div style="font-size: 1.8em; color: {package['color']}; font-weight: bold; margin: 10px 0;">
                            {package['price']}
                        </div>
                    </div>
                    <ul style="padding-left: 20px; text-align: left; margin-bottom: 50px;">
                        {''.join([f'<li style="margin-bottom: 8px; color: #ddd;">{benefit}</li>' for benefit in package['benefits']])}
                    </ul>
                    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
                        <a href="{package['link']}" target="_blank" style="
                            display: block;
                            background: linear-gradient(45deg, {package['color']}, #ff1493);
                            color: white;
                            text-align: center;
                            padding: 12px;
                            border-radius: 8px;
                            text-decoration: none;
                            font-weight: bold;
                            transition: all 0.3s;
                        " onmouseover="this.style.transform='scale(1.05)'" 
                        onmouseout="this.style.transform='scale(1)'">
                            💝 Quero este!
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if st.button("💬 Voltar ao chat", key="back_from_offers"):
            st.session_state.current_page = "chat"
            save_persistent_data()
            st.rerun()

# ======================
# SERVIÇOS DE CHAT
# ======================
class ChatService:
    @staticmethod
    def initialize_session(conn: sqlite3.Connection) -> None:
        load_persistent_data()
        
        defaults = {
            'age_verified': False,
            'connection_complete': False,
            'chat_started': False,
            'audio_sent': False,
            'current_page': 'home',
            'last_cta_time': 0,
            'preview_shown': False,
            'session_id': str(random.randint(100000, 999999)),
            'messages': DatabaseService.load_messages(conn, get_user_id(), st.session_state.get('session_id', '')) or [],
            'request_count': len([m for m in st.session_state.get('messages', []) if m["role"] == "user"])
        }
        
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default

    @staticmethod
    def format_conversation_history(messages: List[Dict], max_messages: int = 8) -> str:
        formatted = []
        for msg in messages[-max_messages:]:
            role = "Cliente" if msg["role"] == "user" else "Mylle"
            content = msg["content"]
            if content == "[ÁUDIO]":
                content = "[áudio sensual]"
            elif content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    @staticmethod
    def display_chat_history() -> None:
        chat_container = st.container()
        with chat_container:
            for idx, msg in enumerate(st.session_state.messages[-10:]):
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="😎"):
                        st.markdown(f"""
                        <div style="
                            background: rgba(255, 102, 179, 0.15);
                            padding: 12px;
                            border-radius: 18px 18px 0 18px;
                            margin: 5px 0;
                            color: white;
                        ">
                            {msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                elif msg["content"] == "[ÁUDIO]":
                    with st.chat_message("assistant", avatar="💋"):
                        st.markdown(UiService.get_chat_audio_player(), unsafe_allow_html=True)
                else:
                    try:
                        content_data = json.loads(msg["content"])
                        if isinstance(content_data, dict):
                            with st.chat_message("assistant", avatar="💋"):
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(45deg, #ff66b3, #ff1493);
                                    color: white;
                                    padding: 12px;
                                    border-radius: 18px 18px 18px 0;
                                    margin: 5px 0;
                                ">
                                    {content_data.get("text", "")}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if content_data.get("cta", {}).get("show") and idx == len(st.session_state.messages[-10:]) - 1:
                                    if st.button(content_data.get("cta", {}).get("label", "🎁 Ver Conteúdo"),
                                                key=f"cta_button_{hash(msg['content'])}",
                                                use_container_width=True):
                                        st.session_state.current_page = content_data.get("cta", {}).get("target", "offers")
                                        save_persistent_data()
                                        st.rerun()
                    except:
                        with st.chat_message("assistant", avatar="💋"):
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(45deg, #ff66b3, #ff1493);
                                color: white;
                                padding: 12px;
                                border-radius: 18px 18px 18px 0;
                                margin: 5px 0;
                            ">
                                {msg["content"]}
                            </div>
                            """, unsafe_allow_html=True)

    @staticmethod
    def process_user_input(conn: sqlite3.Connection) -> None:
        ChatService.display_chat_history()
        
        if not st.session_state.get("audio_sent") and st.session_state.chat_started:
            status_container = st.empty()
            UiService.show_audio_recording_effect(status_container)
            
            st.session_state.messages.append({"role": "assistant", "content": "[ÁUDIO]"})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", "[ÁUDIO]")
            st.session_state.audio_sent = True
            save_persistent_data()
            st.rerun()
        
        user_input = st.chat_input("💬 Digite sua mensagem...", key="chat_input")
        
        if user_input:
            cleaned_input = re.sub(r'<[^>]*>', '', user_input)[:500]
            
            if st.session_state.request_count >= Config.MAX_REQUESTS_PER_SESSION:
                st.session_state.messages.append({"role": "assistant", "content": "Preciso dar uma pausa, amor... Volto já! 😘"})
                DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", "Preciso dar uma pausa, amor... Volto já! 😘")
                save_persistent_data()
                st.rerun()
                return
            
            st.session_state.messages.append({"role": "user", "content": cleaned_input})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "user", cleaned_input)
            st.session_state.request_count += 1
            
            with st.chat_message("user", avatar="😎"):
                st.markdown(f"""
                <div style="
                    background: rgba(255, 102, 179, 0.15);
                    padding: 12px;
                    border-radius: 18px 18px 0 18px;
                    margin: 5px 0;
                    color: white;
                ">
                    {cleaned_input}
                </div>
                """, unsafe_allow_html=True)
            
            with st.chat_message("assistant", avatar="💋"):
                resposta = ApiService.ask_gemini(cleaned_input, st.session_state.session_id, conn)
                
                if isinstance(resposta, str):
                    resposta = {"text": resposta, "cta": {"show": False}}
                elif "text" not in resposta:
                    resposta = {"text": str(resposta), "cta": {"show": False}}
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(45deg, #ff66b3, #ff1493);
                    color: white;
                    padding: 12px;
                    border-radius: 18px 18px 18px 0;
                    margin: 5px 0;
                ">
                    {resposta["text"]}
                </div>
                """, unsafe_allow_html=True)
                
                if CTAEngine.should_show_preview():
                    UiService.show_preview_image()
                
                if resposta.get("cta", {}).get("show"):
                    if st.button(resposta["cta"].get("label", "🎁 Ver Conteúdo"),
                                key=f"chat_button_{time.time()}",
                                use_container_width=True):
                        st.session_state.current_page = resposta["cta"].get("target", "offers")
                        save_persistent_data()
                        st.rerun()
            
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
            DatabaseService.save_message(conn, get_user_id(), st.session_state.session_id, "assistant", json.dumps(resposta))
            save_persistent_data()
            
            st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)

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
        UiService.show_call_effect()
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
                <p style="font-size: 1.1em; color: #aaa;">Pronta para conversas quentes com você... 🔥</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💋 Começar a Conversa", type="primary", use_container_width=True):
                st.session_state.update({
                    'chat_started': True,
                    'current_page': 'chat',
                    'audio_sent': False
                })
                save_persistent_data()
                st.rerun()
        st.stop()
    
    if st.session_state.current_page == "home":
        NewPages.show_home_page()
    elif st.session_state.current_page == "gallery":
        UiService.show_gallery_page()
    elif st.session_state.current_page == "offers":
        NewPages.show_offers_page()
    else:
        UiService.enhanced_chat_ui(conn)
    
    save_persistent_data()

if __name__ == "__main__":
    main()


