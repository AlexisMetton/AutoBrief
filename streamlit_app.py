import streamlit as st
import os
from datetime import datetime, timedelta
from config import Config
from secure_auth import SecureAuth
from newsletter_manager import NewsletterManager
import json

# Configuration de la page
st.set_page_config(
    page_title="AutoBrief - Veille IA Automatisée",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

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
        with st.spinner("🔄 Génération automatique en cours..."):
            result = newsletter_manager.process_newsletters()
            if result:
                st.session_state['last_summary'] = result
                st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.success("✅ Résumé automatique généré !")
                st.rerun()
    
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>AutoBrief</h1>
        <p>Automatisez votre veille avec l'intelligence artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        # Authentification
        if not auth.authenticate_user():
            st.stop()
        
        # Menu utilisateur
        st.markdown(f"👤 **Connecté:** {st.session_state.get('user_email', 'Utilisateur')}")
        
        if st.button("🚪 Se déconnecter", type="secondary"):
            auth.logout()
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "📋 Menu",
            ["🏠 Accueil", "📧 Newsletters", "⚙️ Configuration", "📊 Résultats", "🤖 Scheduler", "❓ Aide"],
            index=0
        )
    
    # Contenu principal selon la page sélectionnée
    if page == "🏠 Accueil":
        show_home_page(newsletter_manager)
    elif page == "📧 Newsletters":
        show_newsletters_page(newsletter_manager)
    elif page == "⚙️ Configuration":
        show_configuration_page()
    elif page == "📊 Résultats":
        show_results_page(newsletter_manager)
    elif page == "🤖 Scheduler":
        show_scheduler_page(newsletter_manager)
    elif page == "❓ Aide":
        show_help_page()

def show_home_page(newsletter_manager):
    """Page d'accueil avec vue d'ensemble"""
    st.markdown("## 🏠 Tableau de bord")
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📧 Newsletters",
            value=len(newsletter_manager.get_newsletters()),
            delta=None
        )
    
    with col2:
        st.metric(
            label="📅 Dernière exécution",
            value="Jamais" if 'last_run' not in st.session_state else st.session_state['last_run'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="📊 Emails traités",
            value=st.session_state.get('processed_emails', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            label="🤖 Status IA",
            value="✅ Actif" if st.session_state.get('openai_configured', False) else "❌ Inactif",
            delta=None
        )
    
    # Actions rapides
    st.markdown("### 🚀 Actions rapides")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Générer le résumé maintenant", type="primary", use_container_width=True):
            if not newsletter_manager.get_newsletters():
                st.error("❌ Aucune newsletter configurée. Allez dans l'onglet 'Newsletters' pour en ajouter.")
            else:
                with st.spinner("🔄 Génération du résumé en cours..."):
                    result = newsletter_manager.process_newsletters()
                    if result:
                        st.session_state['last_summary'] = result
                        st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.success("✅ Résumé généré avec succès !")
                        st.rerun()
                    else:
                        st.error("❌ Aucun contenu trouvé pour la période sélectionnée")
    
    with col2:
        if st.button("📧 Gérer les newsletters", use_container_width=True):
            st.session_state['page'] = "📧 Newsletters"
            st.rerun()
    
    # Dernier résumé
    if 'last_summary' in st.session_state:
        st.markdown("### 📄 Dernier résumé généré")
        with st.expander("👀 Voir le résumé", expanded=False):
            st.markdown(st.session_state['last_summary'])

def show_newsletters_page(newsletter_manager):
    """Page de gestion des newsletters"""
    st.markdown("## 📧 Gestion des Newsletters")
    
    newsletter_manager.render_newsletter_management()
    
    # Configuration de la période
    st.markdown("### ⏰ Configuration de la période")
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
    st.markdown("## ⚙️ Configuration")
    
    # Configuration OpenAI
    st.markdown("### 🤖 Configuration OpenAI")
    
    if st.session_state.get('openai_configured', False):
        st.success("✅ Clé OpenAI configurée")
    else:
        st.warning("⚠️ Clé OpenAI non configurée")
    
    # Test de la configuration
    if st.button("🧪 Tester la configuration"):
        with st.spinner("Test en cours..."):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=Config.get_openai_key())
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                st.success("✅ Configuration OpenAI fonctionnelle")
                st.session_state['openai_configured'] = True
            except Exception as e:
                st.error(f"❌ Erreur de configuration: {e}")
                st.session_state['openai_configured'] = False
    
    # Informations système
    st.markdown("### 📊 Informations système")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"🐍 Python: {os.sys.version}")
        st.info(f"📦 Streamlit: {st.__version__}")
    
    with col2:
        st.info(f"🔐 Authentification: {'✅ Active' if st.session_state.get('authenticated') else '❌ Inactive'}")
        st.info(f"📧 Gmail API: {'✅ Connecté' if st.session_state.get('authenticated') else '❌ Non connecté'}")

def show_results_page(newsletter_manager):
    """Page des résultats"""
    st.markdown("## 📊 Résultats et Historique")
    
    if 'last_summary' not in st.session_state:
        st.info("ℹ️ Aucun résumé généré. Allez dans l'onglet 'Accueil' pour générer votre premier résumé.")
        return
    
    # Dernier résumé
    st.markdown("### 📄 Dernier résumé généré")
    st.markdown(f"**Date:** {st.session_state.get('last_run', 'Inconnue')}")
    
    # Options d'export
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Télécharger en TXT"):
            st.download_button(
                label="📄 Télécharger le résumé",
                data=st.session_state['last_summary'],
                file_name=f"veille_ia_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    with col2:
        if st.button("📧 Envoyer par email"):
            st.info("💡 Fonctionnalité d'envoi par email à venir")
    
    with col3:
        if st.button("🔄 Régénérer"):
            with st.spinner("🔄 Régénération en cours..."):
                result = newsletter_manager.process_newsletters()
                if result:
                    st.session_state['last_summary'] = result
                    st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.success("✅ Résumé régénéré !")
                    st.rerun()
    
    # Affichage du résumé
    st.markdown("---")
    st.markdown(st.session_state['last_summary'])

def show_scheduler_page(newsletter_manager):
    """Page de gestion du scheduler"""
    st.markdown("## 🤖 Gestion du Scheduler")
    
    st.info("""
    📋 **Fonctionnement du scheduler automatique :**
    
    - ✅ **Vérification quotidienne** : GitHub Actions exécute le scheduler tous les jours à 09:00 UTC
    - ✅ **Génération automatique** : Crée les résumés selon votre planification
    - ✅ **Interface Streamlit** : Application toujours disponible sur Streamlit Cloud
    - ✅ **Persistance** : Sauvegarde l'historique des exécutions
    - ✅ **100% Gratuit** : GitHub Actions + Streamlit Cloud
    """)
    
    # Statut du scheduler
    st.markdown("### 📊 Statut du Scheduler")
    
    settings = newsletter_manager.get_user_settings()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="🔄 Génération automatique",
            value="✅ Activée" if settings.get('auto_send', False) else "❌ Désactivée"
        )
    
    with col2:
        st.metric(
            label="📅 Dernière exécution",
            value=settings.get('last_run', 'Jamais')
        )
    
    # Test manuel du scheduler
    st.markdown("### 🧪 Test du Scheduler")
    
    if st.button("🚀 Lancer le scheduler maintenant", type="primary"):
        with st.spinner("🔄 Exécution du scheduler..."):
            try:
                # Simuler l'exécution du scheduler
                if newsletter_manager.should_run_automatically():
                    result = newsletter_manager.process_newsletters()
                    if result:
                        st.success("✅ Scheduler exécuté avec succès !")
                        st.session_state['last_summary'] = result
                        st.session_state['last_run'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    else:
                        st.warning("⚠️ Aucun contenu trouvé pour la période sélectionnée")
                else:
                    st.info("ℹ️ Pas encore l'heure d'exécution selon votre planification")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'exécution: {e}")
    
    # Configuration GitHub Actions
    st.markdown("### 🚀 Configuration GitHub Actions")
    
    st.markdown("""
    **Pour activer le scheduler automatique :**
    
    1. **Fork ce repository** : Cliquez sur "Fork" en haut à droite
    2. **Configurer les secrets** : Dans Settings > Secrets and variables > Actions
    3. **Activer GitHub Actions** : Le workflow se lance automatiquement
    4. **Vérifier les exécutions** : Dans l'onglet "Actions" de votre repository
    """)
    
    # Secrets GitHub
    with st.expander("📋 Secrets GitHub à configurer"):
        st.code("""
# Dans GitHub > Settings > Secrets and variables > Actions
# Ajouter ces secrets :

OPENAI_API_KEY=sk-votre-cle-openai
SECRET_KEY=votre-cle-secrete-32-caracteres
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"votre-projet",...}
        """, language="bash")
        
        st.info("""
        💡 **Comment obtenir les secrets :**
        
        - **OPENAI_API_KEY** : [platform.openai.com](https://platform.openai.com) > API Keys
        - **SECRET_KEY** : Générez une clé de 32 caractères aléatoires
        - **GOOGLE_CREDENTIALS** : Google Cloud Console > Credentials > Télécharger JSON
        """)
    
    # Workflow GitHub Actions
    with st.expander("🔧 Workflow GitHub Actions"):
        st.code("""
# .github/workflows/auto-brief-scheduler.yml
name: AutoBrief Scheduler

on:
  schedule:
    - cron: '0 9 * * *'  # Tous les jours à 09:00 UTC
  workflow_dispatch:     # Déclenchement manuel

jobs:
  auto-brief:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run scheduler
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
        GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
      run: python scheduler.py
        """, language="yaml")

def show_help_page():
    """Page d'aide"""
    st.markdown("## ❓ Aide et Support")
    
    st.markdown("""
    ### 🚀 Comment utiliser AutoBrief
    
    **1. Configuration initiale:**
    - Assurez-vous d'avoir un fichier `.env` avec vos clés API
    - Placez le fichier `credentials.json` dans le répertoire du projet
    
    **2. Ajout des newsletters:**
    - Allez dans l'onglet "📧 Newsletters"
    - Ajoutez les adresses email qui vous envoient des newsletters
    - Configurez la période d'analyse
    
    **3. Génération du résumé:**
    - Cliquez sur "🔄 Générer le résumé maintenant"
    - Le système analysera vos emails et extraira les actualités IA
    - Le résumé sera disponible dans l'onglet "📊 Résultats"
    
    ### 🔧 Configuration requise
    
    **Variables d'environnement (.env):**
    ```
    OPENAI_API_KEY=votre_clé_openai
    SECRET_KEY=votre_clé_secrète
    ```
    
    **Fichiers requis:**
    - `credentials.json` (Google OAuth)
    - `.env` (clés API)
    
    ### 🛡️ Sécurité
    
    - ✅ Authentification OAuth2 Google
    - ✅ Chiffrement des tokens
    - ✅ Variables d'environnement sécurisées
    - ✅ Sessions chiffrées
    - ✅ Permissions limitées (lecture seule Gmail)
    
    ### 📞 Support
    
    Pour toute question ou problème, consultez la documentation ou contactez le support.
    """)

if __name__ == "__main__":
    main()

