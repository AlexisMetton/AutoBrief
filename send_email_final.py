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
        
        # Créer le service Gmail
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        credentials = Credentials.from_authorized_user_info(credentials_info)
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
