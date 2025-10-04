#!/usr/bin/env python3
"""
Script standalone pour envoyer des emails AutoBrief
Sans dépendance Streamlit - pour GitHub Actions
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_standalone(to_email, subject, content):
    """Envoie un email sans Streamlit"""
    
    try:
        logger.info(f"📧 Envoi email standalone pour {to_email}")
        logger.info(f"📧 Sujet: {subject}")
        
        # Importer les modules nécessaires
        from config import Config
        from secure_auth import SecureAuth
        from newsletter_manager import NewsletterManager
        
        # Créer les instances sans Streamlit
        config = Config()
        auth = SecureAuth()
        
        # Créer un NewsletterManager sans session Streamlit
        newsletter_manager = NewsletterManagerStandalone(to_email, config, auth)
        
        # Envoyer l'email
        success = newsletter_manager.send_summary_email(content, to_email)
        
        if success:
            logger.info(f"✅ Email envoyé avec succès à {to_email}")
            return True
        else:
            logger.error(f"❌ Erreur lors de l'envoi de l'email")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False

class NewsletterManagerStandalone:
    """Version standalone de NewsletterManager sans Streamlit"""
    
    def __init__(self, user_email, config, auth):
        self.user_email = user_email
        self.config = config
        self.auth = auth
        self.client = None
        
        # Initialiser OpenAI
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=config.get_openai_key())
        except Exception as e:
            logger.error(f"❌ Erreur initialisation OpenAI: {e}")
    
    def send_summary_email(self, summary, notification_email):
        """Envoie le résumé par email"""
        try:
            # Utiliser Gmail API directement
            service = self.auth.get_gmail_service()
            if not service:
                logger.error("❌ Impossible d'accéder à Gmail")
                return False
            
            # Créer le message
            import base64
            from email.mime.text import MIMEText
            
            message = MIMEText(summary, 'html')
            message['to'] = notification_email
            message['subject'] = f"📧 Résumé AutoBrief - {datetime.now().strftime('%d/%m/%Y')}"
            message['from'] = self.user_email
            
            # Encoder le message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Envoyer l'email
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ Email envoyé - Message ID: {result['id']}")
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
    success = send_email_standalone(to_email, subject, content)
    
    if success:
        logger.info("✅ Email envoyé avec succès !")
        sys.exit(0)
    else:
        logger.error("❌ Échec envoi email")
        sys.exit(1)

if __name__ == "__main__":
    main()
