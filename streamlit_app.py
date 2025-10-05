import streamlit as st
import os
from datetime import datetime, timedelta
from config import Config
from secure_auth import SecureAuth
from newsletter_manager import NewsletterManager
import json

def create_header():
    """Crée le header avec logo seulement"""
    
    # CSS pour le header
    st.markdown("""
    <style>
    .main-header {
        background: white;
        border-bottom: 2px solid #e1e5e9;
        padding: 1rem 2rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .logo {
        height: 40px;
        width: 40px;
    }
    .app-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header avec logo seulement
    st.markdown("""
    <div class="main-header">
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/AlexisMetton/AutoBrief/main/public/assets/logo_autobrief.png" 
                 alt="AutoBrief" class="logo">
            <h1 class="app-title">AutoBrief</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Configuration de la page
st.set_page_config(
    page_title="AutoBrief - Veille IA Automatisée",
    page_icon="https://raw.githubusercontent.com/AlexisMetton/AutoBrief/main/public/assets/favicon_autobrief.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    # Initialisation
    try:
        config = Config()
        config.validate_config()
    except ValueError as e:
        st.error(f"❌ Configuration manquante: {e}")
        st.info("💡 Créez un fichier .env avec vos clés API (voir .env.example)")
        return
    
    auth = SecureAuth()
    newsletter_manager = NewsletterManager()
    
    # Vérifier si un résumé automatique doit être généré
    if newsletter_manager.should_run_automatically():
        with st.spinner("Génération automatique en cours..."):
            result = newsletter_manager.process_newsletters()
            if result:
                st.session_state['last_summary'] = result
                st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.success("Résumé automatique généré !")
                st.rerun()
    
    # Créer le header (toujours affiché)
    create_header()
    
    # Authentification
    if not auth.authenticate_user():
        st.stop()
    
    # Navigation avec session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    
    # Navigation visible et fonctionnelle
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Accueil", key="nav_home", type="primary" if st.session_state.current_page == "Accueil" else "secondary"):
            st.session_state.current_page = "Accueil"
            st.rerun()
    
    with col2:
        if st.button("Newsletters", key="nav_newsletters", type="primary" if st.session_state.current_page == "Newsletters" else "secondary"):
            st.session_state.current_page = "Newsletters"
            st.rerun()
    
    with col3:
        if st.button("Paramètres", key="nav_settings", type="primary" if st.session_state.current_page == "Paramètres" else "secondary"):
            st.session_state.current_page = "Paramètres"
            st.rerun()
    
    with col4:
        if st.button("Aide", key="nav_help", type="primary" if st.session_state.current_page == "Aide" else "secondary"):
            st.session_state.current_page = "Aide"
            st.rerun()
    
    # Menu utilisateur dans la sidebar
    with st.sidebar:
        st.markdown(f"**Connecté:** {st.session_state.get('user_email', 'Utilisateur')}")
        
        if st.button("Se déconnecter", type="secondary"):
            auth.logout()
        
        st.markdown("---")
    
    # Déterminer la page active
    page = st.session_state.current_page
    
    # Contenu principal selon la page sélectionnée
    if page == "Accueil":
        show_home_page(newsletter_manager)
    elif page == "Newsletters":
        show_newsletters_page(newsletter_manager)
    elif page == "Paramètres":
        show_configuration_page()
    elif page == "Aide":
        show_help_page()

def show_home_page(newsletter_manager):
    """Page d'accueil avec vue d'ensemble"""
    
    # Section hero
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="margin: 0; font-size: 2.5rem;">🤖 AutoBrief</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Automatisez votre veille avec l'intelligence artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Newsletters",
            value=len(newsletter_manager.get_newsletters()),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Dernière exécution",
            value="Jamais" if 'last_run' not in st.session_state else st.session_state['last_run'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Emails traités",
            value=st.session_state.get('processed_emails', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            label="Status IA",
            value="Actif" if st.session_state.get('openai_configured', False) else "Inactif",
            delta=None
        )
    
    # Actions rapides
    st.markdown("### Actions rapides")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Tester la newsletter", type="primary", use_container_width=True):
            if not newsletter_manager.get_newsletters():
                st.error("Aucune newsletter configurée. Allez dans l'onglet 'Newsletters' pour en ajouter.")
            else:
                with st.spinner("Test de la newsletter en cours..."):
                    # Récupérer la configuration utilisateur
                    user_data = newsletter_manager.load_user_data()
                    days_to_analyze = user_data.get('settings', {}).get('days_to_analyze', 7)
                    
                    # Générer le résumé avec la configuration utilisateur
                    result = newsletter_manager.process_newsletters(days=days_to_analyze, send_email=True)
                    if result:
                        st.session_state['last_summary'] = result
                        st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.success("Test de newsletter réussi ! Résumé généré et email envoyé.")
                        st.rerun()
                    else:
                        st.error("Aucun contenu trouvé pour la période sélectionnée")
    
    with col2:
        if st.button("Tester l'envoi", type="secondary", use_container_width=True):
            settings = newsletter_manager.get_user_settings()
            notification_email = settings.get('notification_email')
            if notification_email and notification_email.strip():
                try:
                    test_summary = "Ceci est un test d'envoi d'email depuis AutoBrief. Si vous recevez ce message, l'envoi automatique fonctionne correctement !"
                    if newsletter_manager.send_summary_email(test_summary, notification_email):
                        st.success(f"Email de test envoyé à {notification_email}")
                    else:
                        st.error("Erreur lors de l'envoi de l'email de test")
                except Exception as e:
                    st.error(f"Erreur: {e}")
            else:
                st.warning("Configurez d'abord une adresse email de notification")
    
    with col3:
        if st.button("Gérer les newsletters", use_container_width=True):
            st.session_state['current_page'] = "Newsletters"
            st.rerun()
    
    # Dernier résumé
    if 'last_summary' in st.session_state:
        st.markdown("### Dernier résumé généré")
        with st.expander("Voir le résumé", expanded=False):
            st.markdown(st.session_state['last_summary'])

def show_newsletters_page(newsletter_manager):
    """Page de gestion des newsletters"""
    st.markdown("## Gestion des Newsletters")
    
    newsletter_manager.render_newsletter_management()
    
    # Configuration de la période
    st.markdown("### Configuration de la période")
    col1, col2 = st.columns(2)
    
    with col1:
        days = st.slider(
            "Nombre de jours à analyser:",
            min_value=1,
            max_value=30,
            value=7,
            help="Période de recherche dans vos emails"
        )
    
    with col2:
        st.info(f"📅 Analyse des emails des {days} derniers jours")

def show_configuration_page():
    """Page de configuration"""
    st.markdown("## Configuration")
    
    # Configuration OpenAI
    st.markdown("### Configuration OpenAI")
    
    if st.session_state.get('openai_configured', False):
        st.success("Clé OpenAI configurée")
    else:
        st.warning("Clé OpenAI non configurée")
    
    # Test de la configuration
    if st.button("Tester la configuration"):
        with st.spinner("Test en cours..."):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=Config.get_openai_key())
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                st.success("Configuration OpenAI fonctionnelle")
                st.session_state['openai_configured'] = True
            except Exception as e:
                st.error(f"Erreur de configuration: {e}")
                st.session_state['openai_configured'] = False
    
    # Affichage du token OAuth2
    st.markdown("### Token OAuth2")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Afficher le contenu de token.json"):
            st.session_state['show_token'] = True
    
    with col2:
        if st.button("Masquer le token"):
            st.session_state['show_token'] = False
    
    # Afficher le token si demandé
    if st.session_state.get('show_token', False):
        try:
            # Vérifier d'abord si on a un token chiffré dans la session
            if 'encrypted_token' in st.session_state and st.session_state['encrypted_token']:
                # Décrypter le token pour l'affichage
                from secure_auth import SecureAuth
                auth = SecureAuth()
                decrypted_token = auth.decrypt_token(st.session_state['encrypted_token'])
                
                if decrypted_token:
                    st.success("Token OAuth2 trouvé dans la session !")
                    st.code(json.dumps(decrypted_token, indent=2), language='json')
                    
                    st.info("**Pour GitHub Actions :** Copiez ce contenu et ajoutez-le comme secret `GOOGLE_CREDENTIALS`")
                else:
                    st.error("Erreur lors du déchiffrement du token.")
            else:
                st.warning("Aucun token OAuth2 trouvé dans la session.")
                st.info("Connectez-vous d'abord avec Google pour générer le token.")
                
        except Exception as e:
            st.error(f"Erreur lors de la lecture du token: {e}")
    
    # Informations système
    st.markdown("### Informations système")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"Python: {os.sys.version}")
        st.info(f"Streamlit: {st.__version__}")
    
    with col2:
        st.info(f"Authentification: {'Active' if st.session_state.get('authenticated') else 'Inactive'}")
        st.info(f"Gmail API: {'Connecté' if st.session_state.get('authenticated') else 'Non connecté'}")



def show_help_page():
    """Page d'aide"""
    st.markdown("## Aide et Support")
    
    st.markdown("""
    ### Comment utiliser AutoBrief
    
    **1. Configuration initiale:**
    - Assurez-vous d'avoir un fichier `.env` avec vos clés API
    - Placez le fichier `credentials.json` dans le répertoire du projet
    
    **2. Ajout des newsletters:**
    - Allez dans l'onglet "Newsletters"
    - Ajoutez les adresses email qui vous envoient des newsletters
    - Configurez la période d'analyse
    
    **3. Génération du résumé:**
    - Cliquez sur "Tester la newsletter"
    - Le système analysera vos emails et extraira les actualités IA
    - Le résumé sera disponible dans l'onglet "Résultats"
    
    ### Configuration requise
    
    **Variables d'environnement (.env):**
    ```
    OPENAI_API_KEY=votre_clé_openai
    SECRET_KEY=votre_clé_secrète
    ```
    
    **Fichiers requis:**
    - `credentials.json` (Google OAuth)
    - `.env` (clés API)
    
    ### Sécurité
    
    - Authentification OAuth2 Google
    - Chiffrement des tokens
    - Variables d'environnement sécurisées
    - Sessions chiffrées
    - Permissions limitées (lecture seule Gmail)
    
    ### Support
    
    Pour toute question ou problème, consultez la documentation ou contactez le support.
    """)

if __name__ == "__main__":
    main()

