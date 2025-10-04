#!/usr/bin/env python3
"""
API endpoint pour AutoBrief
Permet au scheduler GitHub Actions de déclencher l'envoi d'emails automatiquement
"""

import streamlit as st
import json
import os
from datetime import datetime
from newsletter_manager import NewsletterManager
from config import Config
from secure_auth import SecureAuth

def send_email_api(user_email, subject, content, api_key):
    """API endpoint pour l'envoi d'emails automatique"""
    
    # Vérifier la clé API
    if not verify_api_key(api_key):
        return {"error": "Clé API invalide", "status": 401}
    
    try:
        # Créer une instance temporaire de NewsletterManager
        # On simule une session utilisateur pour cet email
        st.session_state['user_email'] = user_email
        st.session_state['authenticated'] = True
        
        # Initialiser les composants
        config = Config()
        auth = SecureAuth()
        newsletter_manager = NewsletterManager()
        
        # Vérifier que l'utilisateur existe dans le Gist
        user_data = newsletter_manager.load_user_data()
        if not user_data or not user_data.get('newsletters'):
            return {"error": f"Utilisateur {user_email} non trouvé ou aucune newsletter", "status": 404}
        
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

def verify_api_key(api_key):
    """Vérifie la clé API"""
    # La clé API est stockée dans les secrets Streamlit
    expected_key = None
    
    try:
        # Essayer de récupérer depuis les secrets Streamlit
        if hasattr(st, 'secrets') and st.secrets:
            expected_key = st.secrets.get('API_KEY')
    except:
        pass
    
    # Fallback sur les variables d'environnement
    if not expected_key:
        expected_key = os.getenv('API_KEY')
    
    return api_key == expected_key

def process_newsletters_api(user_email, api_key):
    """API endpoint pour traiter les newsletters d'un utilisateur"""
    
    # Vérifier la clé API
    if not verify_api_key(api_key):
        return {"error": "Clé API invalide", "status": 401}
    
    try:
        # Créer une instance temporaire de NewsletterManager
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

# Point d'entrée pour l'API
def main():
    """Point d'entrée principal de l'API"""
    
    # Récupérer les paramètres de la requête
    if hasattr(st, 'query_params'):
        params = st.query_params
    else:
        params = {}
    
    action = params.get('action', '')
    api_key = params.get('api_key', '')
    
    if action == 'send_email':
        user_email = params.get('user_email', '')
        subject = params.get('subject', '')
        content = params.get('content', '')
        
        if not user_email or not subject or not content:
            st.json({"error": "Paramètres manquants: user_email, subject, content", "status": 400})
            return
        
        result = send_email_api(user_email, subject, content, api_key)
        st.json(result)
        
    elif action == 'process_newsletters':
        user_email = params.get('user_email', '')
        
        if not user_email:
            st.json({"error": "Paramètre manquant: user_email", "status": 400})
            return
        
        result = process_newsletters_api(user_email, api_key)
        st.json(result)
        
    else:
        st.json({
            "error": "Action non reconnue. Actions disponibles: send_email, process_newsletters",
            "status": 400
        })

if __name__ == "__main__":
    main()
