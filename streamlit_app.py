import streamlit as st
import os
from datetime import datetime, timedelta
from config import Config
from secure_auth import SecureAuth
from newsletter_manager import NewsletterManager
import json

# Ajouter Font Awesome
st.markdown("""
<script src="https://kit.fontawesome.com/4b82313637.js" crossorigin="anonymous"></script>
""", unsafe_allow_html=True)

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
    page_title="AutoBrief - Veille Automatisée",
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
        st.error(f"<i class='fas fa-exclamation-triangle'></i> Configuration manquante: {e}")
        st.info("<i class='fas fa-lightbulb'></i> Créez un fichier .env avec vos clés API (voir .env.example)")
        return
    
    auth = SecureAuth()
    newsletter_manager = NewsletterManager()
    
    # Créer le header (toujours affiché)
    create_header()
        
        # Authentification
    if not auth.authenticate_user():
        st.stop()
        
    # Vérifier si un résumé automatique doit être généré (APRÈS authentification)
    if newsletter_manager.should_run_automatically():
        with st.spinner("Génération automatique en cours..."):
            # Récupérer la configuration utilisateur pour les jours à analyser
            user_data = newsletter_manager.load_user_data()
            days_to_analyze = user_data.get('settings', {}).get('days_to_analyze', 7)
            
            result = newsletter_manager.process_newsletters(days=days_to_analyze)
            if result:
                st.session_state['last_summary'] = result
                st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.success("Résumé automatique généré !")
                st.rerun()
    
    # Navigation avec session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    
    # CSS pour styliser la navigation Streamlit
    st.markdown("""
    <style>
    /* Centrer et espacer les colonnes */
    .st-emotion-cache-139jccg {
        width: auto !important;
        flex: none !important;
    }
    .st-emotion-cache-1permvm {
        display: flex !important;
        gap: 1rem !important;
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        min-width: 1rem !important;
        flex-flow: wrap !important;
        flex: 1 1 0% !important;
        align-items: stretch !important;
        overflow: visible !important;
        justify-content: start !important;
    }
    .st-emotion-cache-18kf3ut {
        display: flex !important;
        flex-direction: column !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 1rem !important;
        height: auto !important;
        align-content: center !important;
    }

        /* Styliser les boutons de navigation */
    .st-key-nav_newsletters button, .st-key-nav_home button, .st-key-nav_settings button, .st-key-nav_help button {
        background: transparent !important;
        border: none !important;
        color: #666 !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 4px !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    .st-key-nav_newsletters button:hover, .st-key-nav_home button:hover, .st-key-nav_settings button:hover, .st-key-nav_help button:hover {
        color: #667eea !important;
        background: #f8f9fa !important;
    }
    /* Bouton actif avec soulignement */
    .st-key-nav_newsletters button[kind="primary"], .st-key-nav_home button[kind="primary"], .st-key-nav_settings button[kind="primary"], .st-key-nav_help button[kind="primary"] {
        color: #667eea !important;
        text-decoration: underline !important;
        text-underline-offset: 4px !important;
        text-decoration-thickness: 2px !important;
    }
    
    .st-emotion-cache-1cl4umz {
        background-color: #667eea !important;
        border: 1px solid #667eea !important;
    }

    .st-emotion-cache-1cl4umz:hover, .st-emotion-cache-1cl4umz:focus-visible {
        background-color: #6366f1 !important;
        border-color: #6366f1 !important;
    }

    .st-emotion-cache-139jccg .st-emotion-cache-wfksaw {
        justify-content: flex-end !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
    
    # Actions rapides
    st.markdown("### <i class='fas fa-bolt'></i> Actions rapides", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Tester la newsletter", type="primary", use_container_width=True, icon=":material/play_arrow:"):
            if not newsletter_manager.get_newsletters():
                st.error("Aucune newsletter configurée. Allez dans l'onglet 'Newsletters' pour en ajouter.")
            else:
                with st.spinner("Test de la newsletter en cours..."):
                    # Récupérer la configuration utilisateur
                    user_data = newsletter_manager.load_user_data()
                    days_to_analyze = user_data.get('settings', {}).get('days_to_analyze', 7)
                    
                    
                    # Générer le résumé avec la configuration utilisateur
                    result = newsletter_manager.process_newsletters(days=days_to_analyze, send_email=True)
                    if result and result.strip():
                        st.session_state['last_summary'] = result
                        st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.success("Test de newsletter réussi ! Résumé généré et email envoyé.")
                        st.rerun()
                    else:
                        st.warning("Aucun contenu IA trouvé dans les newsletters pour la période sélectionnée. L'email n'a pas été envoyé.")
    
    with col2:
        if st.button("Tester l'envoi", type="secondary", use_container_width=True, icon=":material/send:"):
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
    
    # Dernier résumé
    if 'last_summary' in st.session_state:
        st.markdown("### <i class='fas fa-file-alt'></i> Dernier résumé généré", unsafe_allow_html=True)
        with st.expander("Voir le résumé", expanded=False):
            st.markdown(st.session_state['last_summary'])

def show_newsletters_page(newsletter_manager):
    """Page de gestion des newsletters"""
    
    newsletter_manager.render_newsletter_management()

def show_configuration_page():
    """Page de configuration"""
    
    # Configuration OpenAI
    st.markdown("### <i class='fas fa-cog'></i> Configuration OpenAI", unsafe_allow_html=True)
    
    # Test de la configuration
    if st.button("Tester la configuration", icon=":material/check_circle:"):
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
    st.markdown("### <i class='fas fa-key'></i> Token OAuth2", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Afficher le contenu de token.json", icon=":material/visibility:"):
            st.session_state['show_token'] = True
    
    with col2:
        if st.button("Masquer le token", icon=":material/visibility_off:"):
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
    st.markdown("### <i class='fas fa-info-circle'></i> Informations système", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"Python: {os.sys.version}")
        st.info(f"Streamlit: {st.__version__}")
    
    with col2:
        st.info(f"Authentification: {'Active' if st.session_state.get('authenticated') else 'Inactive'}")
        st.info(f"Gmail API: {'Connecté' if st.session_state.get('authenticated') else 'Non connecté'}")



def show_help_page():
    """Page d'aide"""
    
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

