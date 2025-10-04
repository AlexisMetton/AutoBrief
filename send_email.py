#!/usr/bin/env python3
"""
Script simple pour envoyer un email via l'API AutoBrief
Utilisé par le scheduler GitHub Actions
"""

import os
import sys
import json
import requests
from datetime import datetime

def send_email_direct(to_email, subject, content):
    """Envoie un email directement via les modules AutoBrief"""
    
    try:
        print(f"📧 Envoi email direct pour {to_email}")
        print(f"📧 Sujet: {subject}")
        
        # Importer les modules nécessaires
        from newsletter_manager import NewsletterManager
        import streamlit as st
        
        # Simuler une session utilisateur
        st.session_state['user_email'] = to_email
        st.session_state['authenticated'] = True
        
        # Créer l'instance NewsletterManager
        newsletter_manager = NewsletterManager()
        
        # Envoyer l'email
        success = newsletter_manager.send_summary_email(content, to_email)
        
        if success:
            print(f"✅ Email envoyé avec succès à {to_email}")
            return True
        else:
            print(f"❌ Erreur lors de l'envoi de l'email")
            return False
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False

def main():
    """Point d'entrée principal"""
    
    # Récupérer les paramètres depuis les variables d'environnement
    to_email = os.getenv('TO_EMAIL', '')
    subject = os.getenv('SUBJECT', '')
    content = os.getenv('CONTENT', '')
    
    if not to_email or not subject or not content:
        print("❌ Paramètres manquants: TO_EMAIL, SUBJECT, CONTENT")
        return
    
    # Envoyer l'email
    success = send_email_direct(to_email, subject, content)
    
    if success:
        print("✅ Email envoyé avec succès !")
        sys.exit(0)
    else:
        print("❌ Échec envoi email")
        sys.exit(1)

if __name__ == "__main__":
    main()
