#!/usr/bin/env python3
"""
API Endpoint pour AutoBrief
Point d'entrée pour les appels API externes (GitHub Actions)
"""

import os
import sys
import json
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from newsletter_manager import NewsletterManager
from config import Config
from secure_auth import SecureAuth

def verify_api_key(api_key):
    """Vérifie la clé API"""
    expected_key = os.getenv('API_KEY')
    return api_key == expected_key

def send_email_api(user_email, subject, content, api_key):
    """API endpoint pour l'envoi d'emails automatique"""
    
    # Vérifier la clé API
    if not verify_api_key(api_key):
        return {"error": "Clé API invalide", "status": 401}
    
    try:
        # Simuler une session utilisateur pour l'API
        import streamlit as st
        st.session_state['user_email'] = user_email
        st.session_state['authenticated'] = True
        
        # Initialiser les composants
        newsletter_manager = NewsletterManager()
        
        # Envoyer l'email
        success = newsletter_manager.send_summary_email(content, user_email)
        
        if success:
            return {
                "status": 200,
                "message": f"Email envoyé avec succès à {user_email}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": 500,
                "error": "Erreur lors de l'envoi de l'email",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": 500,
            "error": f"Erreur interne: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def process_newsletters_api(user_email, api_key):
    """API endpoint pour traiter les newsletters d'un utilisateur"""
    
    # Vérifier la clé API
    if not verify_api_key(api_key):
        return {"error": "Clé API invalide", "status": 401}
    
    try:
        # Simuler une session utilisateur pour l'API
        import streamlit as st
        st.session_state['user_email'] = user_email
        st.session_state['authenticated'] = True
        
        newsletter_manager = NewsletterManager()
        
        # Traiter les newsletters et envoyer l'email
        result = newsletter_manager.process_newsletters(send_email=True)
        
        if result:
            return {
                "status": 200,
                "message": f"Newsletters traitées et email envoyé à {user_email}",
                "summary_length": len(result),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": 404,
                "error": "Aucun contenu trouvé pour générer le résumé",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": 500,
            "error": f"Erreur interne: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Point d'entrée principal de l'API"""
    
    # Lire les paramètres depuis les variables d'environnement ou stdin
    import sys
    
    # Pour les appels HTTP, on peut utiliser des variables d'environnement
    action = os.getenv('ACTION', '')
    api_key = os.getenv('API_KEY', '')
    user_email = os.getenv('USER_EMAIL', '')
    subject = os.getenv('SUBJECT', '')
    content = os.getenv('CONTENT', '')
    
    # Si pas de paramètres dans l'environnement, essayer de lire depuis stdin
    if not action and len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
            action = params.get('action', '')
            api_key = params.get('api_key', '')
            user_email = params.get('user_email', '')
            subject = params.get('subject', '')
            content = params.get('content', '')
        except:
            pass
    
    if action == 'send_email':
        if not user_email or not subject or not content:
            print(json.dumps({"error": "Paramètres manquants: user_email, subject, content", "status": 400}))
            return
        
        result = send_email_api(user_email, subject, content, api_key)
        print(json.dumps(result))
        
    elif action == 'process_newsletters':
        if not user_email:
            print(json.dumps({"error": "Paramètre manquant: user_email", "status": 400}))
            return
        
        result = process_newsletters_api(user_email, api_key)
        print(json.dumps(result))
        
    else:
        print(json.dumps({
            "error": "Action non reconnue. Actions disponibles: send_email, process_newsletters",
            "status": 400
        }))

if __name__ == "__main__":
    main()
