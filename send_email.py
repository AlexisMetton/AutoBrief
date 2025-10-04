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

def send_email_via_streamlit(to_email, subject, content):
    """Envoie un email via l'application Streamlit"""
    
    try:
        # URL de votre application Streamlit
        streamlit_url = "https://alexismetton.streamlit.app"
        
        # Récupérer la clé API depuis les variables d'environnement
        api_key = os.getenv('API_KEY')
        if not api_key:
            print(f"❌ API_KEY non trouvé dans les variables d'environnement")
            return False
        
        # Construire l'URL de l'API
        api_url = f"{streamlit_url}/api"
        
        # Paramètres de la requête
        params = {
            'action': 'send_email',
            'api_key': api_key,
            'user_email': to_email,
            'subject': subject,
            'content': content
        }
        
        print(f"📧 Envoi email via API Streamlit pour {to_email}")
        print(f"📧 URL: {api_url}")
        
        # Faire l'appel API
        response = requests.get(api_url, params=params, timeout=30)
        
        print(f"📧 Status Code: {response.status_code}")
        print(f"📧 Response: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == 200:
                    print(f"✅ Email envoyé avec succès à {to_email}")
                    return True
                else:
                    print(f"❌ Erreur API: {result.get('error', 'Erreur inconnue')}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Réponse non-JSON reçue: {response.text}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ Timeout lors de l'appel API")
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
    success = send_email_via_streamlit(to_email, subject, content)
    
    if success:
        print("✅ Email envoyé avec succès !")
        sys.exit(0)
    else:
        print("❌ Échec envoi email")
        sys.exit(1)

if __name__ == "__main__":
    main()
