#!/usr/bin/env python3
"""
Page API pour AutoBrief
Endpoint pour l'envoi d'emails automatique via GitHub Actions
"""

import streamlit as st
import json
import os
from datetime import datetime
from newsletter_manager import NewsletterManager
from config import Config
from secure_auth import SecureAuth

st.set_page_config(
    page_title="API AutoBrief",
    page_icon="🔌",
    layout="wide"
)

st.markdown("# 🔌 API AutoBrief")

st.markdown("""
Cette page fournit une API endpoint pour permettre au scheduler GitHub Actions 
de déclencher l'envoi d'emails automatiquement.
""")

# Configuration de l'API
st.markdown("## 🔑 Configuration API")

st.info("""
**Pour utiliser l'API, vous devez configurer une clé API dans les secrets Streamlit :**
- Nom : `API_KEY`
- Valeur : Une chaîne de caractères secrète (ex: `autobrief_api_2024_secret_key`)
""")

# Documentation de l'API
st.markdown("## 📚 Documentation API")

st.markdown("""
### **Endpoint : Envoi d'email**
```
GET https://votre-app.streamlit.app/api?action=send_email&api_key=YOUR_API_KEY&user_email=user@example.com&subject=Test&content=Contenu
```

### **Endpoint : Traitement des newsletters**
```
GET https://votre-app.streamlit.app/api?action=process_newsletters&api_key=YOUR_API_KEY&user_email=user@example.com
```
""")

# Test de l'API
st.markdown("## 🧪 Test de l'API")

with st.expander("Tester l'API localement", expanded=False):
    
    api_key = st.text_input("Clé API", type="password", help="Entrez votre clé API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Test d'envoi d'email")
        
        test_user_email = st.text_input("Email utilisateur", value="alexis.metton@gmail.com")
        test_subject = st.text_input("Sujet", value="Test API")
        test_content = st.text_area("Contenu", value="Ceci est un test de l'API AutoBrief.")
        
        if st.button("Tester l'envoi d'email"):
            if api_key and test_user_email and test_subject and test_content:
                # Simuler l'appel API
                st.session_state['user_email'] = test_user_email
                st.session_state['authenticated'] = True
                
                try:
                    newsletter_manager = NewsletterManager()
                    success = newsletter_manager.send_summary_email(test_content, test_user_email)
                    
                    if success:
                        st.success("✅ Email envoyé avec succès !")
                    else:
                        st.error("❌ Erreur lors de l'envoi de l'email")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            else:
                st.error("❌ Veuillez remplir tous les champs")
    
    with col2:
        st.markdown("### Test de traitement des newsletters")
        
        test_user_email_2 = st.text_input("Email utilisateur", value="alexis.metton@gmail.com", key="test_user_2")
        
        if st.button("Tester le traitement"):
            if api_key and test_user_email_2:
                # Simuler l'appel API
                st.session_state['user_email'] = test_user_email_2
                st.session_state['authenticated'] = True
                
                try:
                    newsletter_manager = NewsletterManager()
                    result = newsletter_manager.process_newsletters(send_email=True)
                    
                    if result:
                        st.success("✅ Newsletters traitées et email envoyé !")
                        with st.expander("Voir le résumé généré"):
                            st.markdown(result)
                    else:
                        st.error("❌ Aucun contenu trouvé")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            else:
                st.error("❌ Veuillez remplir tous les champs")

# Informations de débogage
st.markdown("## 🔍 Informations de débogage")

with st.expander("État de l'application", expanded=False):
    st.json({
        "user_email": st.session_state.get('user_email', 'Non connecté'),
        "authenticated": st.session_state.get('authenticated', False),
        "api_key_configured": bool(st.secrets.get('API_KEY') if hasattr(st, 'secrets') else False),
        "timestamp": datetime.now().isoformat()
    })

# Logs des appels API
if 'api_logs' not in st.session_state:
    st.session_state['api_logs'] = []

st.markdown("## 📝 Logs des appels API")

if st.session_state['api_logs']:
    for log in reversed(st.session_state['api_logs'][-10:]):  # Afficher les 10 derniers
        st.text(log)
else:
    st.info("Aucun appel API enregistré")

# Bouton pour vider les logs
if st.button("Vider les logs"):
    st.session_state['api_logs'] = []
    st.rerun()

# Traitement des appels API
def handle_api_call():
    """Traite les appels API et retourne du JSON"""
    
    # Récupérer les paramètres de la requête
    if hasattr(st, 'query_params'):
        params = st.query_params
    else:
        params = {}
    
    action = params.get('action', '')
    api_key = params.get('api_key', '')
    
    # Si c'est un appel API, traiter et retourner du JSON
    if action and api_key:
        
        # Vérifier la clé API
        expected_key = None
        try:
            if hasattr(st, 'secrets') and st.secrets:
                expected_key = st.secrets.get('API_KEY')
        except:
            pass
        
        if not expected_key:
            expected_key = os.getenv('API_KEY')
        
        if api_key != expected_key:
            st.json({"error": "Clé API invalide", "status": 401})
            return
        
        # Traiter l'action
        if action == 'send_email':
            user_email = params.get('user_email', '')
            subject = params.get('subject', '')
            content = params.get('content', '')
            
            if not user_email or not subject or not content:
                st.json({"error": "Paramètres manquants", "status": 400})
                return
            
            try:
                # Simuler une session utilisateur
                st.session_state['user_email'] = user_email
                st.session_state['authenticated'] = True
                
                newsletter_manager = NewsletterManager()
                success = newsletter_manager.send_summary_email(content, user_email)
                
                if success:
                    st.json({
                        "status": 200,
                        "message": f"Email envoyé avec succès à {user_email}",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    st.json({
                        "status": 500,
                        "error": "Erreur lors de l'envoi de l'email",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                st.json({
                    "status": 500,
                    "error": f"Erreur interne: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
        
        elif action == 'process_newsletters':
            user_email = params.get('user_email', '')
            
            if not user_email:
                st.json({"error": "Paramètre user_email manquant", "status": 400})
                return
            
            try:
                # Simuler une session utilisateur
                st.session_state['user_email'] = user_email
                st.session_state['authenticated'] = True
                
                newsletter_manager = NewsletterManager()
                result = newsletter_manager.process_newsletters(send_email=True)
                
                if result:
                    st.json({
                        "status": 200,
                        "message": f"Newsletters traitées et email envoyé à {user_email}",
                        "summary_length": len(result),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    st.json({
                        "status": 404,
                        "error": "Aucun contenu trouvé",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                st.json({
                    "status": 500,
                    "error": f"Erreur interne: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
        
        else:
            st.json({
                "error": "Action non reconnue",
                "status": 400
            })
        
        return
    
    # Si ce n'est pas un appel API, afficher l'interface normale
    # Log des appels pour l'interface
    if action:
        log_entry = f"[{datetime.now()}] 🔄 Appel API: {action}"
        if 'api_logs' not in st.session_state:
            st.session_state['api_logs'] = []
        st.session_state['api_logs'].append(log_entry)

# Appeler le gestionnaire d'API
handle_api_call()
