# 🔐 Guide pour récupérer les credentials OAuth2 de l'utilisateur

## 🚨 Problème identifié

GitHub Actions utilise actuellement les **credentials d'application** (`installed`) au lieu des **credentials OAuth2 de l'utilisateur** nécessaires pour envoyer des emails.

## 📋 Solution : Récupérer les credentials OAuth2

### 1. 🔑 Se connecter à votre application Streamlit

1. Allez sur votre application Streamlit : `https://alexismetton.streamlit.app`
2. Connectez-vous avec votre compte Google
3. Autorisez l'accès à Gmail

### 2. 📁 Récupérer le fichier `token.json`

Après connexion, l'application crée un fichier `token.json` qui contient vos credentials OAuth2.

#### Option A : Via l'interface Streamlit (Recommandé)

1. Dans votre application Streamlit, allez à la page **Configuration**
2. Ajoutez un bouton temporaire pour afficher le contenu de `token.json`
3. Copiez le contenu JSON affiché

#### Option B : Via les logs Streamlit

1. Allez dans les logs de votre application Streamlit
2. Cherchez les logs d'authentification
3. Récupérez le contenu du token

### 3. 🔧 Mettre à jour les secrets GitHub

1. Allez dans **Settings** > **Secrets and variables** > **Actions**
2. Modifiez le secret `GOOGLE_CREDENTIALS`
3. Remplacez le contenu par le contenu de votre `token.json`

### 4. 📝 Format attendu

Le fichier `token.json` doit contenir :
```json
{
  "token": "ya29.a0...",
  "refresh_token": "1//0...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
  ]
}
```

## 🚀 Test

Après mise à jour des secrets :
1. Déclenchez manuellement GitHub Actions
2. Vérifiez que l'email est envoyé avec succès

## ⚠️ Important

- **Ne partagez jamais** vos credentials OAuth2
- **Renouvelez** les credentials si nécessaire
- **Gardez** les credentials d'application séparés des credentials utilisateur

## 🔄 Alternative : Service Account

Si vous préférez, vous pouvez créer un **Service Account** Google qui n'expire jamais :

1. Allez dans Google Cloud Console
2. Créez un Service Account
3. Téléchargez le fichier JSON
4. Utilisez ce fichier comme `GOOGLE_CREDENTIALS`

---

**Une fois les credentials OAuth2 configurés, l'envoi d'emails automatique fonctionnera parfaitement !** ✅
