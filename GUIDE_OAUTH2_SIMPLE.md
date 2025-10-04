# 🔐 Guide simple pour OAuth2 (Alternative au Service Account)

## 🚨 Problème avec Service Account

Le Service Account nécessite une configuration complexe des permissions Gmail. Une alternative plus simple est d'utiliser les credentials OAuth2 de l'utilisateur.

## 📋 Solution : Credentials OAuth2

### **1. 🔑 Se connecter à l'application Streamlit**

1. Allez sur : `https://alexismetton.streamlit.app`
2. Connectez-vous avec Google
3. Autorisez l'accès à Gmail

### **2. 📁 Récupérer le fichier token.json**

1. Allez à la page **"🤖 Scheduler"**
2. Cliquez sur **"🔑 Afficher credentials OAuth2 (pour GitHub Actions)"**
3. Copiez le contenu JSON affiché

### **3. 🔧 Mettre à jour les secrets GitHub**

1. Allez dans **Settings** > **Secrets and variables** > **Actions**
2. Modifiez le secret `GOOGLE_CREDENTIALS`
3. Remplacez le contenu par le contenu de votre `token.json`

### **4. ⚠️ Important : Renouveler régulièrement**

Les tokens OAuth2 expirent, vous devrez :
- **Renouveler** tous les 7 jours environ
- **Se reconnecter** à l'application Streamlit
- **Récupérer** le nouveau token
- **Mettre à jour** le secret GitHub

## 🎯 Avantages de cette approche

- ✅ **Plus simple** à configurer
- ✅ **Fonctionne** immédiatement
- ✅ **Pas de configuration** complexe des permissions

## ⚠️ Inconvénients

- ❌ **Expire** tous les 7 jours
- ❌ **Nécessite** une maintenance régulière

## 🚀 Test

Après mise à jour des secrets :
1. Déclenchez manuellement GitHub Actions
2. Vérifiez que l'email est envoyé avec succès

---

**Cette approche est plus simple et fonctionne immédiatement !** ✅
