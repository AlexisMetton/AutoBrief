# AutoBrief - Veille Automatisée

> **Automatisez votre veille en intelligence artificielle en analysant vos newsletters et en générant des résumés personnalisés.**

## ✨ Fonctionnalités

- 🔐 **Authentification sécurisée** avec Google OAuth2
- 📧 **Gestion des newsletters** - Ajoutez facilement vos sources
- 🤖 **IA intégrée** - Extraction automatique des actualités
- 🔒 **Sécurité maximale** - Chiffrement des données sensibles
- 📱 **Interface intuitive** - Accessible à tous les utilisateurs
- 📊 **Résumés personnalisés** - Contenu adapté à vos besoins

## 🚀 Installation Ultra-Simple

### **Option 1 : Déploiement Cloud (RECOMMANDÉ)**
1. **Fork** ce repository sur GitHub
2. **Déployez** sur [Streamlit Cloud](https://share.streamlit.io)
3. **Configurez** vos clés API dans les secrets
4. **C'est tout !** Votre AutoBrief est prêt

📖 **Guide complet** : [GUIDE_INSTALLATION_UTILISATEUR.md](GUIDE_INSTALLATION_UTILISATEUR.md)

### **Option 2 : Installation locale**
```bash
# Cloner le projet
git clone <votre-repo>
cd AutoBrief

# Créer l'environnement virtuel
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp env.example .env
# Éditer .env avec vos clés API

# Lancement
streamlit run streamlit_app.py
```

## 🎯 **Démarrage Rapide**

### **1. Fork le projet**
[![Fork](https://img.shields.io/badge/Fork-AutoBrief-blue?style=for-the-badge&logo=github)](https://github.com/votre-repo/AutoBrief/fork)

### **2. Déployer sur Streamlit**
[![Deploy](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-green?style=for-the-badge&logo=streamlit)](https://share.streamlit.io)

### **3. Configurer les secrets**
```toml
[secrets]
OPENAI_API_KEY = "sk-votre_cle_ici"
SECRET_KEY = "votre_cle_secrete_32_caracteres"
GOOGLE_CREDENTIALS = '{"type":"service_account","project_id":"votre-projet","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
```

## 🛡️ Sécurité

### Mesures de sécurité intégrées :
- ✅ **Chiffrement des tokens** - Tous les tokens sont chiffrés
- ✅ **Variables d'environnement** - Aucune clé en dur
- ✅ **Sessions sécurisées** - Gestion des sessions chiffrées
- ✅ **Permissions limitées** - Accès lecture seule Gmail
- ✅ **Validation des entrées** - Protection contre les injections

### Fichiers sensibles (automatiquement ignorés) :
- `.env` - Variables d'environnement
- `credentials.json` - Identifiants Google (stockés dans les secrets)

## 📖 Utilisation

### Interface utilisateur
1. **Accueil** - Vue d'ensemble et actions rapides
2. **Newsletters** - Gestion de vos sources d'information
3. **Configuration** - Paramètres et tests
4. **Résultats** - Historique et téléchargement
5. **Aide** - Documentation et support

### Workflow typique
1. Connectez-vous avec votre compte Google
2. Ajoutez les adresses email de vos newsletters
3. Configurez la période d'analyse
4. Générez votre résumé automatiquement
5. Téléchargez ou consultez les résultats

## 🔧 Configuration requise

### Variables d'environnement
```env
# Obligatoires
OPENAI_API_KEY=sk-...
SECRET_KEY=...

# Optionnelles
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Déploiement en production
1. **Streamlit Cloud** (gratuit) :
   - Connectez votre repo GitHub
   - Configurez les secrets dans l'interface
   - Déployez automatiquement

## 🤝 Support

### Problèmes courants
- **Erreur d'authentification** : Vérifiez `GOOGLE_CREDENTIALS` dans les secrets
- **Clé OpenAI invalide** : Vérifiez votre clé dans les secrets
- **Aucun email trouvé** : Vérifiez les adresses des newsletters
- **Erreur 400 redirect_uri_mismatch** : Vérifiez les URLs de redirection dans Google Cloud Console

### Logs et débogage
Les erreurs sont affichées dans l'interface. Pour plus de détails, consultez la console.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🔄 Mises à jour

Pour mettre à jour AutoBrief :
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

**AutoBrief** - Automatisez votre veille en toute sécurité ! 🚀