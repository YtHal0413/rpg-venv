import os

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "RPG_SECRET_KEY_SUPER_SAFE_123")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    AVATAR_FOLDER = os.path.join(BASE_DIR, "static", "avatars")  # NOVO
    DATABASE_NAME = "rpg_plataforma.db"
    DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_NAME)
    
    # Extensões permitidas para upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    CHAVE_TESTE_VALIDA = "HA4H4nF1tR1A0HA4"
    LIMITE_COLUNAS_FICHA = 3
    LIMITE_ABAS_COLUNA = 3

class DesenvolvimentoConfig(Config):
    DEBUG = True

class ProducaoConfig(Config):
    DEBUG = False