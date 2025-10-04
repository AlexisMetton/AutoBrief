# 📧 AutoBrief - Résumé Automatique de Newsletters

AutoBrief est une application Streamlit qui génère automatiquement des résumés intelligents de vos newsletters Gmail grâce à l'IA, avec planification automatique via GitHub Actions.

## ✨ Fonctionnalités

- 🔐 **Authentification Google** - Connexion sécurisée avec votre compte Gmail
- 📧 **Analyse IA** - Résumé intelligent de vos newsletters avec OpenAI
- ⏰ **Planification automatique** - Envoi automatique selon votre planning
- 💾 **Persistance des données** - Sauvegarde automatique dans GitHub Gist
- 🚀 **Déploiement Streamlit Cloud** - Application hébergée gratuitement
- 🤖 **Automatisation GitHub Actions** - Planification et exécution automatiques

## 🚀 Installation Rapide

### 1. Fork du Repository

1. Cliquez sur **"Fork"** en haut à droite de ce repository
2. Votre fork sera disponible à `https://github.com/VOTRE-USERNAME/AutoBrief`

### 2. Déploiement Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez-vous avec votre compte GitHub
3. Cliquez sur **"New app"**
4. Sélectionnez votre repository `AutoBrief`
5. Cliquez sur **"Deploy!"**

### 3. Configuration des Secrets

Dans Streamlit Cloud, ajoutez ces secrets :

```
OPENAI_API_KEY = "sk-..."
SECRET_KEY = "votre-clé-secrète-32-caractères"
GIST_ID = "votre-gist-id"
GIST_TOKEN = "ghp_..."
GOOGLE_CREDENTIALS = {
  "token": "...",
  "refresh_token": "...",
  "client_id": "...",
  "client_secret": "...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
  ]
}
```

## 🔧 Configuration Google OAuth

### 1. Créer un Projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'**API Gmail**

### 2. Configurer OAuth

1. Allez dans **"APIs & Services" > "Credentials"**
2. Cliquez sur **"Create Credentials" > "OAuth client ID"**
3. Sélectionnez **"Desktop Application"**
4. Téléchargez le fichier JSON et placez-le dans votre projet

### 3. Obtenir les Credentials OAuth2

1. Lancez votre application Streamlit
2. Connectez-vous avec Google
3. Allez dans **"🤖 Scheduler"**
4. Cliquez sur **"🔑 Afficher credentials OAuth2"**
5. Copiez le contenu JSON dans le secret `GOOGLE_CREDENTIALS`

## 💾 Configuration GitHub Gist

### 1. Créer un Gist Privé

1. Allez sur [gist.github.com](https://gist.github.com)
2. Créez un nouveau Gist **privé** (pas public !)
3. Nommez le fichier `user_data.json`
4. Ajoutez ce contenu :
```json
{}
```
5. Cliquez sur **"Create secret gist"**
6. Copiez l'ID du Gist (dans l'URL)

### 2. Créer un Token GitHub

1. Allez dans **GitHub > Settings > Developer settings > Personal access tokens**
2. Cliquez sur **"Generate new token (classic)"**
3. Sélectionnez la scope **"gist"**
4. Copiez le token

### 3. Configurer les Secrets

Ajoutez ces secrets dans Streamlit Cloud :
- `GIST_ID` : L'ID de votre Gist
- `GIST_TOKEN` : Votre token GitHub

## 🤖 Configuration GitHub Actions

### 1. Activer GitHub Actions

1. Allez dans votre repository GitHub
2. Cliquez sur l'onglet **"Actions"**
3. Activez GitHub Actions si ce n'est pas déjà fait

### 2. Configurer les Secrets GitHub

Dans **Settings > Secrets and variables > Actions**, ajoutez :

```
OPENAI_API_KEY = "sk-..."
SECRET_KEY = "votre-clé-secrète"
GOOGLE_CREDENTIALS = "contenu-json-des-credentials"
GIST_ID = "votre-gist-id"
GIST_TOKEN = "ghp_..."
API_KEY = "clé-api-aléatoire"
```

### 3. Planification

Le scheduler s'exécute automatiquement toutes les heures et vérifie votre planification configurée dans l'application.

## 📖 Utilisation

### 1. Configuration des Newsletters

1. Connectez-vous à votre application Streamlit
2. Allez dans **"📧 Newsletters"**
3. Ajoutez les adresses email des newsletters à suivre
4. Configurez les paramètres (fréquence, jours d'analyse, etc.)

### 2. Planification

1. Allez dans **"🤖 Scheduler"**
2. Activez l'**envoi automatique**
3. Configurez le jour et l'heure d'envoi
4. Laissez GitHub Actions gérer le reste !

### 3. Test

Utilisez le bouton **"🧪 Tester la newsletter"** pour générer un résumé immédiatement.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   GitHub Actions │    │   GitHub Gist   │
│   Application   │◄──►│   Scheduler      │◄──►│   Persistence   │
│                 │    │                  │    │                 │
│ • Interface     │    │ • Planification  │    │ • Données       │
│ • Configuration │    │ • Génération IA  │    │ • Utilisateurs  │
│ • Authentification│   │ • Envoi emails  │    │ • Settings      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 Développement Local

### Installation

```bash
git clone https://github.com/VOTRE-USERNAME/AutoBrief.git
cd AutoBrief
pip install -r requirements.txt
```

### Configuration

1. Copiez `env.example` vers `.env`
2. Remplissez vos clés API
3. Lancez avec `streamlit run streamlit_app.py`

### Test du Scheduler

```bash
python scheduler.py
```

## 📋 Secrets Requis

| Secret | Description | Où l'obtenir |
|--------|-------------|--------------|
| `OPENAI_API_KEY` | Clé API OpenAI | [platform.openai.com](https://platform.openai.com) |
| `SECRET_KEY` | Clé de chiffrement | Générateur dans l'app |
| `GIST_ID` | ID du Gist GitHub | [gist.github.com](https://gist.github.com) |
| `GIST_TOKEN` | Token GitHub | GitHub Settings > Developer settings |
| `GOOGLE_CREDENTIALS` | Credentials OAuth2 | Via l'application Streamlit |
| `API_KEY` | Clé API pour GitHub Actions | Clé aléatoire |

## 🔒 Sécurité

### ⚠️ **IMPORTANT : Sécurité Gist Obligatoire**

**NE JAMAIS utiliser un Gist public !** Cela exposerait les tokens OAuth2 de tous les utilisateurs.

- ✅ **Gist secret** - Non listé publiquement
- ✅ **Token GitHub** - Authentification requise pour lire/écrire
- ✅ **Chiffrement** - Tokens OAuth2 chiffrés dans le Gist (nouveau)
- ❌ **Gist public** - DANGEREUX ! Expose tous les tokens
- ⚠️ **Gist secret sans token** - Accessible via URL directe (non sécurisé)
- 🚨 **Contenu visible** - Même secret, le contenu est lisible si URL connue
- 🚫 **Gist invisible** - Impossible sur GitHub (limitation de la plateforme)

### 🛡️ **Bonnes pratiques :**

1. **Gist secret + Token** - Gist "secret" + Token GitHub obligatoire
2. **Token GitHub sécurisé** - Utilisez un token avec scope "gist" uniquement
3. **Révoquer les tokens** - Si compromis, révoquez immédiatement
4. **Surveillance** - Vérifiez régulièrement l'accès au Gist
5. **Ne pas partager l'URL** - L'URL du Gist doit rester confidentielle
6. **Chiffrement des données** - Les tokens OAuth2 sont chiffrés dans le Gist (nouveau)
7. **Accès limité** - Seuls les utilisateurs autorisés peuvent lire/écrire

### 🚫 **Limitations GitHub Gist :**

**GitHub Gist ne permet PAS :**
- ❌ **Gist privé** (n'existe pas)
- ❌ **Gist invisible** (n'existe pas)
- ❌ **Permissions granulaires** (n'existe pas)
- ❌ **Authentification utilisateur** (n'existe pas)

### 🔄 **Alternatives pour vraie invisibilité :**

| Solution | Invisibilité | Coût | Complexité |
|----------|-------------|------|------------|
| **GitHub Gist** | ⚠️ Semi-secret | Gratuit | Simple |
| **Base de données** | ✅ Privé | Payant | Complexe |
| **Fichiers locaux** | ✅ Privé | Gratuit | Limité |
| **Cloud Storage** | ✅ Privé | Payant | Moyen |

**Recommandation :** GitHub Gist + Chiffrement = **Sécurité maximale possible** 🔒

## 🆘 Support

- 📖 **Documentation complète** : [GUIDE_INSTALLATION_UTILISATEUR.md](GUIDE_INSTALLATION_UTILISATEUR.md)
- 🔑 **Génération de clé** : [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md)
- 🐛 **Issues** : [GitHub Issues](https://github.com/VOTRE-USERNAME/AutoBrief/issues)

## 📄 Licence

MIT License - Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

**🎉 Félicitations ! Votre AutoBrief est maintenant opérationnel !**