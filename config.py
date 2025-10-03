import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import base64

# Charger les variables d'environnement
load_dotenv()

class Config:
    # Configuration Streamlit
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', 8501))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    
    # Clés API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Chemins
    OUTPUT_DIR = 'output'
    TOKEN_PATH = 'token.json'
    CREDENTIALS_PATH = 'credentials.json'
    
    # Scopes Gmail
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Headers pour éviter les blocages
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    @classmethod
    def get_encryption_key(cls):
        """Génère ou récupère la clé de chiffrement"""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY manquante dans les variables d'environnement")
        
        # Utiliser la SECRET_KEY pour générer une clé Fernet
        key = base64.urlsafe_b64encode(cls.SECRET_KEY.encode()[:32].ljust(32, b'0'))
        return Fernet(key)
    
    @classmethod
    def validate_config(cls):
        """Valide que toutes les configurations nécessaires sont présentes"""
        missing = []
        
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.SECRET_KEY:
            missing.append("SECRET_KEY")
            
        if missing:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing)}")
        
        return True

