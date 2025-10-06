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
            st.markdown(st.session_state['last_summary'], unsafe_allow_html=True)

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
    
    st.markdown("## <i class='fas fa-question-circle'></i> Guide d'Installation Complet", unsafe_allow_html=True)
    
    st.markdown("""
    Ce guide vous accompagne étape par étape pour déployer votre propre instance d'AutoBrief.
    """)
    
    # Étape 1 : Fork du Repository
    with st.expander("🚀 Étape 1 : Fork du Repository", expanded=False):
        st.markdown("""
        ### 1.1 Forker le Repository
        
        1. Allez sur [github.com/AlexisMetton/AutoBrief](https://github.com/AlexisMetton/AutoBrief)
        2. Cliquez sur le bouton **"Fork"** en haut à droite
        3. Sélectionnez votre compte GitHub comme destination
        4. Votre fork sera disponible à `https://github.com/VOTRE-USERNAME/AutoBrief`
        
        ### 1.2 Cloner Localement (Optionnel)
        
        ```bash
        git clone https://github.com/VOTRE-USERNAME/AutoBrief.git
        cd AutoBrief
        ```
        """)
    
    # Étape 2 : Configuration Google Cloud
    with st.expander("🔑 Étape 2 : Configuration Google Cloud", expanded=False):
        st.markdown("""
        ### 2.1 Créer un Projet Google Cloud
        
        1. Allez sur [console.cloud.google.com](https://console.cloud.google.com)
        2. Cliquez sur **"Select a project"** puis **"New Project"**
        3. Nommez votre projet (ex: "autobrief-app")
        4. Cliquez sur **"Create"**
        
        ### 2.2 Activer l'API Gmail
        
        1. Dans votre projet, allez dans **"APIs & Services" > "Library"**
        2. Recherchez **"Gmail API"**
        3. Cliquez sur **"Enable"**
        
        ### 2.3 Configurer OAuth
        
        1. Allez dans **"APIs & Services" > "Credentials"**
        2. Cliquez sur **"+ Create Credentials" > "OAuth client ID"**
        3. Si c'est votre première fois, configurez l'écran de consentement :
           - Choisissez **"External"**
           - Remplissez les champs obligatoires (nom, email, etc.)
        4. Créez les credentials OAuth :
           - **Application type** : **"Desktop Application"**
           - **Name** : "AutoBrief"
        5. Cliquez sur **"Create"**
        6. **Important** : Notez l'URI de redirection : `urn:ietf:wg:oauth:2.0:oob`
        
        ### 2.4 Télécharger les Credentials
        
        1. Dans la liste des credentials, cliquez sur votre OAuth client
        2. Cliquez sur **"Download JSON"**
        3. Renommez le fichier en `credentials.json`
        4. Placez-le dans votre projet AutoBrief
        """)
    
    # Étape 3 : Déploiement Streamlit Cloud
    with st.expander("🚀 Étape 3 : Déploiement Streamlit Cloud", expanded=False):
        st.markdown("""
        ### 3.1 Déployer l'Application
        
        1. Allez sur [share.streamlit.io](https://share.streamlit.io)
        2. Connectez-vous avec votre compte GitHub
        3. Cliquez sur **"New app"**
        4. Remplissez :
           - **Repository** : `VOTRE-USERNAME/AutoBrief`
           - **Branch** : `main`
           - **Main file path** : `streamlit_app.py`
        5. Cliquez sur **"Deploy!"**
        
        ### 3.2 Attendre le Déploiement
        
        L'application va se déployer automatiquement. Cela peut prendre 2-5 minutes.
        """)
    
    # Étape 4 : Configuration des Secrets
    with st.expander("🔐 Étape 4 : Configuration des Secrets", expanded=True):
        st.markdown("""
        ### 4.1 Listes des secrets à créer
        
        | Secret | Description | Où l'obtenir |
        |--------|-------------|--------------|
        | `OPENAI_API_KEY` | Clé API OpenAI | [platform.openai.com](https://platform.openai.com) |
        | `SECRET_KEY` | Clé de chiffrement | [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md)  |
        | `GIST_ID` | ID du Gist GitHub | [gist.github.com](https://gist.github.com) |
        | `GIST_TOKEN` | Token GitHub | GitHub Settings > Developer settings |
        | `GOOGLE_CREDENTIALS` | Credentials OAuth2 | Contenu du fichier `credentials.json` |
        | `API_KEY` | Clé API pour GitHub Actions | [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md) |
        
        ### 4.2 Configurer les Secrets Streamlit
        
        Dans votre application Streamlit déployée :
        
        1. Allez dans **"Settings" > "Secrets"**
        2. Ajoutez ces secrets :
        
        ```
        OPENAI_API_KEY = "sk-..."
        SECRET_KEY = "votre-clé-secrète-32-caractères"
        GIST_ID = "votre-gist-id"
        GIST_TOKEN = "ghp_..."
        GOOGLE_CREDENTIALS = "contenu-json-complet-des-credentials"
        API_KEY = "clé-api-aléatoire-pour-sécurité"
        ```
        """)
    
    # Étape 5 : Configuration Gmail
    with st.expander("📧 Étape 5 : Configuration Gmail", expanded=False):
        st.markdown("""
        ### 5.1 Première Connexion
        
        1. Dans votre application Streamlit, cliquez sur **"Se connecter avec Google"**
        2. Autorisez l'accès à Gmail
        3. **Important** : Assurez-vous d'autoriser les permissions `gmail.readonly` et `gmail.send`
        """)
    
    # Étape 6 : Configuration GitHub Gist
    with st.expander("💾 Étape 6 : Configuration GitHub Gist", expanded=False):
        st.markdown("""
        ### 6.1 Créer un Gist Secret
        
        1. Allez sur [gist.github.com](https://gist.github.com)
        2. Créez un nouveau Gist **secret** (pas public !)
        3. **Filename** : `user_data.json`
        4. **Content** :
        ```json
        {}
        ```
        5. Cliquez sur **"Create secret gist"**
        6. Copiez l'ID du Gist (dans l'URL : `gist.github.com/VOTRE-USERNAME/ID-DU-GIST`)
        
        ### 6.2 Créer un Token GitHub
        
        1. Allez dans **GitHub > Settings > Developer settings > Personal access tokens**
        2. Cliquez sur **"Generate new token (classic)"**
        3. Donnez un nom au token (ex: "AutoBrief Gist")
        4. Sélectionnez la scope **"gist"**
        5. Cliquez sur **"Generate token"**
        6. **Important** : Copiez le token immédiatement (commence par `ghp_`)
        """)
    
    # Étape 7 : Configuration GitHub Actions
    with st.expander("🤖 Étape 7 : Configuration GitHub Actions", expanded=False):
        st.markdown("""
        ### 7.1 Activer GitHub Actions
        
        1. Allez dans votre repository GitHub
        2. Cliquez sur l'onglet **"Actions"**
        3. Si GitHub Actions n'est pas activé, cliquez sur **"I understand my workflows, go ahead and enable them"**
        
        ### 7.2 Configurer les Secrets GitHub
        
        Dans votre repository GitHub :
        
        1. Allez dans **"Settings" > "Secrets and variables" > "Actions"**
        2. Cliquez sur **"New repository secret"**
        3. Ajoutez ces secrets :
        
        ```
        OPENAI_API_KEY = "sk-..."
        SECRET_KEY = "votre-clé-secrète"
        GOOGLE_CREDENTIALS = "contenu-json-complet-des-credentials"
        GIST_ID = "votre-gist-id"
        GIST_TOKEN = "ghp_..."
        API_KEY = "clé-api-aléatoire-pour-sécurité"
        ```
        
        ### 7.3 Tester le Workflow
        
        1. Allez dans l'onglet **"Actions"**
        2. Cliquez sur **"AutoBrief Scheduler"**
        3. Cliquez sur **"Run workflow"**
        4. Cliquez sur le bouton vert **"Run workflow"**
        """)
    
    # Étape 8 : Configuration des Newsletters
    with st.expander("📧 Étape 8 : Configuration des Newsletters", expanded=False):
        st.markdown("""
        ### 8.1 Ajouter des Newsletters
        
        1. Dans votre application Streamlit, allez dans **"Newsletters"**
        2. Cliquez sur **"Ajouter une newsletter"**
        3. Ajoutez les adresses email des newsletters à suivre
        4. Configurez les paramètres :
           - **Fréquence** : hebdomadaire, mensuelle, etc.
           - **Jours d'analyse** : combien de jours d'emails analyser (max 7)
           - **Email de notification** : où envoyer le résumé
        
        ### 8.2 Test
        
        1. Cliquez sur **"Tester la newsletter"**
        2. Vérifiez que vous recevez un email avec le résumé
        """)
    
    # Vérification Finale
    with st.expander("✅ Vérification Finale", expanded=False):
        st.markdown("""
        ### Checklist de Validation
        
        - [ ] Application Streamlit déployée et accessible
        - [ ] Connexion Google fonctionnelle
        - [ ] Secrets Streamlit configurés
        - [ ] Gist GitHub créé et accessible
        - [ ] Secrets GitHub Actions configurés
        - [ ] Workflow GitHub Actions s'exécute sans erreur
        - [ ] Newsletters configurées
        - [ ] Test de newsletter réussi
        - [ ] Planification configurée
        """)
    
    # Dépannage
    with st.expander("🆘 Dépannage", expanded=False):
        st.markdown("""
        ### Problèmes Courants
        
        **❌ Erreur "redirect_uri_mismatch"**
        - Vérifiez que vous utilisez un client "Desktop Application"
        
        **❌ Erreur "Gmail API has not been used"**
        - Activez l'API Gmail dans Google Cloud Console
        
        **❌ Erreur "401 Unauthorized" sur le Gist**
        - Vérifiez que votre Gist existe
        - Vérifiez que votre token GitHub a la scope "gist"
        
        **❌ GitHub Actions échoue**
        - Vérifiez que tous les secrets GitHub sont configurés
        - Vérifiez les logs dans l'onglet "Actions"
        """)
    
    st.markdown("---")
    st.success("🎉 **Félicitations ! Votre AutoBrief est maintenant opérationnel !**")

if __name__ == "__main__":
    main()

