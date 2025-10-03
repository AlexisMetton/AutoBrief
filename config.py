import os
import streamlit as st
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import base64

# Charger les variables d'environnement
load_dotenv()

class Config:
    # Configuration Streamlit
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', 8501))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    
    # Clés API - Priorité aux secrets Streamlit
    @classmethod
    def get_openai_key(cls):
        """Récupère la clé OpenAI depuis les secrets ou l'environnement"""
        try:
            # Essayer d'accéder aux secrets Streamlit
            if hasattr(st, 'secrets') and st.secrets:
                return st.secrets.get('OPENAI_API_KEY')
        except Exception:
            pass
        # Fallback vers les variables d'environnement
        return os.getenv('OPENAI_API_KEY')
    
    @classmethod
    def get_secret_key(cls):
        """Récupère la clé secrète depuis les secrets ou l'environnement"""
        try:
            # Essayer d'accéder aux secrets Streamlit
            if hasattr(st, 'secrets') and st.secrets:
                return st.secrets.get('SECRET_KEY')
        except Exception:
            pass
        # Fallback vers les variables d'environnement
        return os.getenv('SECRET_KEY')
    
    @property
    def OPENAI_API_KEY(self):
        return self.get_openai_key()
    
    @property
    def SECRET_KEY(self):
        return self.get_secret_key()
    
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
        secret_key = cls.get_secret_key()
        if not secret_key:
            raise ValueError("SECRET_KEY manquante dans les variables d'environnement")
        
        # Utiliser la SECRET_KEY pour générer une clé Fernet
        key = base64.urlsafe_b64encode(secret_key.encode()[:32].ljust(32, b'0'))
        return Fernet(key)
    
    @classmethod
    def validate_config(cls):
        """Valide que toutes les configurations nécessaires sont présentes"""
        missing = []
        
        # Vérifier les secrets Streamlit d'abord
        try:
            if hasattr(st, 'secrets') and st.secrets:
                openai_key = st.secrets.get('OPENAI_API_KEY')
                secret_key = st.secrets.get('SECRET_KEY')
            else:
                openai_key = None
                secret_key = None
        except Exception:
            openai_key = None
            secret_key = None
        
        # Fallback vers les variables d'environnement
        if not openai_key:
            openai_key = os.getenv('OPENAI_API_KEY')
        if not secret_key:
            secret_key = os.getenv('SECRET_KEY')
        
        if not openai_key:
            missing.append("OPENAI_API_KEY")
        if not secret_key:
            missing.append("SECRET_KEY")
            
        if missing:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing)}")
        
        return True

