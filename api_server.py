#!/usr/bin/env python3
"""
Serveur API simple pour AutoBrief
Endpoint HTTP pour l'envoi d'emails automatique
"""

import os
import sys
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from newsletter_manager import NewsletterManager
from config import Config
from secure_auth import SecureAuth

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIHandler(BaseHTTPRequestHandler):
    """Gestionnaire des requêtes API"""
    
    def do_GET(self):
        """Traite les requêtes GET"""
        try:
            # Parser l'URL
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Récupérer les paramètres
            action = query_params.get('action', [None])[0]
            api_key = query_params.get('api_key', [None])[0]
            user_email = query_params.get('user_email', [None])[0]
            subject = query_params.get('subject', [None])[0]
            content = query_params.get('content', [None])[0]
            
            # Vérifier la clé API
            if not self.verify_api_key(api_key):
                self.send_json_response({"error": "Clé API invalide", "status": 401})
                return
            
            # Traiter l'action
            if action == 'send_email':
                if not user_email or not subject or not content:
                    self.send_json_response({"error": "Paramètres manquants", "status": 400})
                    return
                
                result = self.send_email(user_email, subject, content)
                self.send_json_response(result)
                
            elif action == 'process_newsletters':
                if not user_email:
                    self.send_json_response({"error": "Paramètre user_email manquant", "status": 400})
                    return
                
                result = self.process_newsletters(user_email)
                self.send_json_response(result)
                
            else:
                self.send_json_response({"error": "Action non reconnue", "status": 400})
                
        except Exception as e:
            logger.error(f"Erreur dans do_GET: {e}")
            self.send_json_response({"error": f"Erreur interne: {str(e)}", "status": 500})
    
    def verify_api_key(self, api_key):
        """Vérifie la clé API"""
        expected_key = os.getenv('API_KEY')
        return api_key == expected_key
    
    def send_email(self, user_email, subject, content):
        """Envoie un email"""
        try:
            # Simuler une session utilisateur
            import streamlit as st
            st.session_state['user_email'] = user_email
            st.session_state['authenticated'] = True
            
            newsletter_manager = NewsletterManager()
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
    
    def process_newsletters(self, user_email):
        """Traite les newsletters d'un utilisateur"""
        try:
            # Simuler une session utilisateur
            import streamlit as st
            st.session_state['user_email'] = user_email
            st.session_state['authenticated'] = True
            
            newsletter_manager = NewsletterManager()
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
                    "error": "Aucun contenu trouvé",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": 500,
                "error": f"Erreur interne: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def send_json_response(self, data):
        """Envoie une réponse JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override pour éviter les logs verbeux"""
        pass

def run_api_server(port=8000):
    """Lance le serveur API"""
    try:
        server = HTTPServer(('0.0.0.0', port), APIHandler)
        logger.info(f"🚀 Serveur API démarré sur le port {port}")
        logger.info(f"📡 Endpoint: http://localhost:{port}/")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Serveur API arrêté")
    except Exception as e:
        logger.error(f"❌ Erreur serveur: {e}")

if __name__ == "__main__":
    port = int(os.getenv('API_PORT', 8000))
    run_api_server(port)
