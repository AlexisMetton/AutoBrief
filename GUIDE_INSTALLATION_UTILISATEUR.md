# Guide d'Installation Complet - AutoBrief

Ce guide vous accompagne étape par étape pour déployer votre propre instance d'AutoBrief.

## 🚀 Étape 1 : Fork du Repository

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

## 🔑 Étape 2 : Configuration Google Cloud

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

## 🚀 Étape 3 : Déploiement Streamlit Cloud

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

## 🔐 Étape 4 : Configuration des Secrets

### 4.1 Listes des secrets à créer

| Secret | Description | Où l'obtenir |
|--------|-------------|--------------|
| `OPENAI_API_KEY` | Clé API OpenAI | [platform.openai.com](https://platform.openai.com) |
| `SECRET_KEY` | Clé de chiffrement | [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md)  |
| `GIST_ID` | ID du Gist GitHub | [gist.github.com](https://gist.github.com) |
| `GIST_TOKEN` | Token GitHub | GitHub Settings > Developer settings |
| `GOOGLE_CREDENTIALS` | Credentials OAuth2 | Contenu du fichier `credentials.json` |
| `API_KEY` | Clé API pour GitHub Actions | [SECRET_KEY_GENERATOR.md](SECRET_KEY_GENERATOR.md) |

### 4.2 Configurer les Secrets GitHub
### 7.1 Activer GitHub Actions

1. Allez dans votre repository GitHub > Cliquez sur l'onglet **"Actions"** > Si GitHub Actions n'est pas activé, cliquez sur **"I understand my workflows, go ahead and enable them"**

2. Puis, allez dans **Settings > Secrets and variables > Actions**

3. Ajoutez ces secrets :

```
OPENAI_API_KEY = "sk-..."
SECRET_KEY = "votre-clé-secrète"
GOOGLE_CREDENTIALS = "contenu-json-des-credentials"
GIST_ID = "votre-gist-id"
GIST_TOKEN = "ghp_..."
API_KEY = "clé-api-aléatoire"
```

### 4.3 Configurer les Secrets Streamlit

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

## 📧 Étape 5 : Configuration Gmail

### 5.1 Première Connexion

1. Dans votre application Streamlit, cliquez sur **"Se connecter avec Google"**
2. Autorisez l'accès à Gmail
3. **Important** : Assurez-vous d'autoriser les permissions `gmail.readonly` et `gmail.send`

## 💾 Étape 6 : Configuration GitHub Gist

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

### 6.3 Ajouter les Secrets Gist

Dans les secrets Streamlit :

```
GIST_ID = "votre-gist-id"
GIST_TOKEN = "ghp_..."
```

## 🤖 Étape 7 : Configuration GitHub Actions

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

## 📧 Étape 8 : Configuration des Newsletters

### 8.1 Ajouter des Newsletters

1. Dans votre application Streamlit, allez dans **"Newsletters"**
2. Cliquez sur **"Ajouter une newsletter"**
3. Ajoutez les adresses email des newsletters à suivre
4. Configurez les paramètres :
   - **Fréquence** : hebdomadaire, mensuelle, etc.
   - **Jours d'analyse** : combien de jours d'emails analyser
   - **Email de notification** : où envoyer le résumé

### 8.3 Test

1. Cliquez sur **"Tester la newsletter"**
2. Vérifiez que vous recevez un email avec le résumé

## ✅ Vérification Finale

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

## 🆘 Dépannage

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

---

**🎉 Félicitations ! Votre AutoBrief est maintenant opérationnel !**
