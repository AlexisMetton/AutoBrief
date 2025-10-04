# 📚 Guide d'Installation Complet - AutoBrief

Ce guide vous accompagne étape par étape pour déployer votre propre instance d'AutoBrief.

## 🎯 Vue d'ensemble

AutoBrief est une application qui :
- 📧 **Analyse vos newsletters Gmail** avec l'IA
- ⏰ **Envoie des résumés automatiques** selon votre planning
- 💾 **Sauvegarde vos données** dans GitHub Gist
- 🚀 **Fonctionne automatiquement** via GitHub Actions

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

### 4.1 Obtenir la Clé OpenAI

1. Allez sur [platform.openai.com](https://platform.openai.com)
2. Créez un compte ou connectez-vous
3. Allez dans **"API Keys"**
4. Cliquez sur **"Create new secret key"**
5. Copiez la clé (commence par `sk-`)

### 4.2 Générer une Clé Secrète

1. Allez sur votre application Streamlit déployée
2. Allez dans **"🔧 Configuration"**
3. Cliquez sur **"Générer une nouvelle clé secrète"**
4. Copiez la clé générée

### 4.3 Configurer les Secrets Streamlit

Dans votre application Streamlit déployée :

1. Allez dans **"Settings" > "Secrets"**
2. Ajoutez ces secrets :

```
OPENAI_API_KEY = "sk-..."
SECRET_KEY = "votre-clé-secrète-32-caractères"
GIST_ID = "votre-gist-id"
GIST_TOKEN = "ghp_..."
```

**Note :** Les credentials Google OAuth2 sont maintenant automatiquement sauvegardés dans le Gist lors de la première connexion.

## 📧 Étape 5 : Configuration Gmail

### 5.1 Première Connexion

1. Dans votre application Streamlit, cliquez sur **"🔑 Se connecter avec Google"**
2. Autorisez l'accès à Gmail
3. **Important** : Assurez-vous d'autoriser les permissions `gmail.readonly` et `gmail.send`

### 5.2 Authentification Automatique

**✅ Nouveau :** Les credentials OAuth2 sont maintenant automatiquement sauvegardés dans le Gist lors de la première connexion. Plus besoin de les copier manuellement !

## 🤖 Étape 6 : Activation de l'Automatisation

### 6.1 Configuration du Planning

1. Dans votre application Streamlit, allez dans **"🤖 Scheduler"**
2. Configurez votre planning :
   - **Fréquence** : Quotidien, Hebdomadaire, ou Mensuel
   - **Jour** : Pour les planifications hebdomadaires/mensuelles
   - **Heure** : Heure UTC d'exécution
   - **Email de notification** : Votre adresse email

### 6.2 Fonctionnalités Automatiques

**✅ Une fois configuré, tout est automatique :**
- **Authentification** → Tokens OAuth2 sauvegardés automatiquement
- **Génération IA** → Résumés créés sans intervention
- **Envoi d'email** → Notifications envoyées selon le planning
- **Multi-utilisateurs** → Chaque utilisateur a ses propres credentials

## 💾 Étape 7 : Configuration GitHub Gist

### 7.1 Créer un Gist Secret

1. Allez sur [gist.github.com](https://gist.github.com)
2. Créez un nouveau Gist **secret** (pas public !)
3. **Filename** : `user_data.json`
4. **Content** :
```json
{}
```
5. Cliquez sur **"Create secret gist"**
6. Copiez l'ID du Gist (dans l'URL : `gist.github.com/VOTRE-USERNAME/ID-DU-GIST`)

> ⚠️ **Important :** Un Gist "secret" n'est pas vraiment privé ! Il est accessible via URL directe.
> Pour une vraie sécurité, vous DEVEZ configurer un token GitHub (étape suivante).

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

1. Dans votre application Streamlit, allez dans **"📧 Newsletters"**
2. Cliquez sur **"Ajouter une newsletter"**
3. Ajoutez les adresses email des newsletters à suivre
4. Configurez les paramètres :
   - **Fréquence** : hebdomadaire, mensuelle, etc.
   - **Jours d'analyse** : combien de jours d'emails analyser
   - **Email de notification** : où envoyer le résumé

### 8.2 Configurer la Planification

1. Allez dans **"🤖 Scheduler"**
2. Activez **"Envoi automatique"**
3. Configurez :
   - **Jour** : jour de la semaine
   - **Heure** : heure d'envoi (UTC)
4. Sauvegardez

### 8.3 Test

1. Cliquez sur **"🧪 Tester la newsletter"**
2. Vérifiez que vous recevez un email avec le résumé IA

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
- L'URI de redirection doit être `urn:ietf:wg:oauth:2.0:oob`

**❌ Erreur "Gmail API has not been used"**
- Activez l'API Gmail dans Google Cloud Console

**❌ Erreur "401 Unauthorized" sur le Gist**
- Vérifiez que votre Gist est public
- Vérifiez que votre token GitHub a la scope "gist"

**❌ GitHub Actions échoue**
- Vérifiez que tous les secrets GitHub sont configurés
- Vérifiez les logs dans l'onglet "Actions"

### Support

- 📖 **Documentation** : [README.md](README.md)
- 🐛 **Issues** : [GitHub Issues](https://github.com/VOTRE-USERNAME/AutoBrief/issues)

---

**🎉 Félicitations ! Votre AutoBrief est maintenant opérationnel !**

Votre application va maintenant :
- ✅ Analyser automatiquement vos newsletters Gmail
- ✅ Générer des résumés IA intelligents
- ✅ Vous envoyer des emails selon votre planning
- ✅ Sauvegarder vos données automatiquement

**Profitez de vos résumés automatiques !** 📧✨