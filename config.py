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
    
    # Clés API - Détection automatique de l'environnement
    @classmethod
    def get_openai_key(cls):
        """Récupère la clé OpenAI depuis les secrets ou l'environnement"""
        # Essayer d'accéder aux secrets Streamlit d'abord
        try:
            return st.secrets['OPENAI_API_KEY']
        except (KeyError, AttributeError, Exception):
            # Fallback vers les variables d'environnement
            return os.getenv('OPENAI_API_KEY')
    
    @classmethod
    def get_secret_key(cls):
        """Récupère la clé secrète depuis les secrets ou l'environnement"""
        # Essayer d'accéder aux secrets Streamlit d'abord
        try:
            return st.secrets['SECRET_KEY']
        except (KeyError, AttributeError, Exception):
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
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    
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
        
        # Utiliser les méthodes get_* qui gèrent déjà le fallback
        openai_key = cls.get_openai_key()
        secret_key = cls.get_secret_key()
        
        if not openai_key:
            missing.append("OPENAI_API_KEY")
        if not secret_key:
            missing.append("SECRET_KEY")
            
        if missing:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing)}")
        
        return True

