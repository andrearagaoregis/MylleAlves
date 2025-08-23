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

# Novo tema Ninho Hot (tons de rosa e roxo)
ninho_hot_theme_style = """
<style>
    :root {
        --primary-color: #ff2a6d;
        --secondary-color: #d1005d;
        --accent-color: #ff2a6d;
        --dark-bg: #1a001a;
        --light-bg: #330033;
        --text-color: #ffffff;
        --border-color: #ff2a6d;
        --chat-user-bg: #ff2a6d;
        --chat-model-bg: #4d004d;
        --whatsapp-green: #128C7E;
        --whatsapp-light-green: #25D366;
        --whatsapp-chat-bg: #0d1418;
    }
    
    .stApp {
        background: var(--whatsapp-chat-bg);
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
    
    /* Estilo do chat estilo WhatsApp melhorado */
    .chat-container {
        height: calc(100vh - 120px);
        overflow-y: auto;
        padding: 10px;
        background: url('https://i.ibb.co/6WQ0q1R/whatsapp-bg.png');
        background-size: cover;
        margin-bottom: 70px;
        padding-bottom: 20px;
    }
    
    .user-message {
        background: var(--whatsapp-light-green);
        color: white;
        padding: 8px 12px;
        border-radius: 7.5px 0 7.5px 7.5px;
        margin: 5px 0;
        max-width: 70%;
        margin-left: auto;
        text-align: right;
        box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
        position: relative;
    }
    
    .model-message {
        background: var(--chat-model-bg);
        color: white;
        padding: 8px 12px;
        border-radius: 0 7.5px 7.5px 7.5px;
        margin: 5px 0;
        max-width: 70%;
        margin-right: auto;
        box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
        position: relative;
    }
    
    .message-time {
        font-size: 0.65em;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 3px;
        text-align: right;
        float: right;
        margin-left: 7px;
    }
    
    .message-avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 8px;
    }
    
    .fixed-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--whatsapp-chat-bg);
        padding: 10px 15px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .message-input {
        flex-grow: 1;
        background: #2a2f32;
        border: none;
        border-radius: 20px;
        padding: 9px 15px;
        color: white;
        font-size: 15px;
    }
    
    .send-button {
        background: var(--whatsapp-light-green);
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
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
    
    .audio-recording {
        display: flex;
        align-items: center;
        background: rgba(255, 42, 109, 0.1);
        padding: 10px 15px;
        border-radius: 18px;
        margin: 10px 0;
        max-width: 80%;
    }
    
    .audio-wave {
        display: flex;
        align-items: center;
        gap: 3px;
        margin: 0 10px;
    }
    
    .audio-bar {
        width: 3px;
        background: var(--primary-color);
        border-radius: 2px;
        animation: audioWave 1.5s infinite ease-in-out;
    }
    
    .audio-bar:nth-child(2) { animation-delay: 0.2s; height: 8px; }
    .audio-bar:nth-child(3) { animation-delay: 0.4s; height: 12px; }
    .audio-bar:nth-child(4) { animation-delay: 0.6s; height: 15px; }
    .audio-bar:nth-child(5) { animation-delay: 0.8s; height: 12px; }
    .audio-bar:nth-child(6) { animation-delay: 1.0s; height: 8px; }
    
    @keyframes audioWave {
        0%, 100% { height: 5px; }
        50% { height: 15px; }
    }
    
    @media (min-width: 768px) {
        .sidebar-logo {
            width: 320px;
        }
        
        .chat-container {
            height: calc(100vh - 100px);
        }
    }
</style>
"""
st.markdown(ninho_hot_theme_style, unsafe_allow_html=True)

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
        'last_cta_time', 'preview_sent', 'preview_count',
        'audio_played'
    ]
    
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}
    
    if new_data != saved_data:
        db.save_state(user_id, new_data)

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
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def show_call_effect():
        LIGANDO_DELAY = 5
        ATENDIDA_DELAY = 3

        call_container = st.empty()
        call_container.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a001a, #330033);
            border-radius: 20px;
            padding: 30px;
            max-width: 300px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 2px solid #ff2a6d;
            text-align: center;
            color: white;
            animation: pulse-ring 2s infinite;
        ">
            <div style="font-size: 3rem;">📱</div>
            <h3 style="color: #ff2a6d; margin-bottom: 5px;">Ligando para Mylle Alves...</h3>
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
            background: linear-gradient(135deg, #1a001a, #330033);
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
            <p style="font-size: 0.9rem; margin:0;">Mylle Alves está te esperando...</p>
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
                background: linear-gradient(145deg, #1a001a, #330033);
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 42, 109, 0.2);
                color: white;
            }
            .age-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 1.5rem;
            }
            .age-icon {
                font-size: 2.5rem;
                color: #ff2a6d;
            }
            .age-title {
                font-size: 1.8rem;
                font-weight: 700;
                margin: 0;
                color: #ff2a6d;
            }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("""
            <div class="age-verification">
                <div class="age-header">
                    <div class="age-icon">🔞</div>
                    <h1 class="age-title">Verificação de Idade</h1>
                </div>
                <div class="age-content">
                    <p>Este site contém material explícito destinado exclusivamente a adultos maiores de 18 anos.</p>
                    <p>Ao acessar este conteúdo, você declara estar em conformidade com todas as leis local aplicáveis.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("Confirmo que sou maior de 18 anos", 
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
                    background: linear-gradient(180deg, #1a001a 0%, #330033 100%) !important;
                    border-right: 1px solid #ff2a6d !important;
                }
                .sidebar-logo-container {
                    margin: -25px -25px 0px -25px;
                    padding: 0;
                    text-align: left;
                }
                .sidebar-header {
                    text-align: center; 
                    margin-bottom: 20px;
                }
                .sidebar-header img {
                    border-radius: 50%; 
                    border: 2px solid #ff2a6d;
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
                    background: rgba(255, 42, 109, 0.2);
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
            
            st.markdown("""
            <div class="sidebar-header">
                <img src="{profile_img}" alt="Mylle Alves">
                <h3 style="color: #ff2a6d; margin-top: 10px;">Mylle Alves Premium</h3>
            </div>
            """.format(profile_img=Config.IMG_PROFILE), unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### Menu Exclusivo")
            
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
            st.markdown("### Sua Conta")
            
            st.markdown("""
            <div style="
                background: rgba(255, 42, 109, 0.1);
                padding: 10px;
                border-radius: 8px;
                text-align: center;
            ">
                <p style="margin:0;">Acesse conteúdo exclusivo</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### Conteúdo VIP")
            st.markdown("""
            <div class="vip-badge">
                <p style="margin: 0 0 10px; font-weight: bold;">Acesso completo por apenas</p>
                <p style="margin: 0; font-size: 1.5em; font-weight: bold;">R$ 29,90/mês</p>
                <p style="margin: 10px 0 0; font-size: 0.8em;">Cancele quando quiser</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Ver Conteúdo VIP", use_container_width=True, type="primary"):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()
            
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; font-size: 0.7em; color: #888;">
                <p>© 2024 Mylle Alves Premium</p>
                <p>Conteúdo para maiores de 18 anos</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def show_gallery_page(conn):
        st.markdown("""
        <div style="
            background: rgba(255, 42, 109, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <p style="margin: 0;">Conteúdo exclusivo disponível</p>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(3)
        
        for idx, col in enumerate(cols):
            if idx < len(Config.IMG_GALLERY):
                with col:
                    st.image(Config.IMG_GALLERY[idx], use_column_width=True)
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: 10px;">
                        <span style="color: #ff2a6d; font-weight: bold;">Foto Exclusiva #{idx + 1}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔐 Acesso VIP Completo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(45deg, #ff2a6d, #d1005d);
                padding: 20px;
                border-radius: 10px;
                color: white;
                text-align: center;
            ">
                <h4>📸 Pacote Fotos</h4>
                <p style="font-size: 1.2em; font-weight: bold;">R$ 19,90</p>
                <p>+100 fotos exclusivas</p>
                <p>Ensaio completo</p>
                <p>Sem censura</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar Fotos", key="buy_photos", use_container_width=True):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()
        
        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(45deg, #ff2a6d, #d1005d);
                padding: 20px;
                border-radius: 10px;
                color: white;
                text-align: center;
            ">
                <h4>🎥 Pacote Completo</h4>
                <p style="font-size: 1.2em; font-weight: bold;">R$ 49,90</p>
                <p>Fotos + Vídeos</p>
                <p>Conteúdo explícito</p>
                <p>Acesso vitalício</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar Completo", key="buy_complete", use_container_width=True):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()
            
    @staticmethod
    def show_offers_page(conn):
        st.markdown("""
        <div style="
            background: linear-gradient(45deg, #ff2a6d, #d1005d);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h2>💎 OFERTAS EXCLUSIVAS</h2>
            <p>Escolha o pacote perfeito para você</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="
                background: rgba(255, 42, 109, 0.1);
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #ff2a6d;
                text-align: center;
                height: 400px;
            ">
                <h3 style="color: #ff2a6d;">🔥 Taradinha</h3>
                <div style="font-size: 2em; color: #ff2a6d; font-weight: bold;">R$ 9,90</div>
                <div style="margin: 20px 0;">
                    <p>✓ 20 fotos sensuais</p>
                    <p>✓ 1 vídeo curto</p>
                    <p>✓ Conteúdo leve</p>
                    <p>✓ Acesso por 7 dias</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar Taradinha", key="buy_taradinha", use_container_width=True):
                st.markdown(f'<meta http-equiv="refresh" content="0; url={Config.CHECKOUT_TARADINHA}">', unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(45deg, #ff2a6d, #d1005d);
                padding: 20px;
                border-radius: 10px;
                color: white;
                text-align: center;
                height: 400px;
            ">
                <h3>💦 Molhadinha</h3>
                <div style="font-size: 2em; font-weight: bold;">R$ 19,90</div>
                <div style="margin: 20px 0;">
                    <p>✓ 50 fotos explícitas</p>
                    <p>✓ 3 vídeos quentes</p>
                    <p>✓ Conteúdo médio</p>
                    <p>✓ Acesso por 30 dias</p>
                    <p>✓ BÔNUS: 1 áudio</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar Molhadinha", key="buy_molhadinha", use_container_width=True):
                st.markdown(f'<meta http-equiv="refresh" content="0; url={Config.CHECKOUT_MOLHADINHA}">', unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="
                background: rgba(209, 0, 93, 0.1);
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #d1005d;
                text-align: center;
                height: 400px;
            ">
                <h3 style="color: #d1005d;">😈 Safadinha</h3>
                <div style="font-size: 2em; color: #d1005d; font-weight: bold;">R$ 49,90</div>
                <div style="margin: 20px 0;">
                    <p>✓ 100+ fotos explícitas</p>
                    <p>✓ 10+ vídeos completos</p>
                    <p>✓ Conteúdo hardcore</p>
                    <p>✓ Acesso VITALÍCIO</p>
                    <p>✓ BÔNUS: Áudios + Chat</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Comprar Safadinha", key="buy_safadinha", use_container_width=True):
                st.markdown(f'<meta http-equiv="refresh" content="0; url={Config.CHECKOUT_SAFADINHA}">', unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("""
        <div style="
            background: rgba(255, 42, 109, 0.05);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        ">
            <h4>🎁 Garantia de Satisfação</h4>
            <p>Se não gostar em 7 dias, devolvemos seu dinheiro!</p>
        </div>
        """, unsafe_allow_html=True)

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
    def display_chat_message(role: str, content: str, timestamp: str = None, show_avatar: bool = True):
        if timestamp is None:
            now = datetime.now()
            timestamp = now.strftime("%H:%M")
        
        if role == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 5px 0;
            ">
                <div style="
                    background: var(--whatsapp-light-green);
                    color: white;
                    padding: 8px 12px;
                    border-radius: 7.5px 0 7.5px 7.5px;
                    max-width: 70%;
                    margin-left: 30%;
                    box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
                ">
                    {content}
                    <div class="message-time">{timestamp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            col1, col2 = st.columns([1, 6])
            
            with col1:
                if show_avatar:
                    st.image(Config.IMG_PROFILE, width=35)
            
            with col2:
                st.markdown(f"""
                <div style="
                    background: var(--chat-model-bg);
                    padding: 8px 12px;
                    border-radius: 0 7.5px 7.5px 7.5px;
                    margin: 5px 0;
                    box-shadow: 0 1px 0.5px rgba(0, 0, 0, 0.13);
                ">
                    {content}
                    <div class="message-time">{timestamp}</div>
                </div>
                """, unsafe_allow_html=True)

    @staticmethod
    def display_audio_message():
        """Exibe uma mensagem de áudio simulada"""
        st.markdown(f"""
        <div style="
            display: flex;
            margin: 10px 0;
        ">
            <img src="{Config.IMG_PROFILE}" width="35" style="border-radius: 50%; margin-right: 8px;">
            <div class="audio-recording">
                <span style="color: #ff2a6d;">▶️</span>
                <div class="audio-wave">
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                </div>
                <span style="font-size: 0.8em; color: rgba(255, 255, 255, 0.6);">0:12</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_chat_interface(conn):
        st.markdown("""
        <style>
            .chat-header {
                background: var(--whatsapp-chat-bg);
                padding: 15px;
                color: white;
                text-align: center;
                margin-bottom: 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                position: sticky;
                top: 0;
                z-index: 100;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="chat-header">
            <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
                <img src="{Config.IMG_PROFILE}" width="40" style="border-radius: 50%;">
                <div>
                    <h4 style="margin: 0; color: white;">Mylle Alves</h4>
                    <p style="margin: 0; font-size: 0.8em; color: #25D366;">Online agora • Digitando...</p>
                </div>
            </div>
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
            
            # Mostrar áudio simulado se ainda não foi mostrado
            if st.session_state.get('show_audio_message', True):
                ChatService.display_audio_message()
                st.session_state.show_audio_message = False
                save_persistent_data()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Área de input estilo WhatsApp no rodapé
        st.markdown("""
        <div class="fixed-input">
            <input type="text" class="message-input" placeholder="Digite uma mensagem" id="messageInput">
            <button class="send-button" onclick="sendMessage()">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="#ffffff">
                    <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"></path>
                </svg>
            </button>
        </div>
        
        <script>
            function sendMessage() {
                const input = document.getElementById('messageInput');
                if (input.value.trim() !== '') {
                    // Streamlit não suporta diretamente a execução de Python a partir de JavaScript
                    // Esta função precisará ser integrada com o Streamlit
                    console.log('Mensagem enviada:', input.value);
                    input.value = '';
                }
            }
            
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
        """, unsafe_allow_html=True)
        
        # Implementação alternativa para enviar mensagens (Streamlit)
        user_input = st.text_input(
            "Digite sua mensagem...",
            key="user_input",
            placeholder="Digite uma mensagem",
            label_visibility="collapsed"
        )
        
        if st.button("Enviar", key="send_button"):
            if user_input:
                resposta = ChatService.send_message(user_input, conn)
                
                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
                
                save_persistent_data()
                st.rerun()

# ======================
# SERVIÇOS DE INTERFACE (CONTINUAÇÃO)
# ======================
class UiService:
    @staticmethod
    def show_home_page(conn):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(Config.IMG_PROFILE, use_column_width=True)
            st.markdown("""
            <div style="text-align: center; margin-top: 10px;">
                <h3 style="color: #ff2a6d;">Mylle Alves</h3>
                <p style="color: #25D366;">Online agora 💚</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("""
            <div style="
                background: rgba(255, 42, 109, 0.1);
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
                background: linear-gradient(45deg, #ff2a6d, #d1005d);
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
                background: rgba(255, 42, 109, 0.1);
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
            
            if st.button("💬 Iniciar Conversa", use_container_width=True, type="primary"):
                st.session_state.current_page = "messages"
                save_persistent_data()
                st.rerun()

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
    
    if 'show_audio_message' not in st.session_state:
        st.session_state.show_audio_message = True

def main():
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
    main()
# ======================
# INICIALIZAÇÃO E CONTROLE PRINCIPAL (CONTINUAÇÃO)
# ======================

# Esta é a continuação do código principal
# A função main() já foi definida na parte anterior

# Garantir que o código seja executado corretamente
if __name__ == "__main__":
    main()

# ======================
# FUNÇÕES ADICIONAIS E MELHORIAS
# ======================

# Adicionando funcionalidade de simulação de gravação de áudio
def simulate_audio_recording():
    """Simula o envio de um áudio pela modelo"""
    if 'audio_sent' not in st.session_state:
        st.session_state.audio_sent = False
    
    if not st.session_state.audio_sent and st.session_state.current_page == "messages":
        # Aguardar um pouco antes de enviar o áudio
        time.sleep(2)
        
        # Adicionar mensagem de áudio da modelo
        audio_message = {
            "text": "Oi amor, acabei de gravar um áudio especial para você! 😘 Quer ouvir? É bem quente...",
            "cta": {
                "show": True,
                "label": "Ouvir Áudio Exclusivo",
                "target": "offers"
            },
            "preview": {
                "show": False
            }
        }
        
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(audio_message)})
        st.session_state.audio_sent = True
        save_persistent_data()
        st.rerun()

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
# ATUALIZAÇÃO DO CHAT SERVICE
# ======================

# Atualizar o método show_chat_interface para incluir rolagem automática
def updated_show_chat_interface(conn):
    st.markdown("""
    <style>
        .chat-header {
            background: var(--whatsapp-chat-bg);
            padding: 15px;
            color: white;
            text-align: center;
            margin-bottom: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .streamlit-input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--whatsapp-chat-bg);
            padding: 10px 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .streamlit-input-container > div {
            flex-grow: 1;
        }
        
        .streamlit-input-container input {
            background: #2a2f32 !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 9px 15px !important;
            color: white !important;
            font-size: 15px !important;
            width: 100% !important;
        }
        
        .streamlit-input-container button {
            background: var(--whatsapp-light-green) !important;
            border: none !important;
            border-radius: 50% !important;
            width: 40px !important;
            height: 40px !important;
            color: white !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            margin: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="chat-header">
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
            <img src="{Config.IMG_PROFILE}" width="40" style="border-radius: 50%;">
            <div>
                <h4 style="margin: 0; color: white;">Mylle Alves</h4>
                <p style="margin: 0; font-size: 0.8em; color: #25D366;">Online agora • Digitando...</p>
            </div>
        </div>
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
        
        # Mostrar áudio simulado se ainda não foi mostrado
        if st.session_state.get('show_audio_message', True):
            ChatService.display_audio_message()
            st.session_state.show_audio_message = False
            save_persistent_data()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Rolagem automática para o final
    scroll_to_bottom()
    
    # Área de input estilo WhatsApp no rodapé usando componentes Streamlit nativos
    st.markdown('<div class="streamlit-input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Digite sua mensagem...",
            key="user_input",
            placeholder="Digite uma mensagem",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("➤", key="send_button")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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

# Substituir a função original pela atualizada
ChatService.show_chat_interface = updated_show_chat_interface

# ======================
# INICIALIZAÇÃO AUTOMÁTICA DE ÁUDIO
# ======================

# Adicionar simulação de áudio após a inicialização
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
    if st.session_state.current_page == "messages" and not st.session_state.audio_sent:
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

# Substituir a função main original pela enhanced
if __name__ == "__main__":
    enhanced_main()
