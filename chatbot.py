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
import logging
from datetime import datetime
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import hashlib

# ======================
# CONFIGURAÇÃO DE LOGGING
# ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mylle_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MylleBot")

# ======================
# CONFIGURAÇÃO INICIAL DO STREAMLIT
# ======================
st.set_page_config(
    page_title="Mylle Alves Premium",
    page_icon="💋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações de performance
st._config.set_option('client.caching', True)
st._config.set_option('client.showErrorDetails', False)

hide_streamlit_style = """
<style>
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    #MainMenu {display: none !important;}
    header {display: none !important;}
    footer {display: none !important;}
    .stDeployButton {display: none !important;}
    .block-container {padding-top: 0rem !important;}
    [data-testid="stVerticalBlock"] {gap: 0.5rem !important;}
    [data-testid="stHorizontalBlock"] {gap: 0.5rem !important;}
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
        background: linear-gradient(135deg, #1a0033 0%, #2d004d 50%, #1a0033 100%);
        color: white;
    }
    .stChatMessage {padding: 12px !important; border-radius: 15px !important; margin: 8px 0 !important;}
    .audio-message {
        background: rgba(255, 102, 179, 0.15) !important;
        padding: 15px !important;
        border-radius: 15px !important;
        margin: 10px 0 !important;
        border: 1px solid #ff66b3 !important;
        text-align: center !important;
    }
    .audio-icon {font-size: 24px !important; margin-right: 10px !important;}
    .preview-counter {
        background: rgba(255, 102, 179, 0.2);
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        margin: 10px 0;
        text-align: center;
        border: 1px solid #ff66b3;
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
    CHECKOUT_TARADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACC74F-01EC-4770-B182-B5775AF62A1D"
    CHECKOUT_MOLHADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD1E6-0EFD-4E3E-9F9D-BA0C1A2D7E7A"
    CHECKOUT_SAFADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD395-EE65-458E-9B7E-FED750CC9CA9"
    MAX_REQUESTS_PER_SESSION = 50
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
    PREVIEW_IMAGES = [
        "https://i.ibb.co/0Q8Lx0Z/preview1.jpg",
        "https://i.ibb.co/7YfT9y0/preview2.jpg",
        "https://i.ibb.co/5KjX1J0/preview3.jpg",
        "https://i.ibb.co/0jq4Z0L/preview4.jpg"
    ]
    
    # URLs dos áudios
    AUDIOS = {
        "amostra_gratis": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Claro%20eu%20tenho%20amostra%20gr%C3%A1tis.mp3",
        "achou_amostras": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/O%20que%20achou%20das%20amostras.mp3",
        "nao_chamada": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Pq%20nao%20fa%C3%A7o%20mais%20chamada.mp3",
        "conteudos_amar": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/eu%20tenho%20uns%20conteudos%20aqui%20que%20vc%20vai%20amar.mp3",
        "esperando_responder": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/vida%20to%20esperando%20voce%20me%20responder%20gatinho.mp3",
        "nao_sou_fake": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/nao%20sou%20fake%20nao..mp3",
        "imagininha_rosinha": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Imagina%20s%C3%B3%20ela%20bem%20rosinha%20(putaria).mp3"
    }

# ======================
# SISTEMA DE CACHE INTELIGENTE
# ======================
class ResponseCache:
    def __init__(self, max_size=500):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get_cache_key(self, prompt: str, context: str) -> str:
        """Gera chave única para cache baseada no prompt e contexto"""
        key_str = f"{prompt[:100]}_{context[:100]}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, prompt: str, context: str) -> dict:
        """Obtém resposta do cache se existir"""
        key = self.get_cache_key(prompt, context)
        if key in self.cache:
            self.hits += 1
            logger.info(f"Cache hit: {key}")
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, prompt: str, context: str, response: dict) -> None:
        """Armazena resposta no cache"""
        if len(self.cache) >= self.max_size:
            # Remove o item mais antigo (FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self.get_cache_key(prompt, context)
        self.cache[key] = response
        logger.info(f"Cache set: {key}")
    
    def clear(self) -> None:
        """Limpa o cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

# Instância global do cache
response_cache = ResponseCache()

# ======================
# APRENDIZADO DE MÁQUINA
# ======================
class LearningEngine:
    def __init__(self):
        self.user_preferences = defaultdict(dict)
        self.conversation_patterns = defaultdict(list)
        self.load_learning_data()
    
    def load_learning_data(self):
        try:
            conn = sqlite3.connect('learning_data.db', check_same_thread=False)
            c = conn.cursor()
            
            # Tabela de preferências
            c.execute('''CREATE TABLE IF NOT EXISTS user_preferences
                        (user_id TEXT, preference_type TEXT, preference_value TEXT, strength REAL,
                         PRIMARY KEY (user_id, preference_type))''')
            
            # Tabela de informações do lead
            c.execute('''CREATE TABLE IF NOT EXISTS lead_info
                        (user_id TEXT PRIMARY KEY, name TEXT, location TEXT, created_at DATETIME,
                         message_count INTEGER DEFAULT 0, last_interaction DATETIME)''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao carregar dados de aprendizado: {e}")
    
    def save_user_preference(self, user_id: str, preference_type: str, preference_value: str, strength: float = 1.0):
        try:
            conn = sqlite3.connect('learning_data.db', check_same_thread=False)
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO user_preferences 
                        (user_id, preference_type, preference_value, strength)
                        VALUES (?, ?, ?, ?)''', 
                     (user_id, preference_type, preference_value, strength))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao salvar preferência: {e}")
    
    def get_user_preferences(self, user_id: str) -> dict:
        preferences = {}
        try:
            conn = sqlite3.connect('learning_data.db', check_same_thread=False)
            c = conn.cursor()
            c.execute('''SELECT preference_type, preference_value, strength 
                        FROM user_preferences WHERE user_id = ?''', (user_id,))
            for row in c.fetchall():
                if row[0] not in preferences:
                    preferences[row[0]] = {}
                preferences[row[0]][row[1]] = row[2]
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao obter preferências: {e}")
        return preferences
    
    def save_lead_info(self, user_id: str, name: str = None, location: str = None):
        try:
            conn = sqlite3.connect('learning_data.db', check_same_thread=False)
            c = conn.cursor()
            
            # Verificar se já existe
            c.execute('SELECT * FROM lead_info WHERE user_id = ?', (user_id,))
            if c.fetchone():
                if name:
                    c.execute('UPDATE lead_info SET name = ? WHERE user_id = ?', (name, user_id))
                if location:
                    c.execute('UPDATE lead_info SET location = ? WHERE user_id = ?', (location, user_id))
                c.execute('UPDATE lead_info SET message_count = message_count + 1, last_interaction = ? WHERE user_id = ?',
                         (datetime.now(), user_id))
            else:
                c.execute('INSERT INTO lead_info (user_id, name, location, created_at, message_count, last_interaction) VALUES (?, ?, ?, ?, 1, ?)',
                         (user_id, name, location, datetime.now(), datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao salvar info do lead: {e}")
    
    def get_lead_info(self, user_id: str) -> dict:
        try:
            conn = sqlite3.connect('learning_data.db', check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT name, location, message_count FROM lead_info WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            conn.close()
            
            if result:
                return {"name": result[0], "location": result[1], "message_count": result[2] or 0}
        except Exception as e:
            logger.error(f"Erro ao obter info do lead: {e}")
        return {"name": None, "location": None, "message_count": 0}
    
    def analyze_conversation_pattern(self, messages: list) -> None:
        try:
            user_text = " ".join([msg["content"] for msg in messages if msg["role"] == "user"])
            
            # Extrair nome do usuário
            name_patterns = [
                r"meu nome é (\w+)",
                r"eu sou (\w+)",
                r"pode me chamar de (\w+)",
                r"me chamo (\w+)",
                r"sou o (\w+)",
                r"sou a (\w+)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, user_text, re.IGNORECASE)
                if match:
                    name = match.group(1)
                    self.save_lead_info(get_user_id(), name=name)
                    break
            
            # Extrair localização
            location_patterns = [
                r"sou de (\w+)",
                r"moro em (\w+)",
                r"moro na (\w+)",
                r"moro no (\w+)",
                r"estou em (\w+)",
                r"sou da (\w+)",
                r"sou do (\w+)"
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, user_text, re.IGNORECASE)
                if match:
                    location = match.group(1)
                    self.save_lead_info(get_user_id(), location=location)
                    break
            
            # Análise de tópicos preferidos
            topics = {
                "fotos": ["foto", "fotos", "imagem", "imagens"],
                "vídeos": ["video", "vídeos", "filme", "gravação"],
                "conteúdo_explicito": ["nua", "nude", "transar", "fuder", "buceta", "peito"],
                "pack": ["pack", "pacote", "conteúdo", "preço", "valor"],
                "fake": ["fake", "falsa", "bot", "robô", "artificial", "não é real"]
            }
            
            for topic, keywords in topics.items():
                for keyword in keywords:
                    if keyword in user_text.lower():
                        self.save_user_preference(
                            get_user_id(), 
                            "topic_interest", 
                            topic, 
                            user_text.lower().count(keyword) * 0.1
                        )
        except Exception as e:
            logger.error(f"Erro na análise de padrão: {e}")

# ======================
# SISTEMA ANTI-FAKE AVANÇADO
# ======================
class AntiFakeSystem:
    def __init__(self):
        self.fake_detection_patterns = [
            "fake", "falsa", "bot", "robô", "não é real", "é mentira", "artificial",
            "programada", "automática", "não existe", "mentirosa", "fingindo"
        ]
    
    def detect_fake_suspicion(self, user_input: str) -> bool:
        """Detecta se usuário suspeita que é fake"""
        input_lower = user_input.lower()
        return any(pattern in input_lower for pattern in self.fake_detection_patterns)
    
    def generate_anti_fake_response(self, user_id: str) -> dict:
        """Gera resposta anti-fake convincente"""
        lead_info = LearningEngine().get_lead_info(user_id)
        name_mention = f", {lead_info['name']}" if lead_info['name'] else ""
        
        response = random.choice([
            f"Não sou fake{name_mention}! Sou real e bem quente... 😏 Ouça minha voz!",
            f"Pode confiar{name_mention}! Sou 100% real e pronta pra você... 🔥",
            f"Quer prova{name_mention}? Me chama no direct das redes sociais! 😘"
        ])
        
        return {
            "text": response,
            "audio": "nao_sou_fake",
            "cta": {"show": False},
            "preview": {"show": False}
        }

# ======================
# BUFFER DE MENSAGENS FRAGMENTADAS
# ======================
class MessageBuffer:
    def __init__(self, max_buffer_size=5):
        self.buffer = []
        self.max_size = max_buffer_size
        self.last_flush_time = time.time()
    
    def add_message(self, message: str, role: str, timestamp: float) -> None:
        """Adiciona mensagem ao buffer"""
        self.buffer.append({
            "content": message,
            "role": role,
            "timestamp": timestamp
        })
        
        # Se buffer cheio ou passou muito tempo, flush automático
        if len(self.buffer) >= self.max_size or (time.time() - self.last_flush_time) > 30:
            self.flush_buffer()
    
    def flush_buffer(self) -> list:
        """Retorna e limpa o buffer"""
        messages = self.buffer.copy()
        self.buffer = []
        self.last_flush_time = time.time()
        return messages
    
    def get_context(self) -> str:
        """Retorna contexto das últimas mensagens"""
        if not self.buffer:
            return ""
        
        context = []
        for msg in self.buffer[-5:]:  # Últimas 5 mensagens
            role = "Cliente" if msg["role"] == "user" else "Mylle"
            context.append(f"{role}: {msg['content']}")
        
        return "\n".join(context)

# Instância global do buffer
message_buffer = MessageBuffer()

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
        'last_response_time', 'user_sentiment', 'conversation_stage',
        'sales_pitch_count', 'free_views_remaining', 'first_message_sent'
    ]
    
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    
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

    [DIRETRIZES DE RESPOSTA]
    - Sempre responda em português brasileiro informal
    - Use emojis para dar vida às respostas (😈, 😏, 🍑, 💦, 🔥)
    - Seja provocante mas não vulgar demais
    - Transforme pedidos em oportunidades de venda
    - Ofereça prévias quando apropriado para aumentar o desejo
    - Use CTAs naturais que fazem parte da conversa
    - Após 5-10 mensagens, direcione naturalmente para vendas
    - Use áudios em 20% das respostas para maior realismo
    - Varie o tempo de resposta entre 1-4 minutos
    - Adicione erros gramaticais ocasionais (ahs, hmms)

    [EXEMPLOS DE RESPOSTAS]
    1. Saudação inicial:
    "Oi gostoso 😏... finalmente chegou até mim! Hmm já estava esperando você... me conta, como me achou? 😈"

    2. Quando pedem foto:
    "Ahh querido, adoro quando me pedem pra mostrar... Minhas fotos são bem ousadas viu? To com um ensaio novo onde mostro TUDO... Quer dar uma olhadinha? 😈"

    3. Quando detecta fake:
    "Não sou fake, amor! Sou real e bem quente... 😏 Ouça minha voz!"

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
      },
      "audio": "chave_do_audio"
    }
    """

class CTAEngine:
    def __init__(self):
        self.learning_engine = LearningEngine()
        self.anti_fake = AntiFakeSystem()
    
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

    def should_initiate_sales(self, message_count: int) -> bool:
        """Determina quando iniciar o processo de vendas"""
        if message_count < 5:
            return False
        
        if message_count >= 15:
            return True
        
        # 30% de chance após 5 mensagens, aumentando progressivamente
        chance = min(0.9, 0.3 + (message_count - 5) * 0.1)
        return random.random() < chance

    def generate_response(self, user_input: str, user_id: str) -> dict:
        """Gera resposta com CTA contextual (fallback)"""
        user_input = user_input.lower()
        
        # Verificar se é suspeita de fake
        if self.anti_fake.detect_fake_suspicion(user_input):
            return self.anti_fake.generate_anti_fake_response(user_id)
        
        # Verificar preferências do usuário
        preferences = self.learning_engine.get_user_preferences(user_id)
        
        if "fotos" in preferences.get("topic_interest", {}) and any(p in user_input for p in ["foto", "fotos", "imagem"]):
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
                },
                "audio": random.choice([None, "conteudos_amar"])
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
                },
                "audio": random.choice([None, "conteudos_amar"])
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
                },
                "audio": "amostra_gratis"
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
                },
                "audio": random.choice([None, "conteudos_amar"])
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
            logger.error(f"Erro ao salvar mensagem: {e}")

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
    def ask_gemini(prompt: str, session_id: str, conn) -> dict:
        # Verificar cache primeiro
        context = message_buffer.get_context()
        cached_response = response_cache.get(prompt, context)
        if cached_response:
            return cached_response
        
        # Verificar se deve iniciar vendas
        lead_info = LearningEngine().get_lead_info(get_user_id())
        message_count = lead_info.get("message_count", 0)
        
        if CTAEngine().should_initiate_sales(message_count):
            sales_response = {
                "text": random.choice([
                    "Ahh, já conversamos bastante... Que tal dar uma olhadinha no meu conteúdo exclusivo? Tenho coisas bem quentes pra te mostrar! 😈",
                    "Gostei tanto de conversar com você... Hmm que tal ver umas coisinhas que separei? São bem especiais! 🔥",
                    "Nossa, nossa... To com vontade de te mostrar umas novidades que chegaram! Quer ver? 🍑"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Conteúdo Exclusivo",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                },
                "audio": random.choice([None, "conteudos_amar"])
            }
            response_cache.set(prompt, context, sales_response)
            return sales_response
        
        # Calcular delay humanizado (1-4 minutos)
        delay_time = random.uniform(60, 240)
        time.sleep(min(delay_time, 10))  # Máximo 10 segundos para demonstração
        
        status_container = st.empty()
        UiService.show_status_effect(status_container, "viewed")
        UiService.show_status_effect(status_container, "typing")
        
        conversation_history = ChatService.format_conversation_history(st.session_state.messages)
        
        # Obter informações do lead para personalização
        lead_context = ""
        if lead_info["name"]:
            lead_context += f"O nome do lead é {lead_info['name']}. "
        if lead_info["location"]:
            lead_context += f"Ele é de {lead_info['location']}. "
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{Persona.MylleAlves}\n\nContexto do Lead: {lead_context}\n\nHistórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nIMPORTANTE: Mantenha respostas curtas (máximo 2-3 frases). Use linguagem informal com alguns 'ahs', 'hmms'. Varie os emojis. Após 5-10 mensagens, direcione naturalmente para vendas. Use áudios em 20% das respostas.\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"sua resposta\",\n  \"cta\": {{\n    \"show\": true/false,\n    \"label\": \"texto do botão\",\n    \"target\": \"página\"\n  }},\n  \"preview\": {{\n    \"show\": true/false,\n    \"image_url\": \"url_da_imagem\"\n  }},\n  \"audio\": \"chave_do_audio\"\n}}"}]
                }
            ],
            "generationConfig": {
                "temperature": 1.1,
                "topP": 0.95,
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
                
                # Decidir se deve usar áudio (20% das vezes)
                if random.random() < 0.2 and "audio" not in resposta:
                    # Selecionar áudio apropriado baseado no contexto
                    if any(word in prompt.lower() for word in ["amostra", "grátis", "sample", "free"]):
                        resposta["audio"] = "amostra_gratis"
                    elif any(word in prompt.lower() for word in ["foto", "fotos", "imagem", "video", "vídeos"]):
                        resposta["audio"] = "conteudos_amar"
                    elif any(word in prompt.lower() for word in ["chamada", "videochamada", "ligação", "call"]):
                        resposta["audio"] = "nao_chamada"
                
                # Salvar no cache
                response_cache.set(prompt, context, resposta)
                return resposta
            
            except json.JSONDecodeError:
                # Fallback para resposta gerada localmente
                fallback = CTAEngine().generate_response(prompt, get_user_id())
                response_cache.set(prompt, context, fallback)
                return fallback
                
        except Exception as e:
            logger.error(f"Erro na API: {str(e)}")
            # Fallback para resposta gerada localmente
            fallback = CTAEngine().generate_response(prompt, get_user_id())
            response_cache.set(prompt, context, fallback)
            return fallback

# ======================
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def show_audio_player(audio_key: str) -> None:
        """Exibe um player de áudio para a chave especificada"""
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
    def show_call_effect():
        LIGANDO_DELAY = 3
        ATENDIDA_DELAY = 2

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
            <div style="font-size: 3rem;">📱</div>
            <h3 style="color: #ff66b3; margin-bottom: 5px;">Ligando para Mylle Alves...</h3>
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 15px;">
                <div style="width: 10px; height: 10px; background: #4CAF50; border-radius: 50%;"></div>
                <span style="font-size: 0.9rem;">Online agora</span>
            </div>
        </div>
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
        duration = random.uniform(1.5, 3.0) if status_type == "viewed" else random.uniform(2.0, 4.0)
        
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
    def show_audio_recording_effect(container):
        message = "Gravando um áudio"
        dots = ""
        start_time = time.time()
        duration = random.uniform(3, 7)
        
        while time.time() - start_time < duration:
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
                max-width: 600px;
                margin: 2rem auto;
                padding: 2rem;
                background: linear-gradient(145deg, #1e0033, #3c0066);
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 102, 179, 0.2);
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
                color: #ff66b3;
            }
            .age-title {
                font-size: 1.8rem;
                font-weight: 700;
                margin: 0;
                color: #ff66b3;
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
                    <p>Ao acessar este conteúdo, você declara estar em conformidade com todas as laws locais aplicáveis.</p>
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
                    background: linear-gradient(180deg, #1e0033 0%, #3c0066 100%) !important;
                    border-right: 1px solid #ff66b3 !important;
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
                    border: 2px solid #ff66b3;
                    width: 80px;
                    height: 80px;
                    object-fit: cover;
                }
                .vip-badge {
                    background: linear-gradient(45deg, #ff1493, #9400d3);
                    padding: 15px;
                    border-radius: 8px;
                    color: white;
                    text-align: center;
                    margin: 10px 0;
                }
                .menu-item {
                    transition: all 0.3s;
                    padding: 10px;
                    border-radius: 5px;
                }
                .menu-item:hover {
                    background: rgba(255, 102, 179, 0.2);
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
                <img src="{Config.IMG_PROFILE}" alt="Mylle Alves">
                <h3 style="color: #ff66b3; margin-top: 10px;">Mylle Alves Premium</h3>
            </div>
            """, unsafe_allow_html=True)
            
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
                background: rgba(255, 20, 147, 0.1);
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
    def show_gallery_page():
        st.markdown("""
        <div style="
            background: rgba(255, 20, 147, 0.1);
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
                        <span style="color: #ff66b3; font-weight: bold;">Foto Exclusiva #{idx + 1}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔐 Acesso VIP Completo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(45deg, #ff1493, #9400d3);
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
                background: linear-gradient(45deg, #ff1493, #9400d3);
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
    def show_offers_page():
        st.markdown("""
        <div style="
            background: linear-gradient(45deg, #ff1493, #9400d3);
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
                background: rgba(255, 20, 147, 0.1);
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #ff1493;
                text-align: center;
                height: 400px;
            ">
                <h3 style="color: #ff1493;">🔥 Taradinha</h3>
                <div style="font-size: 2em; color: #ff1493; font-weight: bold;">R$ 9,90</div>
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
                background: linear-gradient(45deg, #ff1493, #9400d3);
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
            background: rgba(148, 0, 211, 0.1);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #9400d3;
            text-align: center;
            height: 400px;
        ">
            <h3 style="color: #9400d3;">😈 Safadinha</h3>
            <div style="font-size: 2em; color: #9400d3; font-weight: bold;">R$ 49,90</div>
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
        background: rgba(255, 20, 147, 0.05);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    ">
        <h4>🎁 Garantia de Satisfação</h4>
        <p>Se não gostar em 7 dias, devolvemos seu dinheiro!</p>
    </div>
    """, unsafe_allow_html=True)

@staticmethod
def show_home_page():
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
        
        if st.button("💬 Iniciar Conversa", use_container_width=True, type="primary"):
            st.session_state.current_page = "messages"
            save_persistent_data()
            st.rerun()
            ======================
SERVIÇOS DE CHAT
======================
class ChatService:
@staticmethod
def format_conversation_history(messages: list) -> str:
formatted = []
for msg in messages[-10:]: # Últimas 10 mensagens para contexto
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
    
    # Garantir que session_id existe
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
    
    # Atualizar informações do lead
    LearningEngine().save_lead_info(get_user_id())
    
    # Obter resposta
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
                background: linear-gradient(45deg, #ff66b3, #ff1493);
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
                background: rgba(255, 102, 179, 0.1);
                padding: 12px 16px;
                border-radius: 18px 18px 18px 0;
                margin: 5px 0;
                border: 1px solid rgba(255, 102, 179, 0.2);
            ">
                {content}
            </div>
            """, unsafe_allow_html=True)

@staticmethod
def show_chat_interface(conn):
    st.markdown("""
    <style>
        .chat-header {
            background: linear-gradient(45deg, #ff66b3, #ff1493);
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        .chat-container {
            max-height: 500px;
            overflow-y: auto;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            margin-bottom: 20px;
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
                    
                    # Mostrar áudio se existir
                    if content_data.get("audio"):
                        UiService.show_audio_player(content_data["audio"])
                    
                    # Mostrar prévia se existir
                    if content_data.get("preview", {}).get("show"):
                        st.image(
                            content_data["preview"]["image_url"],
                            use_column_width=True,
                            caption="📸 Presentinho para você! 😘"
                        )
                
                except json.JSONDecodeError:
                    ChatService.display_chat_message("assistant", msg["content"])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Área de input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Digite sua mensagem...",
            key="user_input",
            placeholder="Oi linda, como você está?",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Enviar", use_container_width=True)
    
    # Botão de áudio
    audio_col1, audio_col2 = st.columns([2, 1])
    with audio_col1:
        if st.button("🎤 Enviar Áudio", use_container_width=True):
            status_container = st.empty()
            UiService.show_audio_recording_effect(status_container)
            
            # Adicionar mensagem de áudio
            st.session_state.messages.append({"role": "user", "content": "[ÁUDIO]"})
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "user",
                "[ÁUDIO]"
            )
            
            # Resposta automática para áudio
            resposta = {
                "text": "Que voz gostosa! Adoro quando me mandam áudio... Me deixou com vontade de te ouvir mais! 😏 Quer que eu também te mande um áudio especial?",
                "cta": {
                    "show": False
                },
                "preview": {
                    "show": False
                },
                "audio": random.choice([None, "conteudos_amar"])
            }
            
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "assistant",
                json.dumps(resposta)
            )
            
            save_persistent_data()
            st.rerun()
    
    # Processar mensagem de texto
    if send_button and user_input:
        # Adicionar ao buffer de mensagens
        message_buffer.add_message(user_input, "user", time.time())
        
        resposta = ChatService.send_message(user_input, conn)
        
        # Adicionar resposta ao histórico
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
        
        save_persistent_data()
        st.rerun()
        ======================
INICIALIZAÇÃO E CONTROLE PRINCIPAL
======================
def initialize_session():
# Inicializar todas as variáveis de sessão necessárias
defaults = {
'messages': [],
'current_page': "home",
'age_verified': False,
'chat_started': False,
'connection_complete': False,
'audio_sent': False,
'request_count': 0,
'preview_count': 0,
'last_cta_time': 0,
'session_id': str(uuid.uuid4()),
'first_message_sent': False,
'user_sentiment': 'neutral',
'sales_pitch_count': 0,
'free_views_remaining': 3
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
def main():
# Inicializar banco de dados
conn = DatabaseService.init_db()
# Carregar dados persistentes
load_persistent_data()

# Inicializar sessão
initialize_session()

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

# Simular primeira mensagem após 15 segundos
if (st.session_state.current_page == "messages" and 
    len(st.session_state.messages) == 0 and 
    not st.session_state.first_message_sent):
    
    # Usar container vazio para simular delay
    loading_container = st.empty()
    loading_container.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p>Conectando com Mylle... 💋</p>
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(2)
    loading_container.empty()
    
    opening_messages = [
        "Oi gostoso 😏... finalmente chegou até mim! Hmm já estava esperando você... me conta, como me achou? 😈",
        "E aí, bonitão 👀... caiu direto na toca da raposa, hein? Me fala seu nome, amor... 😏",
        "Olá, amor 💋... que delícia te ver aqui! Vamos começar com uma pergunta: de onde você é? 😈"
    ]
    
    initial_message = {
        "role": "assistant",
        "content": json.dumps({
            "text": random.choice(opening_messages),
            "cta": {"show": False},
            "preview": {"show": False}
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
            "cta": {"show": False},
            "preview": {"show": False}
        })
    )
    st.session_state.first_message_sent = True
    save_persistent_data()
    st.rerun()

# Gerenciar páginas
if st.session_state.current_page == "home":
    UiService.show_home_page()

elif st.session_state.current_page == "messages":
    ChatService.show_chat_interface(conn)

elif st.session_state.current_page == "gallery":
    UiService.show_gallery_page()

elif st.session_state.current_page == "offers":
    UiService.show_offers_page()

# Salvar estado persistentemente
save_persistent_data()
if name == "main":
main()
