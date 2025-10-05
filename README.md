# AutoBrief - Résumé Automatique de Newsletters

AutoBrief est une application Streamlit qui génère automatiquement des résumés intelligents de vos newsletters Gmail grâce à l'IA, avec planification automatique via GitHub Actions.

## ✨ Fonctionnalités

- **Authentification Google** - Connexion sécurisée avec votre compte Gmail
- **Analyse IA** - Résumé intelligent de vos newsletters avec OpenAI
- **Planification automatique** - Envoi automatique selon votre planning
- **Persistance des données** - Sauvegarde automatique dans GitHub Gist
- **Déploiement Streamlit Cloud** - Application hébergée gratuitement
- **Automatisation GitHub Actions** - Planification et exécution automatiques

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
GOOGLE_CREDENTIALS = "contenu-json-des-credentials"
API_KEY = "clé-api-aléatoire"
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

**Note :** Après la première connexion, vos tokens OAuth2 seront automatiquement sauvegardés dans le Gist pour l'automatisation.

### 3. Obtenir les Credentials OAuth2

1. Lancez votre application Streamlit
2. Connectez-vous avec Google

## 🤖 Automatisation

### GitHub Actions

Le scheduler GitHub Actions s'exécute automatiquement toutes les heures et vérifie si un résumé doit être généré selon votre planning configuré.

**Fonctionnalités automatiques :**
- **Authentification automatique** → Tokens OAuth2 sauvegardés dans le Gist
- **Génération IA automatique** → Résumés créés sans intervention
- **Envoi d'email automatique** → Notifications envoyées selon le planning
- **Multi-utilisateurs** → Chaque utilisateur a ses propres credentials

### Configuration du Planning

Dans l'interface Streamlit, vous pouvez configurer :
- **Fréquence** : Quotidien, Hebdomadaire, Mensuel
- **Jour** : Pour les planifications hebdomadaires/mensuelles
- **Heure** : Heure d'exécution
- **Email de notification** : Adresse pour recevoir les résumés

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
2. Allez dans **"Newsletters"**
3. Ajoutez les adresses email des newsletters à suivre
4. Configurez les paramètres (fréquence, jours d'analyse, etc.)

### 3. Test

Utilisez le bouton **"Tester la newsletter"** pour générer un résumé immédiatement.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   GitHub Actions │    │   GitHub Gist   │
│   Application   │◄──►│   Scheduler      │◄──►│   Persistence   │
│                 │    │                  │    │                 │
│ • Interface     │    │ • Planification  │    │ • Données       │
│ • Configuration │    │ • Filtrage       │    │ • Utilisateurs  │
│ • Authentification│   │ • Nettoyage     │    │ • Settings      │
│ • Test newsletter│    │ • Génération IA │    │ • Credentials   │
│ • Filtrage promo│    │ • Envoi emails   │    │ • Chiffrement   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gmail API     │    │   OpenAI API     │    │   GitHub API    │
│                 │    │                  │    │                 │
│ • Lecture       │    │ • GPT-3.5-turbo  │    │ • Gist access   │
│ • Filtrage      │    │ • Résumé IA      │    │ • Token auth    │
│ • Envoi emails  │    │ • HTML généré    │    │ • Données crypt │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Secrets Requis

| Secret | Description | Où l'obtenir |
|--------|-------------|--------------|
| `OPENAI_API_KEY` | Clé API OpenAI | [platform.openai.com](https://platform.openai.com) |
| `SECRET_KEY` | Clé de chiffrement | [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md)  |
| `GIST_ID` | ID du Gist GitHub | [gist.github.com](https://gist.github.com) |
| `GIST_TOKEN` | Token GitHub | GitHub Settings > Developer settings |
| `GOOGLE_CREDENTIALS` | Credentials OAuth2 | Contenu du fichier `credentials.json` |
| `API_KEY` | Clé API pour GitHub Actions | [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md) |

## 🆘 Support

- 📖 **Documentation complète** : [GUIDE_INSTALLATION_UTILISATEUR.md](GUIDE_INSTALLATION_UTILISATEUR.md)
- 🔑 **Génération de clé** : [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md)

## 📄 Licence

MIT License - Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

**🎉 Félicitations ! Votre AutoBrief est maintenant opérationnel !**