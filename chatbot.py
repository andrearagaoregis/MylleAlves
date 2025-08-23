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
from datetime import datetime, timedelta
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any, Optional
import hashlib

# ======================
# CONFIGURAÇÃO DE LOGGING
# ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mylle_alves_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MylleAlvesBot')

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
    CHECKOUT_START = "https://checkout.exemplo.com/start"
    CHECKOUT_PREMIUM = "https://checkout.exemplo.com/premium"
    CHECKOUT_EXTREME = "https://checkout.exemplo.com/extreme"
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    IMG_PROFILE = "https://ibb.co/KpQHRFpZ"
    IMG_GALLERY = [
        "https://ibb.co/d0w2RDLb",
        "https://ibb.co/LD4SM7Pn",
        "https://ibb.co/2YYh55Hf"
    ]
    IMG_HOME_PREVIEWS = [
        "https://ibb.co/MDmGhjnX",
        "https://ibb.co/fGD0zvmY",
        "https://ibb.co/tSVc9Rz"
    ]
    LOGO_URL = "https://i.ibb.co/LX7x3tcB/Logo-Golden-Pepper-Letreiro-1.png"
    
    # Novos áudios da Mylle Alves
    AUDIO_LIBRARY = {
        "amostra_gratis": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Claro%20eu%20tenho%20amostra%20gr%C3%A1tis.mp3",
        "achou_amostras": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/O%20que%20achou%20das%20amostras.mp3",
        "nao_chamada": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Pq%20nao%20fa%C3%A7o%20mais%20chamada.mp3",
        "conteudos_amar": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/eu%20tenho%20uns%20conteudos%20aqui%20que%20vc%20vai%20amar.mp3",
        "esperando_resposta": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/vida%20to%20esperando%20voce%20me%20responder%20gatinho.mp3"
    }
    
    # Redes sociais
    SOCIAL_MEDIA = {
        "instagram": "https://instagram.com/myllealves",
        "facebook": "https://facebook.com/myllealves",
        "telegram": "https://t.me/myllealves",
        "tiktok": "https://tiktok.com/@myllealves"
    }
    
    # Tempos de resposta humanos (em segundos)
    RESPONSE_TIME_MIN = 60  # 1 minuto
    RESPONSE_TIME_MAX = 300  # 5 minutos
    
    # Configuração anti-fake
    MAX_REQUESTS_PER_MINUTE = 10
    MIN_TYPING_TIME = 2  # segundos
    MAX_TYPING_TIME = 8  # segundos

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
        # Tabela global_state existente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_state (
                user_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Nova tabela para preferências do usuário
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                interests TEXT,
                favorite_content TEXT,
                last_interaction TIMESTAMP,
                mood TEXT,
                purchase_history TEXT,
                FOREIGN KEY (user_id) REFERENCES global_state (user_id)
            )
        ''')
        
        # Nova tabela para analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_analytics (
                user_id TEXT,
                timestamp DATETIME,
                action TEXT,
                details TEXT,
                PRIMARY KEY (user_id, timestamp)
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
    
    def save_user_preferences(self, user_id, interests, favorite_content, mood):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (user_id, interests, favorite_content, last_interaction, mood)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, json.dumps(interests), json.dumps(favorite_content), datetime.now(), mood))
        self.conn.commit()
    
    def load_user_preferences(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT interests, favorite_content, mood FROM user_preferences WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {
                'interests': json.loads(result[0]) if result[0] else [],
                'favorite_content': json.loads(result[1]) if result[1] else [],
                'mood': result[2]
            }
        return None
    
    def log_user_action(self, user_id, action, details=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO user_analytics (user_id, timestamp, action, details)
            VALUES (?, ?, ?, ?)
        ''', (user_id, datetime.now(), action, json.dumps(details) if details else None))
        self.conn.commit()

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
        'last_cta_time', 'user_interests', 'user_mood',
        'last_message_time', 'typing_started', 'fragmented_messages',
        'current_fragment', 'audio_queue', 'conversation_topic'
    ]
    
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}
    
    if new_data != saved_data:
        db.save_state(user_id, new_data)

# ======================
# MODELOS DE DADOS
# ======================
class Persona:
    MYLLE_ALVES = """
    [PERFIL MYLLE ALVES]
    - Mulher sensual e confiante que adora flertar
    - Linguagem casual com toques de malícia
    - Respostas humanizadas com erros gramaticais ocasionais
    - Adora conversar e criar conexões genuínas
    
    [CARACTERÍSTICAS DA PERSONALIDADE]
    - Idade: 22 anos
    - Altura: 1.68m
    - Medidas: 85-60-90
    - Cidade: São Paulo
    - Signo: Leão
    - Hobbies: Dançar, malhar, fotografia
    
    [ESTILO DE CONVERSA]
    - Usa "ahs", "hmms", "né" ocasionalmente
    - Gosta de emojis (💋, 🔥, 😈, 🌶️)
    - Respostas curtas e diretas
    - Tom flertuoso e provocante
    
    [DIRETRIZES DE RESPOSTA]
    1. Analise o histórico da conversa para entender o contexto
    2. Use o nome do usuário quando possível para personalizar
    3. Mostre interesse genuíno pelo que o usuário diz
    4. Ofereça conteúdo quando o clima estiver apropriado
    5. Seja natural e evite respostas muito robóticas
    
    [EXEMPLOS DE RESPOSTAS]
    1. Quando perguntam sobre conteúdo:
    "Ahh eu tenho uns conteúdos bem quentes aqui que você vai adorar 😈 quer dar uma olhada?"
    
    2. Quando elogiam:
    "Hmm que delícia ouvir isso! Você me deixa toda feliz 💋"
    
    3. Quando pedem algo específico:
    "Nossa, você é bem direto né? Gosto disso 😏 mas preciso te conhecer melhor primeiro..."
    """

class CTAEngine:
    @staticmethod
    def should_show_cta(conversation_history: list, user_interests: list = None) -> bool:
        """Analisa o contexto para decidir quando mostrar CTA"""
        if len(conversation_history) < 2:
            return False

        # Não mostrar CTA se já teve um recentemente
        if 'last_cta_time' in st.session_state:
            elapsed = time.time() - st.session_state.last_cta_time
            if elapsed < 180:  # 3 minutos de intervalo entre CTAs
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
            "conteúdo", "conteudo", "conteúdos", "conteudos",
            "quanto custa", "comprar", "assinar", "pacote",
            "onlyfans", "privado", "exclusivo"
        ]
        
        direct_asks = [
            "mostra", "quero ver", "me manda", "como assinar",
            "como comprar", "como ter acesso", "onde vejo mais",
            "quanto custa", "tem promoção", "oferta"
        ]
        
        hot_count = sum(1 for word in hot_words if word in context)
        has_direct_ask = any(ask in context for ask in direct_asks)
        
        # Considerar interesses do usuário
        interest_bonus = 0
        if user_interests:
            for interest in user_interests:
                if any(keyword in context for keyword in interest.split()):
                    interest_bonus += 2
        
        return (hot_count >= 2) or has_direct_ask or (interest_bonus >= 3)

    @staticmethod
    def generate_cta_based_on_interests(user_interests: list) -> dict:
        """Gera CTA baseado nos interesses do usuário"""
        if not user_interests:
            return {
                "label": "Ver Conteúdo Exclusivo 🌶️",
                "target": "offers",
                "priority": "medium"
            }
        
        # Mapear interesses para tipos de conteúdo
        interest_mapping = {
            "fotos": {"label": "Ver Fotos Quentes 🔥", "target": "gallery", "priority": "high"},
            "vídeos": {"label": "Assistir Vídeos Exclusivos 🎥", "target": "offers", "priority": "high"},
            "video": {"label": "Assistir Vídeos Exclusivos 🎥", "target": "offers", "priority": "high"},
            "conversa": {"label": "Chat Privado Premium 💬", "target": "vip", "priority": "medium"},
            "personalizado": {"label": "Conteúdo Personalizado 💝", "target": "vip", "priority": "high"},
            "chamada": {"label": "Videochamada 📞", "target": "vip", "priority": "low"},
            "sexting": {"label": "Sexting Quente 🔞", "target": "vip", "priority": "medium"}
        }
        
        # Encontrar o melhor CTA baseado nos interesses
        best_cta = None
        highest_priority = "low"
        
        for interest in user_interests:
            for keyword, cta in interest_mapping.items():
                if keyword in interest.lower():
                    priority_order = {"high": 3, "medium": 2, "low": 1}
                    if priority_order[cta["priority"]] > priority_order.get(highest_priority, 0):
                        best_cta = cta
                        highest_priority = cta["priority"]
        
        return best_cta or {
            "label": "Descobrir Conteúdos Exclusivos 💋",
            "target": "offers",
            "priority": "medium"
        }

    @staticmethod
    def generate_response(user_input: str, user_interests: list = None) -> dict:
        """Gera resposta com CTA contextual"""
        user_input = user_input.lower()
        
        # Primeiro, tentar baseado em interesses específicos
        if user_interests:
            cta_based_on_interest = CTAEngine.generate_cta_based_on_interests(user_interests)
            if cta_based_on_interest["priority"] == "high":
                return {
                    "text": random.choice([
                        "hmm to com uns conteúdos bem do jeito que você curte 😈 quer ver?",
                        "nossa, lembrei que tenho algo especial que combina com seu estilo 💋",
                        "ahh você vai adorar o que preparei pensando em você 🌶️"
                    ]),
                    "cta": {
                        "show": True,
                        "label": cta_based_on_interest["label"],
                        "target": cta_based_on_interest["target"]
                    }
                }
        
        # Depois, tentar por palavras-chave gerais
        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda", "seios", "corpo"]):
            return {
                "text": random.choice([
                    "to com umas fotos bem gostosas aqui quer ver? 😈",
                    "fiz um ensaio novo que ficou incrível 🔥",
                    "minhas fotos tão uma delícia, vem ver 💋"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Fotos Exclusivas 📸",
                    "target": "gallery"
                }
            }
        
        elif any(v in user_input for v in ["video", "transar", "masturbar", "gozar", "fuder", "sexo"]):
            return {
                "text": random.choice([
                    "tenho uns vídeos bem quentes que você vai adorar 🎥",
                    "gravei algo especial esses dias, quer ver? 😏",
                    "meus vídeos tão fazendo sucesso, vem conferir 🔥"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Vídeos Quentes 🎬",
                    "target": "offers"
                }
            }
        
        elif any(c in user_input for c in ["conteúdo", "conteudo", "onlyfans", "privado", "exclusivo"]):
            return {
                "text": random.choice([
                    "ahh eu tenho uns conteúdos bem exclusivos aqui 🌶️",
                    "meu conteúdo privado é uma delícia, quer conhecer? 💋",
                    "to com novidades quentes no meu exclusivo 😈"
                ]),
                "cta": {
                    "show": True,
                    "label": "Ver Conteúdo Exclusivo 🔞",
                    "target": "offers"
                }
            }
        
        else:
            return {
                "text": random.choice([
                    "quero te mostrar coisas que vc nem imagina 😏",
                    "to com umas surpresas bem gostosas pra você 💋",
                    "vem ver o que preparei especialmente pra vc 🌶️"
                ]),
                "cta": {
                    "show": False
                }
            }

# ======================
# SISTEMA ANTI-FAKE
# ======================
class AntiFakeSystem:
    def __init__(self):
        self.request_timestamps = {}
        self.suspicious_patterns = [
            r"(.)\1{5,}",  # Caracteres repetidos
            r"[^\w\sà-úÀ-Ú]",  # Muitos caracteres especiais
            r"\b(http|www|\.com|\.br)\b",  # Links
            r".{100,}",  # Mensagens muito longas
        ]
    
    def check_user_behavior(self, user_id: str, message: str) -> bool:
        """Verifica se o comportamento do usuário parece humano"""
        current_time = time.time()
        
        # Registrar timestamp da requisição
        if user_id not in self.request_timestamps:
            self.request_timestamps[user_id] = []
        
        self.request_timestamps[user_id].append(current_time)
        
        # Manter apenas registros dos últimos 5 minutos
        self.request_timestamps[user_id] = [
            ts for ts in self.request_timestamps[user_id] 
            if current_time - ts < 300
        ]
        
        # Verificar limite de requisições
        if len(self.request_timestamps[user_id]) > Config.MAX_REQUESTS_PER_MINUTE:
            logger.warning(f"Usuário {user_id} excedeu limite de requisições")
            return False
        
        # Verificar padrões suspeitos na mensagem
        for pattern in self.suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                logger.warning(f"Padrão suspeito detectado na mensagem do usuário {user_id}")
                return False
        
        # Verificar tempo entre mensagens (deve ser pelo menos 2 segundos)
        if len(self.request_timestamps[user_id]) > 1:
            time_diff = self.request_timestamps[user_id][-1] - self.request_timestamps[user_id][-2]
            if time_diff < 2:  # Mensagens muito rápidas
                logger.warning(f"Usuário {user_id} enviando mensagens muito rapidamente")
                return False
        
        return True
    
    def calculate_typing_time(self, message_length: int) -> float:
        """Calcula tempo de digitação baseado no tamanho da mensagem"""
        base_time = Config.MIN_TYPING_TIME
        extra_time = min(Config.MAX_TYPING_TIME - base_time, message_length * 0.1)
        return base_time + extra_time + random.uniform(-1, 1)

# ======================
# SISTEMA DE FRAGMENTAÇÃO
# ======================
class MessageFragmenter:
    @staticmethod
    def fragment_message(message: str, max_fragment_length: int = 100) -> List[str]:
        """Divide uma mensagem longa em fragmentos menores"""
        if len(message) <= max_fragment_length:
            return [message]
        
        # Tentar dividir por pontuação primeiro
        fragments = []
        current_fragment = ""
        
        for char in message:
            current_fragment += char
            if len(current_fragment) >= max_fragment_length and char in ['.', '!', '?', ',', ';', ':']:
                fragments.append(current_fragment.strip())
                current_fragment = ""
        
        if current_fragment:
            fragments.append(current_fragment.strip())
        
        # Se ainda houver fragmentos muito longos, dividir por espaços
        final_fragments = []
        for fragment in fragments:
            if len(fragment) > max_fragment_length * 1.5:
                words = fragment.split()
                temp_fragment = ""
                for word in words:
                    if len(temp_fragment) + len(word) + 1 > max_fragment_length:
                        final_fragments.append(temp_fragment.strip())
                        temp_fragment = word
                    else:
                        temp_fragment += " " + word if temp_fragment else word
                if temp_fragment:
                    final_fragments.append(temp_fragment.strip())
            else:
                final_fragments.append(fragment)
        
        return final_fragments
    
    @staticmethod
    def add_human_touches(fragment: str) -> str:
        """Adiciona toques humanos à mensagem"""
        human_touches = [
            ("ahh", 0.1), ("hmm", 0.1), ("né", 0.05), 
            ("sabe", 0.05), ("tipo", 0.05), ("assim", 0.05)
        ]
        
        result = fragment
        for touch, probability in human_touches:
            if random.random() < probability:
                if random.random() < 0.5:
                    result = f"{touch} {result}"
                else:
                    result = f"{result} {touch}"
        
        # Adicionar emojis ocasionalmente
        emojis = ["💋", "🔥", "😈", "🌶️", "😏", "🤤"]
        if random.random() < 0.2:
            result = f"{result} {random.choice(emojis)}"
        
        # Adicionar erro gramatical ocasional
        if random.random() < 0.05:
            result = result.replace('ão', 'am').replace('ão', 'am')
            result = result.replace('mente', 'mente assim')
        
        return result

# ======================
# SISTEMA DE CACHE INTELIGENTE
# ======================
class IntelligentCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    @lru_cache(maxsize=100)
    def get_cached_response(self, user_input: str, context_hash: str) -> Optional[dict]:
        """Obtém resposta do cache se disponível"""
        cache_key = f"{user_input}_{context_hash}"
        
        if cache_key in self.cache:
            # Atualizar tempo de acesso
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]
        
        return None
    
    def cache_response(self, user_input: str, context_hash: str, response: dict):
        """Armazena resposta no cache"""
        if len(self.cache) >= self.max_size:
            # Remover item menos recentemente usado
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        cache_key = f"{user_input}_{context_hash}"
        self.cache[cache_key] = response
        self.access_times[cache_key] = time.time()
    
    def generate_context_hash(self, conversation_history: list) -> str:
        """Gera hash do contexto da conversa"""
        context_str = json.dumps(conversation_history[-3:])  # Últimas 3 mensagens
        return hashlib.md5(context_str.encode()).hexdigest()

# ======================
# ANÁLISE DE SENTIMENTO
# ======================
class SentimentAnalyzer:
    @staticmethod
    def analyze_mood(message: str) -> str:
        """Analisa o sentimento da mensagem do usuário"""
        message_lower = message.lower()
        
        positive_words = ["adoro", "amo", "gosto", "lindo", "perfeito", "maravilhoso", 
                         "incrível", "delicia", "gostoso", "querido", "amor"]
        negative_words = ["odeio", "ruim", "péssimo", "horrível", "nojo", "chato", 
                         "entediado", "cansado", "triste", "bravo", "raiva"]
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    @staticmethod
    def get_response_based_on_mood(mood: str, user_interests: list = None) -> str:
        """Gera resposta apropriada baseada no humor"""
        if mood == "positive":
            responses = [
                "Que bom que você tá animado! 💋",
                "Hmm adoro quando você fica assim 😏",
                "Nossa, você me deixa toda feliz! 🔥"
            ]
        elif mood == "negative":
            responses = [
                "Ahh não fica assim, vou te animar 💝",
                "O que aconteceu? Pode falar comigo 💬",
                "Vem cá, deixa eu te fazer sentir melhor 😘"
            ]
        else:
            responses = [
                "E aí, tudo bem? 💋",
                "Oi sumido, saudades! 😊",
                "Como você tá? ❤️"
            ]
        
        # Adicionar personalização baseada em interesses
        if user_interests and random.random() < 0.3:
            interest = random.choice(user_interests)
            responses = [f"{r} Lembrei que você curte {interest}..." for r in responses]
        
        return random.choice(responses)

# ======================
# SISTEMA DE ÁUDIO
# ======================
class AudioSystem:
    @staticmethod
    def should_send_audio(conversation_history: list, last_audio_time: float = 0) -> bool:
        """Decide se deve enviar áudio baseado no contexto"""
        current_time = time.time()
        
        # Não enviar áudio se já enviou um recentemente
        if current_time - last_audio_time < 300:  # 5 minutos
            return False
        
        # Verificar contexto da conversa
        context = " ".join([msg["content"] for msg in conversation_history[-3:]])
        context = context.lower()
        
        audio_triggers = [
            "audio", "voz", "ouvir", "falar", "chamar",
            "conversa", "telefone", "chamada", "som"
        ]
        
        emotional_triggers = [
            "triste", "feliz", "animado", "entediado", "sozinho",
            "saudade", "vontade", "desejo", "tesão"
        ]
        
        # Verificar se há triggers no contexto
        has_audio_trigger = any(trigger in context for trigger in audio_triggers)
        has_emotional_trigger = any(trigger in context for trigger in emotional_triggers)
        
        return has_audio_trigger or (has_emotional_trigger and random.random() < 0.5)
    
    @staticmethod
    def select_appropriate_audio(conversation_history: list) -> str:
        """Seleciona áudio apropriado baseado no contexto"""
        context = " ".join([msg["content"] for msg in conversation_history[-3:]])
        context = context.lower()
        
        # Mapear contexto para áudios disponíveis
        if any(word in context for word in ["amostra", "grátis", "experimentar", "conhecer"]):
            return "amostra_gratis"
        elif any(word in context for word in ["gostou", "achou", "opinião", "parecer"]):
            return "achou_amostras"
        elif any(word in context for word in ["chamada", "vídeo", "telefone", "voz"]):
            return "nao_chamada"
        elif any(word in context for word in ["conteúdo", "conteudo", "exclusivo", "privado"]):
            return "conteudos_amar"
        elif any(word in context for word in ["esperando", "responder", "demorou", "sumiu"]):
            return "esperando_resposta"
        
        # Se não encontrar match, escolher aleatoriamente
        return random.choice(list(Config.AUDIO_LIBRARY.keys()))
    
    @staticmethod
    def get_audio_player(audio_key: str) -> str:
        """Retorna HTML do player de áudio"""
        return f"""
        <div style="
            background: linear-gradient(45deg, #ff66b3, #ff1493);
            border-radius: 15px;
            padding: 12px;
            margin: 5px 0;
        ">
            <audio controls style="width:100%; height:40px;">
                <source src="{Config.AUDIO_LIBRARY[audio_key]}" type="audio/mp3">
            </audio>
        </div>
        """

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
                     content TEXT,
                     response_time FLOAT,
                     mood TEXT)''')
        conn.commit()
        return conn

    @staticmethod
    def save_message(conn, user_id, session_id, role, content, response_time=0, mood=None):
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO conversations (user_id, session_id, timestamp, role, content, response_time, mood)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, session_id, datetime.now(), role, content, response_time, mood))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar mensagem: {e}")

    @staticmethod
    def load_messages(conn, user_id, session_id, limit=50):
        c = conn.cursor()
        c.execute("""
            SELECT role, content, mood FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, session_id, limit))
        return [{"role": row[0], "content": row[1], "mood": row[2]} for row in c.fetchall()]

# ======================
# SERVIÇOS DE API
# ======================
class ApiService:
    def __init__(self):
        self.cache = IntelligentCache()
        self.anti_fake = AntiFakeSystem()
    
    def ask_gemini(self, prompt: str, session_id: str, conn, conversation_history: list, user_interests: list = None) -> dict:
        # Verificar comportamento do usuário
        user_id = get_user_id()
        if not self.anti_fake.check_user_behavior(user_id, prompt):
            return {
                "text": "Hmm acho que preciso de uma pausa, vamos conversar mais tarde? 💋",
                "cta": {"show": False}
            }
        
        # Verificar cache primeiro
        context_hash = self.cache.generate_context_hash(conversation_history)
        cached_response = self.cache.get_cached_response(prompt, context_hash)
        if cached_response:
            logger.info(f"Resposta recuperada do cache para: {prompt}")
            return cached_response
        
        # Calcular tempo de resposta humano
        typing_time = self.anti_fake.calculate_typing_time(len(prompt))
        time.sleep(min(typing_time, 5))  # Máximo de 5 segundos para digitação
        
        # Fazer chamada à API
        status_container = st.empty()
        UiService.show_status_effect(status_container, "typing")
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{Persona.MYLLE_ALVES}\n\nHistórico da Conversa:\n{conversation_history}\n\nÚltima mensagem do cliente: '{prompt}'\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"sua resposta\",\n  \"cta\": {{\n    \"show\": true/false,\n    \"label\": \"texto do botão\",\n    \"target\": \"página\"\n  }}\n}}"}]
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
                
                # Adicionar toques humanos à resposta
                if "text" in resposta:
                    resposta["text"] = MessageFragmenter.add_human_touches(resposta["text"])
                
                # Verificar se deve mostrar CTA
                if resposta.get("cta", {}).get("show"):
                    if not CTAEngine.should_show_cta(conversation_history, user_interests):
                        resposta["cta"]["show"] = False
                    else:
                        st.session_state.last_cta_time = time.time()
                
                # Cache a resposta
                self.cache.cache_response(prompt, context_hash, resposta)
                
                return resposta
            
            except json.JSONDecodeError:
                # Fallback para resposta humana
                return CTAEngine.generate_response(prompt, user_interests)
                
        except Exception as e:
            logger.error(f"Erro na API: {str(e)}")
            # Fallback para resposta offline
            return CTAEngine.generate_response(prompt, user_interests)

# ======================
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def show_status_effect(container, status_type, duration=None):
        status_messages = {
            "viewed": "Visualizado",
            "typing": "Digitando...",
            "recording": "Gravando áudio...",
            "thinking": "Pensando..."
        }
        
        message = status_messages[status_type]
        dots = ""
        start_time = time.time()
        
        if duration is None:
            duration = random.uniform(2.0, 4.0)
        
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            
            if status_type in ["typing", "thinking", "recording"]:
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
                    <p>Ao acessar este conteúdo, você declara estar em conformidade com todas as leis locais aplicáveis.</p>
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
                .social-buttons {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin: 15px 0;
                }
                .social-button {
                    padding: 8px;
                    border-radius: 8px;
                    text-align: center;
                    color: white;
                    text-decoration: none;
                    font-size: 0.8rem;
                    transition: all 0.3s;
                }
                .social-button:hover {
                    transform: translateY(-2px);
                    opacity: 0.9;
                }
                .instagram { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
                .facebook { background: #1877F2; }
                .telegram { background: #0088cc; }
                .tiktok { background: #000000; }
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
                <img src="{Config.LOGO_URL}" class="sidebar-logo" alt="Mylle Alves Logo">
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="sidebar-header">
                <img src="{profile_img}" alt="Mylle Alves">
                <h3 style="color: #ff66b3; margin-top: 10px;">Mylle Alves</h3>
                <p style="color: #4CAF50; margin: 0; font-size: 0.9em;">● Online agora</p>
            </div>
            """.format(profile_img=Config.IMG_PROFILE), unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📱 Redes Sociais")
            
            st.markdown("""
            <div class="social-buttons">
                <a href="{instagram}" target="_blank" class="social-button instagram">Instagram</a>
                <a href="{facebook}" target="_blank" class="social-button facebook">Facebook</a>
                <a href="{telegram}" target="_blank" class="social-button telegram">Telegram</a>
                <a href="{tiktok}" target="_blank" class="social-button tiktok">TikTok</a>
            </div>
            """.format(
                instagram=Config.SOCIAL_MEDIA["instagram"],
                facebook=Config.SOCIAL_MEDIA["facebook"],
                telegram=Config.SOCIAL_MEDIA["telegram"],
                tiktok=Config.SOCIAL_MEDIA["tiktok"]
            ), unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 🎯 Menu Principal")
            
            menu_options = {
                "Início": "home",
                "Galeria": "gallery",
                "Mensagens": "messages",
                "Conteúdos": "offers"
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
                <p>© 2024 Mylle Alves</p>
                <p>Conteúdo para maiores de 18 anos</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def show_gallery_page(conn):
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
                    color: #ff66b3;
                    margin-top: -10px;
                ">
                    Conteúdo bloqueado 🔒
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center;">
            <h4>Desbloqueie acesso completo</h4>
            <p>Adquira um pacote para ver todos os conteúdos</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Ver Pacotes Disponíveis", 
                    key="vip_button_gallery", 
                    use_container_width=True,
                    type="primary"):
            st.session_state.current_page = "offers"
            st.rerun()
        
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
            if st.button("Conteúdos", key="shortcut_offers",
                       help="Ver ofertas especiais",
                       use_container_width=True):
                st.session_state.current_page = "offers"
                save_persistent_data()
                st.rerun()
        with cols[3]:
            if st.button("Voltar", key="shortcut_back",
                       help="Voltar ao chat",
                       use_container_width=True):
                st.session_state.current_page = "chat"
                save_persistent_data()
                st.rerun()

        st.markdown("""
        <style>
            div[data-testid="stHorizontalBlock"] > div > div > button {
                color: white !important;
                border: 1px solid #ff66b3 !important;
                background: rgba(255, 102, 179, 0.15) !important;
                transition: all 0.3s !important;
                font-size: 0.8rem !important;
            }
            div[data-testid="stHorizontalBlock"] > div > div > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 2px 8px rgba(255, 102, 179, 0.3) !important;
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
    def enhanced_chat_ui(conn, api_service):
        st.markdown("""
        <style>
            .chat-header {
                background: linear-gradient(90deg, #ff66b3, #ff1493);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .stAudio {
                border-radius: 20px !important;
                background: rgba(255, 102, 179, 0.1) !important;
                padding: 10px !important;
                margin: 10px 0 !important;
            }
            audio::-webkit-media-controls-panel {
                background: linear-gradient(45deg, #ff66b3, #ff1493) !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        UiService.chat_shortcuts()
        
        st.markdown(f"""
        <div class="chat-header">
            <h2 style="margin:0; font-size:1.5em; display:inline-block;">💬 Chat com Mylle Alves</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown(f"""
        <div style="
            background: rgba(255, 20, 147, 0.1);
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
        
        ChatService.process_user_input(conn, api_service)
        save_persistent_data()
        
        st.markdown("""
        <div style="
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            font-size: 0.8em;
            color: #888;
        ">
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
                <p style="color: #4CAF50;">● Online agora</p>
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
                <p>♌ Leão</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("""
            <div style="text-align: center;">
                <h4>📱 Me siga nas redes</h4>
                <div style="display: flex; justify-content: center; gap: 10px; margin: 10px 0;">
                    <a href="{instagram}" target="_blank" style="color: #ff66b3; font-size: 1.5em;">📷</a>
                    <a href="{facebook}" target="_blank" style="color: #ff66b3; font-size: 1.5em;">📘</a>
                    <a href="{telegram}" target="_blank" style="color: #ff66b3; font-size: 1.5em;">✈️</a>
                    <a href="{tiktok}" target="_blank" style="color: #ff66b3; font-size: 1.5em;">🎵</a>
                </div>
            </div>
            """.format(
                instagram=Config.SOCIAL_MEDIA["instagram"],
                facebook=Config.SOCIAL_MEDIA["facebook"],
                telegram=Config.SOCIAL_MEDIA["telegram"],
                tiktok=Config.SOCIAL_MEDIA["tiktok"]
            ), unsafe_allow_html=True)
        
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
                        st.markdown("""<div style="text-align:center; color: #ff66b3; margin-top: -15px;">Conteúdo Exclusivo 🔒</div>""", unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.button("💬 Iniciar Conversa com Mylle", 
                        use_container_width=True,
                        type="primary"):
                st.session_state.current_page = "chat"
                save_persistent_data()
                st.rerun()

    @staticmethod
    def show_offers_page():
        st.markdown("""
        <style>
            .package-container {
                display: flex;
                justify-content: space-between;
                margin: 30px 0;
                gap: 20px;
            }
            .package-box {
                flex: 1;
                background: rgba(30, 0, 51, 0.3);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid;
                transition: all 0.3s;
                min-height: 400px;
                position: relative;
                overflow: hidden;
            }
            .package-box:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(255, 102, 179, 0.3);
            }
            .package-start {
                border-color: #ff66b3;
            }
            .package-premium {
                border-color: #9400d3;
            }
            .package-extreme {
                border-color: #ff0066;
            }
            .package-header {
                text-align: center;
                padding-bottom: 15px;
                margin-bottom: 15px;
                border-bottom: 1px solid rgba(255, 102, 179, 0.3);
            }
            .package-price {
                font-size: 1.8em;
                font-weight: bold;
                margin: 10px 0;
            }
            .package-benefits {
                list-style-type: none;
                padding: 0;
            }
            .package-benefits li {
                padding: 8px 0;
                position: relative;
                padding-left: 25px;
            }
            .package-benefits li:before {
                content: "✓";
                color: #ff66b3;
                position: absolute;
                left: 0;
                font-weight: bold;
            }
            .package-badge {
                position: absolute;
                top: 15px;
                right: -30px;
                background: #ff0066;
                color: white;
                padding: 5px 30px;
                transform: rotate(45deg);
                font-size: 0.8em;
                font-weight: bold;
                width: 100px;
                text-align: center;
            }
            .countdown-container {
                background: linear-gradient(45deg, #ff0066, #ff66b3);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 40px 0;
                box-shadow: 0 4px 15px rgba(255, 0, 102, 0.3);
                text-align: center;
            }
            .offer-card {
                border: 1px solid #ff66b3;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                background: rgba(30, 0, 51, 0.3);
            }
            .offer-highlight {
                background: linear-gradient(45deg, #ff0066, #ff66b3);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #ff66b3; border-bottom: 2px solid #ff66b3; display: inline-block; padding-bottom: 5px;">📦 PACOTES EXCLUSIVOS</h2>
            <p style="color: #aaa; margin-top: 10px;">Escolha o que melhor combina com seus desejos...</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="package-container">', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="package-box package-start">
            <div class="package-header">
                <h3 style="color: #ff66b3;">START</h3>
                <div class="package-price" style="color: #ff66b3;">R$ 49,90</div>
                <small>para iniciantes</small>
            </div>
            <ul class="package-benefits">
                <li>10 fotos Inéditas</li>
                <li>3 vídeo Intimos</li>
                <li>Fotos Exclusivas</li>
                <li>Videos Intimos </li>
                <li>Fotos Buceta</li>
            </ul>
            <div style="position: absolute; bottom: 20px; width: calc(100% - 40px);">
                <a href="{checkout_start}" target="_blank" rel="noopener noreferrer" style="
                    display: block;
                    background: linear-gradient(45deg, #ff66b3, #ff1493);
                    color: white;
                    text-align: center;
                    padding: 10px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    transition: all 0.3s;
                " onmouseover="this.style.transform='scale(1.05)'" 
                onmouseout="this.style.transform='scale(1)'"
                onclick="this.innerHTML='REDIRECIONANDO ⌛'; this.style.opacity='0.7'">
                    QUERO ESTE PACOTE ➔
                </a>
            </div>
        </div>
        """.format(checkout_start=Config.CHECKOUT_START), unsafe_allow_html=True)

        st.markdown("""
        <div class="package-box package-premium">
            <div class="package-badge">POPULAR</div>
            <div class="package-header">
                <h3 style="color: #9400d3;">PREMIUM</h3>
                <div class="package-price" style="color: #9400d3;">R$ 99,90</div>
                <small>experiência completa</small>
            </div>
            <ul class="package-benefits">
                <li>20 fotos exclusivas</li>
                <li>5 vídeos premium</li>
                <li>Fotos Peito</li>
                <li>Fotos Bunda</li>
                <li>Fotos Buceta</li>
                <li>Fotos Exclusivas e Videos Exclusivos</li>
                <li>Videos Masturbando</li>
            </ul>
            <div style="position: absolute; bottom: 20px; width: calc(100% - 40px);">
                <a href="{checkout_premium}" target="_blank" rel="noopener noreferrer" style="
                    display: block;
                    background: linear-gradient(45deg, #9400d3, #ff1493);
                    color: white;
                    text-align: center;
                    padding: 10px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    transition: all 0.3s;
                " onmouseover="this.style.transform='scale(1.05)'" 
                onmouseout="this.style.transform='scale(1)'"
                onclick="this.innerHTML='REDIRECIONANDO ⌛'; this.style.opacity='0.7'">
                    QUERO ESTE PACOTE ➔
                </a>
            </div>
        </div>
        """.format(checkout_premium=Config.CHECKOUT_PREMIUM), unsafe_allow_html=True)

        st.markdown("""
        <div class="package-box package-extreme">
            <div class="package-header">
                <h3 style="color: #ff0066;">EXTREME</h3>
                <div class="package-price" style="color: #ff0066;">R$ 199,90</div>
                <small>para verdadeiros fãs</small>
            </div>
            <ul class="package-benefits">
                <li>30 fotos ultra-exclusivas</li>
                <li>10 Videos Exclusivos</li>
                <li>Fotos Peito</li>
                <li>Fotos Bunda</li>
                <li>Fotos Buceta</li>
                <li>Fotos Exclusivas</li>
                <li>Videos Masturbando</li>
                <li>Videos Transando</li>
                <li>Acesso a conteúdos futuros</li>
            </ul>
            <div style="position: absolute; bottom: 20px; width: calc(100% - 40px);">
                <a href="{checkout_extreme}" target="_blank" rel="noopener noreferrer" style="
                    display: block;
                    background: linear-gradient(45deg, #ff0066, #9400d3);
                    color: white;
                    text-align: center;
                    padding: 10px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    transition: all 0.3s;
                " onmouseover="this.style.transform='scale(1.05)'" 
                onmouseout="this.style.transform='scale(1)'"
                onclick="this.innerHTML='REDIRECIONANDO ⌛'; this.style.opacity='0.7'">
                    QUERO ESTE PACOTE ➔
                </a>
            </div>
        </div>
        """.format(checkout_extreme=Config.CHECKOUT_EXTREME), unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="countdown-container">
            <h3 style="margin:0;">⏰ OFERTA RELÂMPAGO</h3>
            <div id="countdown" style="font-size: 1.5em; font-weight: bold;">23:59:59</div>
            <p style="margin:5px 0 0;">Termina em breve!</p>
        </div>
        """, unsafe_allow_html=True)

        st.components.v1.html("""
        <script>
        function updateCountdown() {
            const countdownElement = parent.document.getElementById('countdown');
            if (!countdownElement) return;
            
            let time = countdownElement.textContent.split(':');
            let hours = parseInt(time[0]);
            let minutes = parseInt(time[1]);
            let seconds = parseInt(time[2]);
            
            seconds--;
            if (seconds < 0) { seconds = 59; minutes--; }
            if (minutes < 0) { minutes = 59; hours--; }
            if (hours < 0) { hours = 23; }
            
            countdownElement.textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            setTimeout(updateCountdown, 1000);
        }
        
        setTimeout(updateCountdown, 1000);
        </script>
        """, height=0)

        plans = [
            {
                "name": "1 Mês",
                "price": "R$ 29,90",
                "original": "R$ 49,90",
                "benefits": ["Acesso total", "Conteúdo novo diário", "Chat privado"],
                "tag": "COMUM",
                "link": Config.CHECKOUT_VIP_1MES + "?plan=1mes"
            },
            {
                "name": "3 Meses",
                "price": "R$ 69,90",
                "original": "R$ 149,70",
                "benefits": ["25% de desconto", "Bônus: 1 vídeo exclusivo", "Prioridade no chat"],
                "tag": "MAIS POPULAR",
                "link": Config.CHECKOUT_VIP_3MESES + "?plan=3meses"
            },
            {
                "name": "1 Ano",
                "price": "R$ 199,90",
                "original": "R$ 598,80",
                "benefits": ["66% de desconto", "Presente surpresa mensal", "Acesso a conteúdos raros"],
                "tag": "MELHOR CUSTO-BENEFÍCIO",
                "link": Config.CHECKOUT_VIP_1ANO + "?plan=1ano"
            }
        ]

        for plan in plans:
            with st.container():
                st.markdown(f"""
                <div class="offer-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>{plan['name']}</h3>
                        {f'<span class="offer-highlight">{plan["tag"]}</span>' if plan["tag"] else ''}
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="font-size: 1.8em; color: #ff66b3; font-weight: bold;">{plan['price']}</span>
                        <span style="text-decoration: line-through; color: #888; margin-left: 10px;">{plan['original']}</span>
                    </div>
                    <ul style="padding-left: 20px;">
                        {''.join([f'<li style="margin-bottom: 5px;">{benefit}</li>' for benefit in plan['benefits']])}
                    </ul>
                    <div style="text-align: center; margin-top: 15px;">
                        <a href="{plan['link']}" style="
                            background: linear-gradient(45deg, #ff1493, #9400d3);
                            color: white;
                            padding: 10px 20px;
                            border-radius: 30px;
                            text-decoration: none;
                            display: inline-block;
                            font-weight: bold;
                        ">
                            Assinar {plan['name']}
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if st.button("Voltar ao chat", key="back_from_offers"):
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
        
        # Novos estados para o sistema melhorado
        defaults = {
            'age_verified': False,
            'connection_complete': False,
            'chat_started': False,
            'audio_sent': False,
            'current_page': 'home',
            'show_vip_offer': False,
            'last_cta_time': 0,
            'user_interests': [],
            'user_mood': 'neutral',
            'last_message_time': 0,
            'typing_started': False,
            'fragmented_messages': [],
            'current_fragment': 0,
            'audio_queue': [],
            'conversation_topic': None
        }
        
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default
        
        # Carregar preferências do usuário se existirem
        db = PersistentState()
        preferences = db.load_user_preferences(get_user_id())
        if preferences:
            st.session_state.user_interests = preferences.get('interests', [])
            st.session_state.user_mood = preferences.get('mood', 'neutral')

    @staticmethod
    def format_conversation_history(messages, max_messages=10):
        formatted = []
        
        for msg in messages[-max_messages:]:
            role = "Cliente" if msg["role"] == "user" else "Mylle"
            content = msg["content"]
            if content == "[ÁUDIO]":
                content = "[Enviou um áudio sensual]"
            elif content.startswith('{"text"'):
                try:
                    content = json.loads(content).get("text", content)
                except:
                    pass
            
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    @staticmethod
    def display_chat_history():
        chat_container = st.container()
        with chat_container:
            for idx, msg in enumerate(st.session_state.messages[-12:]):
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="🧑"):
                        st.markdown(f"""
                        <div style="
                            background: rgba(0, 0, 0, 0.1);
                            padding: 12px;
                            border-radius: 18px 18px 0 18px;
                            margin: 5px 0;
                        ">
                            {msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                elif msg["content"] == "[ÁUDIO]":
                    with st.chat_message("assistant", avatar="💋"):
                        # Encontrar qual áudio foi enviado
                        audio_key = st.session_state.audio_queue[-1] if st.session_state.audio_queue else "conteudos_amar"
                        st.markdown(AudioSystem.get_audio_player(audio_key), unsafe_allow_html=True)
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
                                
                                # Mostrar botão apenas na última mensagem
                                if content_data.get("cta", {}).get("show") and idx == len(st.session_state.messages[-12:]) - 1:
                                    if st.button(
                                        content_data.get("cta", {}).get("label", "Ver Ofertas"),
                                        key=f"cta_button_{hash(msg['content'])}",
                                        use_container_width=True
                                    ):
                                        st.session_state.current_page = content_data.get("cta", {}).get("target", "offers")
                                        save_persistent_data()
                                        st.rerun()
                        else:
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
                    except json.JSONDecodeError:
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
    def validate_input(user_input):
        cleaned_input = re.sub(r'<[^>]*>', '', user_input)
        return cleaned_input[:500]

    @staticmethod
    def process_user_input(conn, api_service):
        ChatService.display_chat_history()
        
        # Sistema de áudio - verificar se deve enviar áudio
        current_time = time.time()
        if (AudioSystem.should_send_audio(st.session_state.messages, st.session_state.last_message_time) and 
            not st.session_state.audio_sent):
            
            status_container = st.empty()
            UiService.show_status_effect(status_container, "recording", 3)
            
            audio_key = AudioSystem.select_appropriate_audio(st.session_state.messages)
            st.session_state.audio_queue.append(audio_key)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": "[ÁUDIO]"
            })
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "assistant",
                "[ÁUDIO]"
            )
            st.session_state.audio_sent = True
            st.session_state.last_message_time = current_time
            save_persistent_data()
            st.rerun()
        
        user_input = st.chat_input("Escreva sua mensagem aqui", key="chat_input")
        
        if user_input:
            cleaned_input = ChatService.validate_input(user_input)
            
            # Verificar limite de mensagens
            if st.session_state.request_count >= Config.MAX_REQUESTS_PER_SESSION:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Hmm vou ficar ocupada agora, me manda mensagem depois? 💋"
                })
                DatabaseService.save_message(
                    conn,
                    get_user_id(),
                    st.session_state.session_id,
                    "assistant",
                    "Estou ficando cansada, amor... Que tal continuarmos mais tarde? 😘"
                )
                save_persistent_data()
                st.rerun()
                return
            
            # Analisar sentimento da mensagem
            mood = SentimentAnalyzer.analyze_mood(cleaned_input)
            st.session_state.user_mood = mood
            
            # Atualizar interesses do usuário baseado na mensagem
            ChatService.update_user_interests(cleaned_input)
            
            # Salvar mensagem do usuário
            st.session_state.messages.append({
                "role": "user",
                "content": cleaned_input
            })
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "user",
                cleaned_input,
                mood=mood
            )
            
            st.session_state.request_count += 1
            st.session_state.last_message_time = current_time
            
            # Mostrar mensagem do usuário
            with st.chat_message("user", avatar="🧑"):
                st.markdown(f"""
                <div style="
                    background: rgba(0, 0, 0, 0.1);
                    padding: 12px;
                    border-radius: 18px 18px 0 18px;
                    margin: 5px 0;
                ">
                    {cleaned_input}
                </div>
                """, unsafe_allow_html=True)
            
            # Simular tempo de resposta humano
            response_delay = random.randint(Config.RESPONSE_TIME_MIN, Config.RESPONSE_TIME_MAX)
            time.sleep(min(response_delay, 10))  # Máximo de 10 segundos para demonstração
            
            # Mostrar status de "digitando"
            typing_container = st.empty()
            UiService.show_status_effect(typing_container, "typing")
            
            # Gerar resposta
            with st.chat_message("assistant", avatar="💋"):
                resposta = api_service.ask_gemini(
                    cleaned_input, 
                    st.session_state.session_id, 
                    conn,
                    st.session_state.messages,
                    st.session_state.user_interests
                )
                
                if isinstance(resposta, str):
                    resposta = {"text": resposta, "cta": {"show": False}}
                elif "text" not in resposta:
                    resposta = {"text": str(resposta), "cta": {"show": False}}
                
                # Fragmentar mensagem longa
                fragments = MessageFragmenter.fragment_message(resposta["text"])
                
                for i, fragment in enumerate(fragments):
                    if i > 0:
                        # Pequena pausa entre fragmentos
                        time.sleep(random.uniform(0.5, 1.5))
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(45deg, #ff66b3, #ff1493);
                        color: white;
                        padding: 12px;
                        border-radius: 18px 18px 18px 0;
                        margin: 5px 0;
                    ">
                        {fragment}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Mostrar CTA se aplicável
                if resposta.get("cta", {}).get("show"):
                    if st.button(
                        resposta["cta"].get("label", "Ver Conteúdos 🌶️"),
                        key=f"chat_button_{time.time()}",
                        use_container_width=True
                    ):
                        st.session_state.current_page = resposta["cta"].get("target", "offers")
                        save_persistent_data()
                        st.rerun()
            
            # Salvar resposta da assistente
            st.session_state.messages.append({
                "role": "assistant",
                "content": json.dumps(resposta)
            })
            DatabaseService.save_message(
                conn,
                get_user_id(),
                st.session_state.session_id,
                "assistant",
                json.dumps(resposta),
                response_time=response_delay,
                mood=st.session_state.user_mood
            )
            
            save_persistent_data()
            
            st.markdown("""
            <script>
                window.scrollTo(0, document.body.scrollHeight);
            </script>
            """, unsafe_allow_html=True)

    @staticmethod
    def update_user_interests(message: str):
        """Atualiza interesses do usuário baseado na mensagem"""
        interest_keywords = {
            "fotos": ["foto", "fotos", "imagem", "imagens", "ensaio", "fotografia"],
            "vídeos": ["vídeo", "videos", "film", "grav", "assistir", "youtube"],
            "conversa": ["conversar", "falar", "dialogo", "bate-papo", "papinho"],
            "personalizado": ["personaliz", "exclusiv", "único", "especial", "única"],
            "chamada": ["chamada", "videochamada", "ligação", "zoom", "skype"],
            "sexting": ["sexting", "provocar", "tesão", "excitar", "sensual"]
        }
        
        message_lower = message.lower()
        new_interests = []
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if interest not in st.session_state.user_interests:
                    new_interests.append(interest)
        
        if new_interests:
            st.session_state.user_interests.extend(new_interests)
            # Salvar preferências no banco de dados
            db = PersistentState()
            db.save_user_preferences(
                get_user_id(),
                st.session_state.user_interests,
                [],  # favorite_content vazio por enquanto
                st.session_state.user_mood
            )
            
            # Log da ação
            db.log_user_action(
                get_user_id(),
                "interest_update",
                {"new_interests": new_interests, "total_interests": st.session_state.user_interests}
            )

# ======================
# APLICAÇÃO PRINCIPAL
# ======================
def main():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e0033 0%, #3c0066 100%) !important;
            border-right: 1px solid #ff66b3 !important;
        }
        .stButton button {
            background: rgba(255, 20, 147, 0.2) !important;
            color: white !important;
            border: 1px solid #ff66b3 !important;
            transition: all 0.3s !important;
        }
        .stButton button:hover {
            background: rgba(255, 20, 147, 0.4) !important;
            transform: translateY(-2px) !important;
        }
        [data-testid="stChatInput"] {
            background: rgba(255, 102, 179, 0.1) !important;
            border: 1px solid #ff66b3 !important;
        }
        div.stButton > button:first-child {
            background: linear-gradient(45deg, #ff1493, #9400d3) !important;
            color: white !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 10px 24px !important;
            font-weight: bold !important;
            transition: all 0.3s !important;
            box-shadow: 0 4px 8px rgba(255, 20, 147, 0.3) !important;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(255, 20, 147, 0.4) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = DatabaseService.init_db()
    
    if 'api_service' not in st.session_state:
        st.session_state.api_service = ApiService()
    
    conn = st.session_state.db_conn
    api_service = st.session_state.api_service
    
    ChatService.initialize_session(conn)
    
    if not st.session_state.age_verified:
        UiService.age_verification()
        st.stop()
    
    UiService.setup_sidebar()
    
    if not st.session_state.connection_complete:
        # Simular início de conversa mais natural
        time.sleep(2)
        st.session_state.connection_complete = True
        save_persistent_data()
        st.rerun()
    
    if not st.session_state.chat_started:
        NewPages.show_home_page(conn)
        st.stop()
    
    if st.session_state.current_page == "home":
        NewPages.show_home_page(conn)
    elif st.session_state.current_page == "gallery":
        UiService.show_gallery_page(conn)
    elif st.session_state.current_page == "offers":
        NewPages.show_offers_page()
    elif st.session_state.current_page == "vip":
        st.session_state.show_vip_offer = True
        save_persistent_data()
        st.rerun()
    elif st.session_state.get("show_vip_offer", False):
        st.warning("Página VIP em desenvolvimento")
        if st.button("Voltar ao chat"):
            st.session_state.show_vip_offer = False
            save_persistent_data()
            st.rerun()
    else:
        UiService.enhanced_chat_ui(conn, api_service)
    
    save_persistent_data()

if __name__ == "__main__":
    main()

