# 🔒 Persistance des Données sur Streamlit Cloud

## 🎯 **Problème :**
Sur Streamlit Cloud, les données ne sont pas persistantes par défaut. Chaque redémarrage efface les données utilisateur.

## 🚀 **Solutions :**

### **Option 1 : Utiliser les Secrets Streamlit (RECOMMANDÉ)**

#### **1. Configurer les données initiales**
Dans votre application Streamlit Cloud, ajoutez ce secret :

```toml
# Dans les secrets Streamlit Cloud
user_data = '''
{
  "newsletters": [],
  "settings": {
    "frequency": "weekly",
    "days_to_analyze": 7,
    "notification_email": "",
    "last_run": null,
    "auto_send": false,
    "schedule_day": "monday",
    "schedule_time": "09:00",
    "schedule_timezone": "UTC"
  }
}
'''
```

#### **2. Comment ajouter ce secret :**
1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Sélectionnez votre application
3. Cliquez sur **"Settings"** > **"Secrets"**
4. Ajoutez le secret `user_data` avec le JSON ci-dessus

### **Option 2 : Base de données externe (AVANCÉ)**

Pour une persistance complète, vous pouvez utiliser :
- **Google Sheets** (gratuit)
- **Airtable** (gratuit)
- **Supabase** (gratuit)
- **PlanetScale** (gratuit)

## 🔧 **Comment ça fonctionne maintenant :**

### **Ordre de priorité :**
1. **Cache de session** : Données modifiées récemment
2. **Secrets Streamlit** : Données persistantes
3. **Fichier local** : Fallback pour développement

### **Avantages :**
- ✅ **Persistance** : Données sauvegardées dans les secrets
- ✅ **Performance** : Cache de session pour les modifications
- ✅ **Fallback** : Fonctionne en local et en cloud

## 📋 **Configuration complète :**

### **Secrets Streamlit Cloud :**
```toml
OPENAI_API_KEY = "sk-votre-cle-openai"
SECRET_KEY = "votre-cle-secrete-32-caracteres"
GOOGLE_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "votre-projet",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "...",
  "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
}
'''

user_data = '''
{
  "newsletters": [],
  "settings": {
    "frequency": "weekly",
    "days_to_analyze": 7,
    "notification_email": "",
    "last_run": null,
    "auto_send": false,
    "schedule_day": "monday",
    "schedule_time": "09:00",
    "schedule_timezone": "UTC"
  }
}
'''
```

## ✅ **Résultat :**
- **Données persistantes** : Sauvegardées dans les secrets Streamlit
- **Modifications temporaires** : Cache de session pour la performance
- **Fonctionnement** : Local et cloud

Vos newsletters et paramètres seront maintenant sauvegardés ! 🎉
