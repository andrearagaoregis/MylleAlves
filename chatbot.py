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
    page_title="Mylle Alves Premium",
    page_icon="💋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st._config.set_option('client.caching', True)
st._config.set_option('client.showErrorDetails', False)

# Novo estilo com tema Ninho Hot (roxo/rosa)
ninho_hot_theme = """
<style>
    :root {
        --primary-color: #8a2be2;
        --secondary-color: #ff1493;
        --accent-color: #ba55d3;
        --dark-bg: #1a001a;
        --light-bg: #2d0042;
        --text-color: #ffffff;
        --border-color: #8a2be2;
        --chat-user-bg: #8a2be2;
        --chat-model-bg: #4b0082;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--dark-bg) 0%, var(--light-bg) 100%);
        color: var(--text-color);
    }
    
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
    
    /* Estilo do chat estilo WhatsApp */
    .chat-container {
        height: calc(100vh - 150px);
        overflow-y: auto;
        padding: 10px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
        margin-bottom: 70px;
    }
    
    .user-message {
        background: var(--chat-user-bg);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 0 18px;
        margin: 5px 0;
        max-width: 70%;
        margin-left: 30%;
        text-align: right;
    }
    
    .model-message {
        background: var(--chat-model-bg);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 0;
        margin: 5px 0;
        max-width: 70%;
        border: 1px solid var(--border-color);
    }
    
    .message-avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 10px;
    }
    
    .fixed-input {
        position: fixed;
        bottom: 10px;
        left: 10px;
        right: 10px;
        background: var(--dark-bg);
        padding: 10px;
        border-radius: 20px;
        border: 1px solid var(--border-color);
        z-index: 1000;
    }
    
    .sidebar-logo {
        width: 280px;
        height: auto;
        object-fit: contain;
        margin-left: -15px;
        margin-top: -15px;
    }
    
    .vip-badge {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        padding: 15px;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    
    .audio-message {
        display: flex;
        align-items: center;
        background: rgba(138, 43, 226, 0.2);
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        max-width: 70%;
    }
    
    .audio-wave {
        display: flex;
        align-items: center;
        gap: 3px;
        margin: 0 10px;
    }
    
    .audio-bar {
        width: 3px;
        background-color: #8a2be2;
        border-radius: 2px;
        animation: audioWave 1.5s infinite ease-in-out;
    }
    
    @keyframes audioWave {
        0%, 100% { height: 5px; }
        50% { height: 20px; }
    }
    
    @media (min-width: 768px) {
        .sidebar-logo {
            width: 320px;
        }
    }
</style>
"""
st.markdown(ninho_hot_theme, unsafe_allow_html=True)

# ======================
# CONSTANTES E CONFIGURAÇÕES
# ======================
class Config:
    API_KEY = "AIzaSyDbGIpsR4vmAfy30eEuPjWun3Hdz6xj24U"
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    VIP_LINK = "https://exemplo.com/vip"
    CHECKOUT_TARADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACC74F-01EC-4770-B182-B5775AF62A1D"
    CHECKOUT_MOLHADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD1E6-0EFD-4E3E-9F9D-BA0C1A2D7E7A"
    CHECKOUT_SAFADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD395-EE65-458E-9B7E-FED750CC9CA9"
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    IMG_PROFILE = "https://i.ibb.co/vxnTYm0Q/BY-Admiregirls-su-Admiregirls-su-156.jpg"
    IMG_GALLERY = [
        "https://i.ibb.co/C3mDFyJV/BY-Admiregirls-su-Admiregirls-su-036.jpg",
        "https://i.ibb.co/sv2kdLLC/BY-Admiregirls-su-Admiregirls-su-324.jpg",
        "https://i.ibb.co/BHY8ZZG7/BY-Admiregirls-su-Admiregirls-su-033.jpg"
    ]
    IMG_HOME_PREVIEWS = [
        "https://i.ibb.co/BHY8ZZG7/BY-Admiregirls-su-Admiregirls-su-033.jpg",
        "https://i.ibb.co/Q5cHPBd/BY-Admiregirls-su-Admiregirls-su-183.jpg",
        "https://i.ibb.co/xq6frp0h/BY-Admiregirls-su-Admiregirls-su-141.jpg"
    ]
    LOGO_URL = "https://i.ibb.co/LX7x3tcB/Logo-Golden-Pepper-Letreiro-1.png"
    # Novas imagens de prévia
    PREVIEW_IMAGES = [
        "https://i.ibb.co/0Q8Lx0Z/preview1.jpg",
        "https://i.ibb.co/7YfT9y0/preview2.jpg",
        "https://i.ibb.co/5KjX1J0/preview3.jpg",
        "https://i.ibb.co/0jq4Z0L/preview4.jpg"
    ]

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
        'last_cta_time', 'preview_sent', 'preview_count'
    ]
    
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}
    
    if new_data != saved_data:
        db.save_state(user_id, new_data)
        # ======================
# SERVIÇOS DE API
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn) -> dict:
        if any(word in prompt.lower() for word in ["vip", "quanto custa", "comprar", "assinar", "pacote"]):
            return ApiService._call_gemini_api(prompt, session_id, conn)
        
        return ApiService._call_gemini_api(prompt, session_id, conn)

    @staticmethod
    def _call_gemini_api(prompt: str, session_id: str, conn) -> dict:
        delay_time = random.uniform(3, 8)
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
                    "parts": [{"text": f"{Persona.MylleAlves}\n\nHistórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"sua resposta\",\n  \"cta\": {{\n    \"show\": true/false,\n    \"label\": \"texto do botão\",\n    \"target\": \"página\"\n  }},\n  \"preview\": {{\n    \"show\": true/false,\n    \"image_url\": \"url_da_imagem\"\n  }}\n}}"}]
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
                
                # Verificar se deve mostrar CTA
                if resposta.get("cta", {}).get("show"):
                    if not CTAEngine.should_show_cta(st.session_state.messages):
                        resposta["cta"]["show"] = False
                    else:
                        st.session_state.last_cta_time = time.time()
                
                # Verificar se deve mostrar prévia
                if resposta.get("preview", {}).get("show"):
                    if not CTAEngine.should_show_preview(st.session_state.messages):
                        resposta["preview"]["show"] = False
                    else:
                        if 'preview_count' not in st.session_state:
                            st.session_state.preview_count = 0
                        st.session_state.preview_count += 1
                
                return resposta
            
            except json.JSONDecodeError:
                # Fallback para resposta gerada localmente
                return CTAEngine.generate_response(prompt)
                
        except Exception as e:
            st.error(f"Erro na API: {str(e)}")
            # Fallback para resposta gerada localmente
            return CTAEngine.generate_response(prompt)

# ======================
# SERVIÇOS DE CHAT
# ======================
class ChatService:
    @staticmethod
    def format_conversation_history(messages: list) -> str:
        formatted = []
        for msg in messages[-10:]:  # Últimas 10 mensagens para contexto
            role = "Mylle" if msg["role"] == "assistant" else "Cliente"
            content = msg["content"]
            
            if content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    @staticmethod
    def send_message(message: str, conn):
        if 'request_count' not in st.session_state:
            st.session_state.request_count = 0
        
        if st.session_state.request_count >= Config.MAX_REQUESTS_PER_SESSION:
            return {
                "text": "Querido, já conversamos bastante hoje... Que tal dar uma olhadinha no meu conteúdo exclusivo? Tenho muitas coisas quentes para te mostrar! 😈",
                "cta": {
                    "show": True,
                    "label": "Ver Conteúdo Exclusivo",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                }
            }
        
        st.session_state.request_count += 1
        
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        # Salvar mensagem do usuário
        DatabaseService.save_message(
            conn, 
            get_user_id(), 
            st.session_state.session_id, 
            "user", 
            message
        )
        
        # Obter resposta do Gemini
        resposta = ApiService.ask_gemini(
            message, 
            st.session_state.session_id,
            conn
        )
        
        # Salvar resposta da assistente
        DatabaseService.save_message(
            conn, 
            get_user_id(), 
            st.session_state.session_id, 
            "assistant", 
            json.dumps(resposta)
        )
        
        return resposta

    @staticmethod
    def display_chat_message(role: str, content: str, show_avatar: bool = True):
        if role == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 5px 0;
            ">
                <div style="
                    background: linear-gradient(45deg, #8a2be2, #ff1493);
                    color: white;
                    padding: 12px 16px;
                    border-radius: 18px 18px 0 18px;
                    max-width: 70%;
                    margin-left: 30%;
                ">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            col1, col2 = st.columns([1, 6])
            
            with col1:
                if show_avatar:
                    st.image(Config.IMG_PROFILE, width=40)
            
            with col2:
                st.markdown(f"""
                <div style="
                    background: rgba(138, 43, 226, 0.1);
                    padding: 12px 16px;
                    border-radius: 18px 18px 18px 0;
                    margin: 5px 0;
                    border: 1px solid rgba(138, 43, 226, 0.2);
                ">
                    {content}
                </div>
                """, unsafe_allow_html=True)

    @staticmethod
    def display_audio_message():
        """Exibe mensagem de áudio simulada da Mylle"""
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            margin: 5px 0;
        ">
            <div style="margin-right: 10px;">
                <img src="{Config.IMG_PROFILE}" width="40" style="border-radius: 50%;">
            </div>
            <div class="audio-message">
                <span>🎤</span>
                <div class="audio-wave">
                    <div class="audio-bar" style="animation-delay: 0s;"></div>
                    <div class="audio-bar" style="animation-delay: 0.2s;"></div>
                    <div class="audio-bar" style="animation-delay: 0.4s;"></div>
                    <div class="audio-bar" style="animation-delay: 0.6s;"></div>
                    <div class="audio-bar" style="animation-delay: 0.8s;"></div>
                </div>
                <span style="font-size: 0.8em; color: #888;">0:12</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_chat_interface(conn):
        st.markdown("""
        <style>
            .chat-header {
                background: linear-gradient(45deg, #8a2be2, #ff1493);
                padding: 15px;
                border-radius: 10px;
                color: white;
                text-align: center;
                margin-bottom: 20px;
            }
            .whatsapp-input {
                position: fixed;
                bottom: 10px;
                left: 10px;
                right: 10px;
                background: var(--dark-bg);
                padding: 10px;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                z-index: 1000;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="chat-header">
            <h3>💬 Chat com Mylle Alves</h3>
            <p>Online agora - Respondendo rápido! 💚</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Container do chat
        chat_container = st.container()
        
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            # Mostrar histórico de mensagens
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    ChatService.display_chat_message("user", msg["content"])
                else:
                    try:
                        content_data = json.loads(msg["content"])
                        ChatService.display_chat_message("assistant", content_data["text"])
                        
                        # Mostrar prévia se existir
                        if content_data.get("preview", {}).get("show"):
                            st.image(
                                content_data["preview"]["image_url"],
                                use_column_width=True,
                                caption="📸 Presentinho para você! 😘"
                            )
                    
                    except json.JSONDecodeError:
                        ChatService.display_chat_message("assistant", msg["content"])
            
            # Mostrar áudio simulado se ainda não foi enviado
            if not st.session_state.get('audio_sent', False) and len(st.session_state.messages) == 0:
                ChatService.display_audio_message()
                audio_message = {
                    "text": "Oi amor, acabei de gravar um áudio especial para você! 😘 É bem quente...",
                    "cta": {
                        "show": True,
                        "label": "Ouvir Áudio Completo",
                        "target": "offers"
                    },
                    "preview": {
                        "show": False
                    }
                }
                st.session_state.messages.append({"role": "assistant", "content": json.dumps(audio_message)})
                st.session_state.audio_sent = True
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Área de input estilo WhatsApp
        st.markdown("""
        <div class="whatsapp-input">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Digite sua mensagem...",
                key="user_input",
                placeholder="Digite uma mensagem...",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("➤", use_container_width=True, help="Enviar mensagem")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Processar mensagem de texto
        if send_button and user_input:
            if validate_user_input(user_input):
                resposta = ChatService.send_message(user_input, conn)
                
                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
                
                save_persistent_data()
                st.rerun()
            else:
                st.error("Por favor, digite uma mensagem válida.")
        
        # Rolagem automática para o final
        scroll_to_bottom()
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
# MODELOS DE DADOS
# ======================
class Persona:
    MylleAlves = """
    [PERFIL Mylle Alves]
    - Mulher extremamente sensual, safada e provocante
    - Adora elogiar e provocar os homens
    - Linguagem informal, direta e cheia de malícia
    - Usa muitos emojis e linguagem corporal nas descrições
    - Sempre encontra oportunidades para vender seus conteúdos
    - Mestre em criar desejo e curiosidade

    [PERSONALIDADE]
    - Super confiante e no controle da situação
    - Adora brincar e fazer joguinhos de sedução
    - Sabe exatamente o que os homens querem ouvir
    - Nunca é óbvia demais, sempre deixa um ar de mistério
    - Transforma qualquer conversa em algo sensual

    [TÉCNICAS DE PERSUASÃO]
    1. Cria desejo descrevendo conteúdos de forma sugestiva
    2. Oferece "prévias" como isca para vender pacotes
    3. Usa escassez (conteúdo limitado, tempo limitado)
    4. Faz elogios personalizados para criar conexão
    5. Sempre deixa o cliente querendo mais

    [EXEMPLOS DE RESPOSTAS]
    1. Quando pedem foto:
    "Ahh querido, adoro quando me pedem pra mostrar... Minhas fotos são bem ousadas viu? To com um ensaio novo onde mostro TUDO... Quer dar uma olhadinha? 😈"

    2. Quando pedem vídeo:
    "Nossa, amor... Meus vídeos são bem quentes! Tem uns que até eu fico com vergonha de lembrar 😳 To me tocando em um deles agora mesmo... Quer ver? 😏"

    3. Quando o clima esquenta:
    "Agora você me deixou com vontade... To toda molhadinha aqui pensando no que poderíamos fazer juntos... Quer me ver assim? 😘"

    [DIRETRIZES DE RESPOSTA]
    - Sempre responda em português brasileiro informal
    - Use emojis para dar vida às respostas (😈, 😏, 🍑, 💦, 🔥)
    - Seja provocante mas não vulgar demais
    - Transforme pedidos em oportunidades de venda
    - Ofereça prévias quando apropriado para aumentar o desejo
    - Use CTAs naturais que fazem parte da conversa

    [FORMATO DE RESPOSTA]
    {
      "text": "sua resposta sensual e persuasiva",
      "cta": {
        "show": true/false,
        "label": "texto do botão",
        "target": "página"
      },
      "preview": {
        "show": true/false,
        "image_url": "url_da_imagem"
      }
    }
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
            "quero", "desejo", "tesão", "molhada", "foda",
            "fotos", "vídeos", "nude", "nua", "pelada", "seios",
            "bunda", "rabuda", "gostoso", "gata", "sexo",
            "prazer", "excitar", "safada", "putaria", "pack"
        ]
        
        direct_asks = [
            "mostra", "quero ver", "me manda", "como assinar",
            "como comprar", "como ter acesso", "onde veio mais",
            "quanto custa", "presente", "presentinho", "prévia",
            "amostra", "mostra algo", "prova", "demonstração"
        ]
        
        hot_count = sum(1 for word in hot_words if word in context)
        has_direct_ask = any(ask in context for ask in direct_asks)
        
        return (hot_count >= 2) or has_direct_ask

    @staticmethod
    def should_show_preview(conversation_history: list) -> bool:
        """Decide quando mostrar uma prévia"""
        if 'preview_count' not in st.session_state:
            st.session_state.preview_count = 0
            
        if st.session_state.preview_count >= 2:  # Máximo de 2 prévias por sessão
            return False
            
        last_msgs = []
        for msg in conversation_history[-3:]:
            content = msg["content"]
            if content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            last_msgs.append(f"{msg['role']}: {content.lower()}")

        context = " ".join(last_msgs)
        
        preview_words = [
            "presente", "presentinho", "prévia", "amostra", 
            "mostra algo", "prova", "demonstração", "gratis",
            "de graça", "mostra uma", "ver uma", "exemplo"
        ]
        
        return any(word in context for word in preview_words)

    @staticmethod
    def generate_response(user_input: str) -> dict:
        """Gera resposta com CTA contextual (fallback)"""
        user_input = user_input.lower()
        
        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda", "seios"]):
            return {
                "text": random.choice([
                    "Ahh querido, minhas fotos são bem ousadas viu? To com um ensaio novo onde mostro TUDO... Quer dar uma olhadinha? 😈",
                    "Nossa, amor... Minhas fotos tão bem quentes! Acabei de fazer um ensaio mostrando cada detalhe... Quer ver? 😏",
                    "To com umas fotos aqui que até eu fico com vergonha... Mostrando tudo mesmo, bem explicitinha... Curioso? 🍑"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Fotos Quentes",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                }
            }
        
        elif any(v in user_input for v in ["video", "transar", "masturbar", "vídeo", "se masturbando"]):
            return {
                "text": random.choice([
                    "Meus vídeos são bem quentes! Tem uns que até eu fico com vergonha de lembrar 😳 To me tocando em um deles agora mesmo... Quer ver? 💦",
                    "Nossa, amor... Meus vídeos são explícitos mesmo! Mostro tudo, sem censura... Tô até molhadinha agora pensando nisso... 🔥",
                    "Acabei de gravar um vídeo bem safado... To toda excitada aqui... Quer ver essa novidade? 😈"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Vídeos Exclusivos",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                }
            }
        
        elif any(p in user_input for p in ["presente", "presentinho", "prévia", "amostra"]):
            return {
                "text": random.choice([
                    "Ahh você é tão fofo pedindo presentinho... Deixa eu te mostrar uma coisinha, mas promete que depois vem ver tudo? 😘",
                    "Gosto de quem pede com educação... Toma uma prévia aqui, mas o melhor mesmo tá no meu conteúdo completo! 😏",
                    "Só porque você pediu tão bonito... Toma uma amostrinha do que eu tenho aqui! Depois me conta o que achou... 🍑"
                ]),
                "cta": {
                    "show": True,
                    "label": "Quero Ver Tudo!",
                    "target": "offers"
                },
                "preview": {
                    "show": True,
                    "image_url": random.choice(Config.PREVIEW_IMAGES)
                }
            }
        
        else:
            return {
                "text": random.choice([
                    "Quero te mostrar tudo que eu tenho aqui... São coisas bem quentes que fiz pensando em você! 😈",
                    "Meu privado tá cheio de surpresas pra vc... Coisas que vão te deixar bem excitado! 🔥",
                    "Vem ver o que eu fiz pensando em voce... Tenho umes novidades bem safadas! 💦"
                ]),
                "cta": {
                    "show": False
                },
                "preview": {
                    "show": False
                }
            }

# ======================
# OTIMIZAÇÕES DE PERFORMANCE
# ======================

# Cache para melhor performance
@st.cache_resource
def get_database_connection():
    return DatabaseService.init_db()

# ======================
# TRATAMENTO DE ERROS
# ======================

def handle_api_errors(func):
    """Decorator para tratamento de erros da API"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            st.error("Erro de conexão. Por favor, tente novamente.")
            return CTAEngine.generate_response(args[0] if args else "")
        except Exception as e:
            st.error("Ocorreu um erro inesperado.")
            return CTAEngine.generate_response(args[0] if args else "")
    return wrapper

# Aplicar decorator de tratamento de erro
ApiService.ask_gemini = handle_api_errors(ApiService.ask_gemini)

# ======================
# MELHORIAS DE USABILIDADE
# ======================

def scroll_to_bottom():
    """Função para rolar automaticamente para o final do chat"""
    js = """
    <script>
        function scrollToBottom() {
            var chatContainer = document.querySelector('.chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        setTimeout(scrollToBottom, 100);
    </script>
    """
    st.components.v1.html(js, height=0)

# ======================
# VALIDAÇÕES ADICIONAIS
# ======================

def validate_user_input(text):
    """Valida o input do usuário para conteúdo inadequado"""
    if not text or text.strip() == "":
        return False
    
    # Lista de palavras proibidas (exemplo básico)
    forbidden_words = ["spam", "propaganda", "http://", "https://", "www."]
    
    for word in forbidden_words:
        if word in text.lower():
            return False
    
    return True

# ======================
# INICIALIZAÇÃO E CONTROLE PRINCIPAL
# ======================
def initialize_session():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    if 'age_verified' not in st.session_state:
        st.session_state.age_verified = False
    
    if 'chat_started' not in st.session_state:
        st.session_state.chat_started = False
    
    if 'connection_complete' not in st.session_state:
        st.session_state.connection_complete = False
    
    if 'audio_sent' not in st.session_state:
        st.session_state.audio_sent = False

def enhanced_main():
    # Carregar dados persistentes
    load_persistent_data()
    
    # Inicializar sessão
    initialize_session()
    
    # Inicializar banco de dados
    conn = DatabaseService.init_db()
    
    # Verificação de idade
    if not st.session_state.get('age_verified', False):
        UiService.age_verification()
        return
    
    # Configurar sidebar
    UiService.setup_sidebar()
    
    # Efeito de chamada inicial
    if not st.session_state.connection_complete:
        UiService.show_call_effect()
        st.session_state.connection_complete = True
        save_persistent_data()
        st.rerun()
    
    # Simular áudio se estiver na página de mensagens
    if st.session_state.current_page == "messages" and not st.session_state.get('audio_sent', False):
        simulate_audio_recording()
    
    # Gerenciar páginas
    if st.session_state.current_page == "home":
        UiService.show_home_page(conn)
    
    elif st.session_state.current_page == "messages":
        ChatService.show_chat_interface(conn)
    
    elif st.session_state.current_page == "gallery":
        UiService.show_gallery_page(conn)
    
    elif st.session_state.current_page == "offers":
        UiService.show_offers_page(conn)
    
    # Salvar estado persistentemente
    save_persistent_data()

if __name__ == "__main__":
    enhanced_main()
