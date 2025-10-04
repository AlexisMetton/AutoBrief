#!/usr/bin/env python3
"""
Script final pour envoyer des emails AutoBrief
Complètement standalone - sans aucune dépendance Streamlit
"""

import os
import sys
import json
import logging
import base64
from datetime import datetime
from email.mime.text import MIMEText

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_final(to_email, subject, content):
    """Envoie un email directement via Gmail API"""
    
    try:
        logger.info(f"📧 Envoi email final pour {to_email}")
        logger.info(f"📧 Sujet: {subject}")
        
        # Récupérer les credentials Google depuis les variables d'environnement
        google_credentials = os.getenv('GOOGLE_CREDENTIALS')
        if not google_credentials:
            logger.error("❌ GOOGLE_CREDENTIALS non trouvé dans les variables d'environnement")
            return False
        
        # Charger les credentials
        credentials_info = json.loads(google_credentials)
        
        # Debug: afficher les champs disponibles
        logger.info(f"🔍 Champs disponibles dans credentials: {list(credentials_info.keys())}")
        
        # Vérifier si c'est un fichier de credentials d'application ou d'utilisateur
        if 'installed' in credentials_info:
            # Credentials d'application - on a besoin des credentials OAuth2 de l'utilisateur
            logger.error("❌ GOOGLE_CREDENTIALS contient les credentials d'application, pas les credentials OAuth2 de l'utilisateur")
            logger.error("❌ Pour GitHub Actions, vous devez utiliser les credentials OAuth2 de l'utilisateur")
            logger.error("❌ Récupérez le fichier token.json après authentification dans l'application Streamlit")
            return False
        
        # Créer le service Gmail avec les credentials OAuth2 de l'utilisateur
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        # Créer les credentials OAuth2
        credentials = Credentials(
            token=credentials_info.get('token'),
            refresh_token=credentials_info.get('refresh_token'),
            token_uri=credentials_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=credentials_info.get('client_id'),
            client_secret=credentials_info.get('client_secret')
        )
        
        # Rafraîchir le token si nécessaire
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Créer le message
        message = MIMEText(content, 'html')
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = credentials_info.get('email', 'noreply@autobrief.com')
        
        # Encoder le message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Envoyer l'email
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f"✅ Email envoyé avec succès - Message ID: {result['id']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False

def main():
    """Point d'entrée principal"""
    
    # Récupérer les paramètres depuis les variables d'environnement
    to_email = os.getenv('TO_EMAIL', '')
    subject = os.getenv('SUBJECT', '')
    content = os.getenv('CONTENT', '')
    
    if not to_email or not subject or not content:
        logger.error("❌ Paramètres manquants: TO_EMAIL, SUBJECT, CONTENT")
        return
    
    # Envoyer l'email
    success = send_email_final(to_email, subject, content)
    
    if success:
        logger.info("✅ Email envoyé avec succès !")
        sys.exit(0)
    else:
        logger.error("❌ Échec envoi email")
        sys.exit(1)

if __name__ == "__main__":
    main()
