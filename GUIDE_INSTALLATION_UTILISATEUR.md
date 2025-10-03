# 🚀 AutoBrief - Guide d'Installation Ultra-Simple

## 🎯 Installation en 5 minutes (sans connaissances techniques)

### **Étape 1 : Créer un compte GitHub** (2 minutes)
1. Allez sur [github.com](https://github.com)
2. Cliquez sur "Sign up"
3. Créez votre compte (gratuit)

### **Étape 2 : Copier le projet** (30 secondes)
1. Allez sur [ce lien](https://github.com/votre-repo/AutoBrief)
2. Cliquez sur le bouton **"Fork"** (en haut à droite)
3. Votre copie personnelle est créée ! ✅

### **Étape 3 : Déployer sur Streamlit Cloud** (2 minutes)
1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Cliquez sur "Sign in with GitHub"
3. Cliquez sur "New app"
4. Sélectionnez votre repository "AutoBrief"
5. **Main file path** : `streamlit_app.py` (déjà configuré par défaut)
6. Cliquez sur "Deploy!"

### **Étape 4 : Configurer vos clés** (2 minutes)
1. Dans l'onglet "Secrets", ajoutez au format TOML :
   ```toml
   OPENAI_API_KEY = "sk-votre_cle_openai_ici"
   SECRET_KEY = "votre_cle_secrete_32_caracteres"
   GOOGLE_CREDENTIALS = '{"type":"service_account","project_id":"votre-projet","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
   ```
2. Cliquez sur "Save"

### **Étape 5 : Configurer Google OAuth** (2 minutes)
1. Allez sur [Google Cloud Console](https://console.cloud.google.com)
2. Créez un projet
3. Activez l'API Gmail
4. Créez des identifiants OAuth2
5. **Type d'application** : **Application de bureau**
7. Téléchargez `credentials.json`
8. **Copiez le contenu** du fichier
9. **Ajoutez-le dans les secrets Streamlit** comme `GOOGLE_CREDENTIALS`

## 🎉 **C'est tout ! Votre AutoBrief est prêt !**

**URL de votre application :** `https://votre-nom.streamlit.app`

---

## 🔧 **Configuration détaillée**

### **Obtenir une clé OpenAI :**
1. Allez sur [platform.openai.com](https://platform.openai.com)
2. Créez un compte
3. Allez dans "API Keys"
4. Cliquez sur "Create new secret key"
5. Copiez la clé (commence par `sk-`)

### **Obtenir Google OAuth :**
1. [Google Cloud Console](https://console.cloud.google.com)
2. "New Project" → Nommez-le "AutoBrief"
3. "APIs & Services" → "Library"
4. Recherchez "Gmail API" → "Enable"
5. "APIs & Services" → "Credentials"
6. "Create Credentials" → "OAuth 2.0 Client IDs"
7. **"Application type"** → **"Application de bureau"**
8. Téléchargez le fichier JSON
9. Renommez-le `credentials.json`

---

## 🆘 **Problèmes courants**

### **"App not found"**
- Vérifiez que vous avez bien cliqué sur "Fork"
- Vérifiez que le repository est public

### **"Secrets not found"**
- Vérifiez l'orthographe : `OPENAI_API_KEY` et `SECRET_KEY`
- Vérifiez que vous avez cliqué sur "Save"

### **"Google authentication failed"**
- Vérifiez que `credentials.json` est bien dans le repository
- Vérifiez que l'API Gmail est activée

### **"OpenAI API error"**
- Vérifiez que votre clé OpenAI est correcte
- Vérifiez que vous avez des crédits OpenAI

---

## 📞 **Besoin d'aide ?**

- 📧 **Email** : support@autobrief.com
- 💬 **Discord** : [Serveur AutoBrief](https://discord.gg/autobrief)
- 📖 **Documentation** : [docs.autobrief.com](https://docs.autobrief.com)
- 🐛 **Bug report** : [GitHub Issues](https://github.com/votre-repo/AutoBrief/issues)

---

## 🎯 **Utilisation**

Une fois déployé :
1. **Connectez-vous** avec votre Google
2. **Ajoutez vos newsletters** (emails qui vous envoient des newsletters)
3. **Configurez la fréquence** (quotidien/hebdomadaire)
4. **Générez votre premier résumé** !
5. **Recevez vos résumés automatiquement** par email

**Votre veille est maintenant automatisée !** 🤖✨
