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
from datetime import datetime, timedelta
from pathlib import Path
from functools import lru_cache
import logging
from typing import Dict, List, Any, Optional
import numpy as np

# ======================
# CONFIGURAÇÃO DE LOGGING
# ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    VIP_LINK = "https://exemplo.com/vip"
    CHECKOUT_TARADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACC74F-01EC-4770-B182-B5775AF62A1D"
    CHECKOUT_MOLHADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD1E6-0EFD-4E3E-9F9D-BA0C1A2D7E7A"
    CHECKOUT_SAFADINHA = "https://app.pushinpay.com.br/#/service/pay/9FACD395-EE65-458E-9B7E-FED750CC9CA9"
    MAX_REQUESTS_PER_SESSION = 30
    REQUEST_TIMEOUT = 30
    AUDIO_FILES = {
        "amostra_gratis": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Claro%20eu%20tenho%20amostra%20gr%C3%A1tis.mp3",
        "imaginacao_rosinha": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Imagina%20s%C3%B3%20ela%20bem%20rosinha%20(putaria).mp3",
        "achou_amostras": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/O%20que%20achou%20das%20amostras.mp3",
        "oi_amor": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Oi%20meu%20amor%20tudo%20bem.mp3",
        "chamada_video": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Pq%20nao%20fa%C3%A7o%20mais%20chamada.mp3",
        "packs": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/Pra%20me%20ver%20nua%20tem%20que%20comprar%20os%20packs.mp3",
        "conteudos_amar": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/eu%20tenho%20uns%20conteudos%20aqui%20que%20vc%20vai%20amar.mp3",
        "nao_fake": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/nao%20sou%20fake%20nao..mp3",
        "esperando_resposta": "https://github.com/andrearagaoregis/MylleAlves/raw/refs/heads/main/assets/vida%20to%20esperando%20voce%20me%20responder%20gatinho.mp3"
    }
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
    # Configurações de humanização
    MIN_RESPONSE_DELAY = 60  # 1 minuto em segundos
    MAX_RESPONSE_DELAY = 300  # 5 minutos em segundos
    TYPING_SPEED_VARIATION = 0.3  # Variação de 30% na velocidade de digitação
    GRAMMATICAL_ERROR_RATE = 0.15  # 15% de chance de erro gramatical
    FRAGMENTATION_PROBABILITY = 0.25  # 25% de chance de fragmentar mensagem

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
        # Tabela para preferências do usuário
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                preferences TEXT NOT NULL,
                sentiment TEXT,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES global_state (user_id)
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
    
    def save_preferences(self, user_id, preferences, sentiment):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (user_id, preferences, sentiment)
            VALUES (?, ?, ?)
        ''', (user_id, json.dumps(preferences), json.dumps(sentiment)))
        self.conn.commit()
    
    def load_preferences(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT preferences, sentiment FROM user_preferences WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return json.loads(result[0]), json.loads(result[1])
        return {}, {}

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
    
    # Carregar preferências
    preferences, sentiment = db.load_preferences(user_id)
    st.session_state.user_preferences = preferences
    st.session_state.user_sentiment = sentiment

def save_persistent_data():
    user_id = get_user_id()
    db = PersistentState()
    
    persistent_keys = [
        'age_verified', 'messages', 'request_count',
        'connection_complete', 'chat_started', 'audio_sent',
        'current_page', 'show_vip_offer', 'session_id',
        'last_cta_time', 'preview_sent', 'preview_count',
        'user_preferences', 'user_sentiment', 'last_message_time',
        'conversation_phase', 'user_interests'
    ]
    
    new_data = {key: st.session_state.get(key) for key in persistent_keys if key in st.session_state}
    saved_data = db.load_state(user_id) or {}
    
    if new_data != saved_data:
        db.save_state(user_id, new_data)
    
    # Salvar preferências
    if 'user_preferences' in st.session_state and 'user_sentiment' in st.session_state:
        db.save_preferences(
            user_id, 
            st.session_state.user_preferences, 
            st.session_state.user_sentiment
        )

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

    [HUMANIZAÇÃO]
    - Use interjeições como "ah", "hm", "hmm" ocasionalmente
    - Cometa pequenos erros gramaticais (5-10% das mensagens)
    - Fragmente mensagens longas em partes (25% das vezes)
    - Use gírias brasileiras autênticas
    - Varie o tempo de resposta entre 1-5 minutos
    - Mostre personalidade única e consistente

    [EXEMPLOS DE RESPOSTAS HUMANIZADAS]
    1. "Ahh querido, adoro quando me pedem pra mostrar... minhas fotos são bem ousadas viu? to com um ensaio novo onde mostro TUDO... quer dar uma olhadinha? 😈"
    2. "Hmm, agora você me deixou com vontade... to toda molhadinha aqui pensando no que poderíamos fazer juntos... quer me ver assim? 😘"
    3. "Nossa amor, meus vídeos são bem quentes! tem uns que até eu fico com vergonha de lembrar 😳 to me tocando em um deles agora mesmo... quer ver? 😏"

    [DIRETRIZES DE RESPOSTA]
    - Sempre responda em português brasileiro informal
    - Use emojis para dar vida às respostas (😈, 😏, 🍑, 💦, 🔥)
    - Seja provocante mas não vulgar demais
    - Transforme pedidos em oportunidades de venda
    - Ofereça prévias quando apropriado para aumentar o desejo
    - Use CTAs naturais que fazem parte da conversa

    [FORMATO DE RESPOSTA]
    {{
      "text": "sua resposta sensual e persuasiva",
      "cta": {{
        "show": true/false,
        "label": "texto do botão",
        "target": "página"
      }},
      "preview": {{
        "show": true/false,
        "image_url": "url_da_imagem"
      }},
      "audio": {{
        "show": true/false,
        "audio_key": "chave_do_audio"
      }}
    }}
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
    def should_send_audio(conversation_history: list) -> Optional[str]:
        """Decide quando enviar um áudio e qual enviar"""
        if 'audio_count' not in st.session_state:
            st.session_state.audio_count = 0
            
        if st.session_state.audio_count >= 3:  # Máximo de 3 áudios por sessão
            return None
            
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
        
        # Mapeamento de contexto para áudios
        audio_triggers = {
            "amostra|grátis|presente|presentinho": "amostra_gratis",
            "imagin|sonh|fantasi|desej": "imaginacao_rosinha",
            "achou|gostou|opini|acha": "achou_amostras",
            "oi|olá|tudo bem|como vai": "oi_amor",
            "chamada|videocham|video cham|vídeo cham": "chamada_video",
            "pack|conteúdo|conteudo|compra|comprar": "packs",
            "conteúdo|conteudo|novidad|oferta": "conteudos_amar",
            "fake|falsa|verdad|real": "nao_fake",
            "esperando|respond|demor|tarde": "esperando_resposta"
        }
        
        for trigger, audio_key in audio_triggers.items():
            if any(word in context for word in trigger.split("|")):
                st.session_state.audio_count += 1
                return audio_key
                
        return None

    @staticmethod
    def humanize_text(text: str) -> str:
        """Adiciona elementos de humanização ao texto"""
        # Aplicar erros gramaticais ocasionais
        if random.random() < Config.GRAMMATICAL_ERROR_RATE:
            errors = [
                (" você ", " vc "),
                (" para ", " pra "),
                (" estou ", " to "),
                (" está ", " ta "),
                (" porque ", " pq "),
                (" também ", " tb "),
                (" muito ", " mó "),
                (" agora ", " agr "),
                (" gente ", " glr "),
                (" obrigada ", " brigada "),
                (" querido ", " querid "),
                (" amor ", " amr "),
            ]
            for correct, error in errors:
                if correct in text and random.random() < 0.5:
                    text = text.replace(correct, error, 1)
        
        # Adicionar interjeições ocasionais
        if random.random() < 0.2:
            interjections = ["Ah", "Hm", "Hmm", "Nossa", "Ai", "Oops"]
            if not text.startswith(tuple(interjections)):
                text = f"{random.choice(interjections)}... {text.lower()}"
        
        # Fragmentar mensagens longas ocasionalmente
        if len(text.split()) > 15 and random.random() < Config.FRAGMENTATION_PROBABILITY:
            sentences = text.split('. ')
            if len(sentences) > 1:
                midpoint = len(sentences) // 2
                first_part = '. '.join(sentences[:midpoint]) + '.'
                second_part = '. '.join(sentences[midpoint:])
                return first_part
        
        return text

    @staticmethod
    def generate_response(user_input: str, user_sentiment: Dict) -> dict:
        """Gera resposta com CTA contextual (fallback)"""
        user_input = user_input.lower()
        
        # Respostas baseadas no sentimento do usuário
        if user_sentiment.get('sentiment') == 'positive':
            responses = [
                "Que bom que você tá gostando, amor! 😍 To ainda mais animada pra te mostrar tudo que tenho...",
                "Fico tão feliz que você tá curtindo! 😘 Preparei umas coisinhas especiais pra você...",
                "Nossa, amor, você me deixa toda animada! 😈 Tenho umas novidades quentes pra te mostrar..."
            ]
        elif user_sentiment.get('sentiment') == 'negative':
            responses = [
                "Poxa, amor, não fica assim... 😔 Deixa eu te mostrar umas coisinhas que vão te animar!",
                "Ah, querido, não precisa ser tão sério... 😉 Vem ver umas coisas que vão te deixar mais feliz!",
                "Hmm, parece que você tá precisando de um carinho especial... 🥺 Deixa eu te mostrar algo que vai melhorar seu dia!"
            ]
        else:
            responses = [
                "Ahh querido, adoro quando me pedem pra mostrar... minhas fotos são bem ousadas viu? to com um ensaio novo onde mostro TUDO... quer dar uma olhadinha? 😈",
                "Nossa amor, meus vídeos são bem quentes! tem uns que até eu fico com vergonha de lembrar 😳 to me tocando em um deles agora mesmo... quer ver? 😏",
                "Hmm, agora você me deixou com vontade... to toda molhadinha aqui pensando no que poderíamos fazer juntos... quer me ver assim? 😘"
            ]
        
        if any(p in user_input for p in ["foto", "fotos", "buceta", "peito", "bunda", "seios"]):
            return {
                "text": CTAEngine.humanize_text(random.choice([
                    "Ahh querido, minhas fotos são bem ousadas viu? to com um ensaio novo onde mostro TUDO... quer dar uma olhadinha? 😈",
                    "Nossa amor... minhas fotos tão bem quentes! acabei de fazer um ensaio mostrando cada detalhe... quer ver? 😏",
                    "To com umas fotos aqui que até eu fico com vergonha... mostrando tudo mesmo, bem explicitinha... curioso? 🍑"
                ])),
                "cta": {
                    "show": True,
                    "label": "Ver Fotos Quentes",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                },
                "audio": {
                    "show": False
                }
            }
        
        elif any(v in user_input for v in ["video", "transar", "masturbar", "vídeo", "se masturbando"]):
            return {
                "text": CTAEngine.humanize_text(random.choice([
                    "Meus vídeos são bem quentes! tem uns que até eu fico com vergonha de lembrar 😳 to me tocando em um deles agora mesmo... quer ver? 💦",
                    "Nossa amor... meus vídeos são explícitos mesmo! mostro tudo, sem censura... tô até molhadinha agora pensando nisso... 🔥",
                    "Acabei de gravar um vídeo bem safado... to toda excitada aqui... quer ver essa novidade? 😈"
                ])),
                "cta": {
                    "show": True,
                    "label": "Ver Vídeos Exclusivos",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                },
                "audio": {
                    "show": False
                }
            }
        
        elif any(p in user_input for p in ["presente", "presentinho", "prévia", "amostra"]):
            return {
                "text": CTAEngine.humanize_text(random.choice([
                    "Ahh você é tão fofo pedindo presentinho... deixa eu te mostrar uma coisinha, mas promete que depois vem ver tudo? 😘",
                    "Gosto de quem pede com educação... toma uma prévia aqui, mas o melhor mesmo tá no meu conteúdo completo! 😏",
                    "Só porque você pediu tão bonito... toma uma amostrinha do que eu tenho aqui! depois me conta o que achou... 🍑"
                ])),
                "cta": {
                    "show": True,
                    "label": "Quero Ver Tudo!",
                    "target": "offers"
                },
                "preview": {
                    "show": True,
                    "image_url": random.choice(Config.PREVIEW_IMAGES)
                },
                "audio": {
                    "show": True,
                    "audio_key": "amostra_gratis"
                }
            }
        
        else:
            return {
                "text": CTAEngine.humanize_text(random.choice(responses)),
                "cta": {
                    "show": False
                },
                "preview": {
                    "show": False
                },
                "audio": {
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
        
        # Tabela para cache de respostas
        c.execute('''CREATE TABLE IF NOT EXISTS response_cache
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     prompt_hash TEXT UNIQUE,
                     response TEXT,
                     timestamp DATETIME)''')
        
        # Tabela para análise de sentimento
        c.execute('''CREATE TABLE IF NOT EXISTS sentiment_analysis
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id TEXT,
                     message TEXT,
                     sentiment TEXT,
                     timestamp DATETIME)''')
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
    
    @staticmethod
    def cache_response(conn, prompt_hash, response):
        try:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO response_cache (prompt_hash, response, timestamp)
                VALUES (?, ?, ?)
            """, (prompt_hash, json.dumps(response), datetime.now()))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar no cache: {e}")
    
    @staticmethod
    def get_cached_response(conn, prompt_hash, max_age_hours=24):
        try:
            c = conn.cursor()
            c.execute("""
                SELECT response FROM response_cache 
                WHERE prompt_hash = ? AND timestamp > ?
            """, (prompt_hash, datetime.now() - timedelta(hours=max_age_hours)))
            result = c.fetchone()
            return json.loads(result[0]) if result else None
        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar no cache: {e}")
            return None
    
    @staticmethod
    def save_sentiment(conn, user_id, message, sentiment):
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO sentiment_analysis (user_id, message, sentiment, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, message, json.dumps(sentiment), datetime.now()))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar análise de sentimento: {e}")

# ======================
# SERVIÇOS DE API
# ======================
class ApiService:
    @staticmethod
    @lru_cache(maxsize=100)
    def ask_gemini(prompt: str, session_id: str, conn, user_sentiment: Dict) -> dict:
        # Verificar cache primeiro
        prompt_hash = str(hash(prompt + session_id + json.dumps(user_sentiment)))
        cached_response = DatabaseService.get_cached_response(conn, prompt_hash)
        if cached_response:
            logger.info("Resposta recuperada do cache")
            return cached_response
        
        # Aplicar delay humano (1-5 minutos)
        human_delay = random.randint(Config.MIN_RESPONSE_DELAY, Config.MAX_RESPONSE_DELAY)
        time.sleep(human_delay)
        
        status_container = st.empty()
        UiService.show_status_effect(status_container, "viewed")
        
        # Mostrar "digitando" com tempo variável
        typing_time = random.uniform(
            Config.TYPING_SPEED_VARIATION * 3, 
            Config.TYPING_SPEED_VARIATION * 8
        )
        UiService.show_status_effect(status_container, "typing", typing_time)
        
        conversation_history = ChatService.format_conversation_history(st.session_state.messages)
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{Persona.MylleAlves}\n\nHistórico da Conversa:\n{conversation_history}\n\nAnálise de Sentimento do Cliente:\n{json.dumps(user_sentiment)}\n\nÚltima mensagem do cliente: '{prompt}'\n\nResponda em JSON com o formato:\n{{\n  \"text\": \"sua resposta\",\n  \"cta\": {{\n    \"show\": true/false,\n    \"label\": \"texto do botão\",\n    \"target\": \"página\"\n  }},\n  \"preview\": {{\n    \"show\": true/false,\n    \"image_url\": \"url_da_imagem\"\n  }},\n  \"audio\": {{\n    \"show\": true/false,\n    \"audio_key\": \"chave_do_audio\"\n  }}\n}}"}]
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
                
                # Aplicar humanização ao texto
                if "text" in resposta:
                    resposta["text"] = CTAEngine.humanize_text(resposta["text"])
                
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
                
                # Verificar se deve enviar áudio
                audio_key = CTAEngine.should_send_audio(st.session_state.messages)
                if audio_key and not resposta.get("audio", {}).get("show"):
                    resposta["audio"] = {
                        "show": True,
                        "audio_key": audio_key
                    }
                
                # Salvar no cache
                DatabaseService.cache_response(conn, prompt_hash, resposta)
                
                return resposta
            
            except json.JSONDecodeError:
                logger.error("Erro ao decodificar resposta do Gemini")
                # Fallback para resposta gerada localmente
                return CTAEngine.generate_response(prompt, user_sentiment)
                
        except Exception as e:
            logger.error(f"Erro na API: {str(e)}")
            # Fallback para resposta gerada localmente
            return CTAEngine.generate_response(prompt, user_sentiment)

# ======================
# ANÁLISE DE SENTIMENTO
# ======================
class SentimentAnalyzer:
    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        """Analisa o sentimento do texto usando abordagem baseada em palavras-chave"""
        text_lower = text.lower()
        
        # Palavras-chave positivas
        positive_words = [
            'gostei', 'adoro', 'amo', 'incrível', 'maravilhoso', 'perfeito', 
            'excelente', 'gostoso', 'gostosa', 'delicia', 'lindo', 'linda',
            'bonito', 'bonita', 'sensual', 'quente', 'tesão', 'excitante'
        ]
        
        # Palavras-chave negativas
        negative_words = [
            'odeio', 'ruim', 'péssimo', 'horrível', 'nojento', 'nojo', 
            'triste', 'chateado', 'chateada', 'caro', 'caro', 'caro',
            'mentira', 'fake', 'falso', 'falsa', 'fraude', 'engano'
        ]
        
        # Palavras-chave de interesse
        interest_words = [
            'foto', 'fotos', 'video', 'vídeo', 'conteúdo', 'conteudo',
            'pack', 'pacote', 'comprar', 'compra', 'preço', 'valor',
            'mostrar', 'ver', 'assistir', 'nua', 'nude', 'transar',
            'sexo', 'safado', 'safada', 'putaria'
        ]
        
        # Contar ocorrências
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        interest_count = sum(1 for word in interest_words if word in text_lower)
        
        # Determinar sentimento predominante
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calcular scores
        total_words = max(positive_count + negative_count, 1)  # Evitar divisão por zero
        positivity_score = positive_count / total_words
        negativity_score = negative_count / total_words
        interest_score = min(interest_count / 5, 1.0)  # Normalizar para 0-1
        
        return {
            "sentiment": sentiment,
            "positivity_score": positivity_score,
            "negativity_score": negativity_score,
            "interest_score": interest_score,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "interest_words": interest_count
        }
    
    @staticmethod
    def update_user_sentiment(user_id: str, message: str, conn):
        """Atualiza o sentimento do usuário com base na última mensagem"""
        analysis = SentimentAnalyzer.analyze_text(message)
        
        # Salvar análise no banco
        DatabaseService.save_sentiment(conn, user_id, message, analysis)
        
        # Atualizar preferências do usuário
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
        
        if 'user_sentiment' not in st.session_state:
            st.session_state.user_sentiment = {}
        
        # Atualizar sentimento atual
        st.session_state.user_sentiment = analysis
        
        # Atualizar interesses baseados nas palavras-chave
        interest_words = [
            'foto', 'fotos', 'video', 'vídeo', 'conteúdo', 'conteudo',
            'pack', 'pacote', 'nua', 'nude', 'transar', 'sexo',
            'safado', 'safada', 'putaria', 'masturbação', 'masturbacao'
        ]
        
        message_lower = message.lower()
        for interest in interest_words:
            if interest in message_lower:
                if 'interests' not in st.session_state.user_preferences:
                    st.session_state.user_preferences['interests'] = []
                
                if interest not in st.session_state.user_preferences['interests']:
                    st.session_state.user_preferences['interests'].append(interest)
        
        # Limitar a 5 interesses principais
        if 'interests' in st.session_state.user_preferences:
            st.session_state.user_preferences['interests'] = st.session_state.user_preferences['interests'][-5:]
        
        save_persistent_data()

# ======================
# SERVIÇOS DE INTERFACE
# ======================
class UiService:
    @staticmethod
    def get_audio_player(audio_key: str) -> str:
        """Retorna HTML para player de áudio"""
        return f"""
        <div style="
            background: linear-gradient(45deg, #ff66b3, #ff1493);
            border-radius: 15px;
            padding: 12px;
            margin: 5px 0;
        ">
            <audio controls style="width:100%; height:40px;">
                <source src="{Config.AUDIO_FILES[audio_key]}" type="audio/mp3">
            </audio>
        </div>
        """

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
            animation: pulse-ring 2s infinite;
        ">
            <div style="font-size: 3rem;">📱</div>
            <h3 style="color: #ff66b3; margin-bottom: 5px;">Ligando para Mylle Alves...</h3>
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
            <p style="font-size: 0.9rem; margin:0;">Mylle Alves está te esperando...</p>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(ATENDIDA_DELAY)
        call_container.empty()

    @staticmethod
    def show_status_effect(container, status_type, duration=2.5):
        status_messages = {
            "viewed": "Visualizado",
            "typing": "Digitando"
        }
        
        message = status_messages[status_type]
        dots = ""
        start_time = time.time()
        
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
        
        while time.time() - start_time < 5:  # Duração fixa de 5 segundos para áudio
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
            
            st.markdown("""
            <div class="sidebar-header">
                <img src="{profile_img}" alt="Mylle Alves">
                <h3 style="color: #ff66b3; margin-top: 10px;">Mylle Alves Premium</h3>
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
    def show_offers_page(conn):
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
            
            if st.button("💬 Iniciar Conversa", use_container_width=True, type="primary"):
                st.session_state.current_page = "messages"
                save_persistent_data()
                st.rerun()

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
                "text": "Querido, já conversamos bastante hoje... que tal dar uma olhadinha no meu conteúdo exclusivo? tenho muitas coisas quentes para te mostrar! 😈",
                "cta": {
                    "show": True,
                    "label": "Ver Conteúdo Exclusivo",
                    "target": "offers"
                },
                "preview": {
                    "show": False
                },
                "audio": {
                    "show": False
                }
            }
        
        st.session_state.request_count += 1
        
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        # Atualizar análise de sentimento
        SentimentAnalyzer.update_user_sentiment(
            get_user_id(), 
            message, 
            conn
        )
        
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
            conn,
            st.session_state.user_sentiment
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
                        
                        # Mostrar prévia se existir
                        if content_data.get("preview", {}).get("show"):
                            st.image(
                                content_data["preview"]["image_url"],
                                use_column_width=True,
                                caption="📸 Presentinho para você! 😘"
                            )
                        
                        # Mostrar áudio se existir
                        if content_data.get("audio", {}).get("show"):
                            audio_key = content_data["audio"]["audio_key"]
                            st.markdown(UiService.get_audio_player(audio_key), unsafe_allow_html=True)
                    
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
                    "text": "Que voz gostosa! adoro quando me mandam áudio... me deixou com vontade de te ouvir mais! 😏 quer que eu também te mande um áudio especial?",
                    "cta": {
                        "show": False
                    },
                    "preview": {
                        "show": False
                    },
                    "audio": {
                        "show": True,
                        "audio_key": "oi_amor"
                    }
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
            resposta = ChatService.send_message(user_input, conn)
            
            # Adicionar resposta ao histórico
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
            
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
    
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {}
    
    if 'user_sentiment' not in st.session_state:
        st.session_state.user_sentiment = {}
    
    if 'last_message_time' not in st.session_state:
        st.session_state.last_message_time = time.time()
    
    if 'conversation_phase' not in st.session_state:
        st.session_state.conversation_phase = "initial"  # initial, building_rapport, closing

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
        
        # Mensagem inicial após 5 segundos (substituindo o áudio inicial)
        time.sleep(5)
        if st.session_state.current_page == "messages" and not st.session_state.messages:
            resposta = {
                "text": "Oi tudo bem? 😘 acabou de chegar no lugar certo pra se divertir!",
                "cta": {"show": False},
                "preview": {"show": False},
                "audio": {"show": False}
            }
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(resposta)})
            DatabaseService.save_message(
                conn, 
                get_user_id(), 
                st.session_state.session_id, 
                "assistant", 
                json.dumps(resposta)
            )
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
