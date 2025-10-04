# 🔒 Configuration de la Persistance sur Streamlit Cloud

## 🎯 **Problème :**
Sur Streamlit Cloud, les données ne sont pas persistantes entre les sessions. GitHub Actions ne peut pas accéder aux données utilisateur.

## 🚀 **Solution : Secrets Streamlit**

### **Étape 1 : Configurer vos newsletters**
1. Allez dans l'onglet **"📧 Newsletters"**
2. Ajoutez vos newsletters
3. Configurez vos paramètres
4. Cliquez sur **"💾 Sauvegarder les paramètres"**

### **Étape 2 : Copier les données**
1. Après la sauvegarde, vous verrez un **code JSON** à copier
2. Copiez tout le contenu affiché

### **Étape 3 : Ajouter le secret Streamlit**
1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Sélectionnez votre application
3. Cliquez sur **"Settings"** > **"Secrets"**
4. Ajoutez ce secret :

```toml
user_data = '''
{
  "votre.email@example.com": {
    "newsletters": ["newsletter1@example.com", "newsletter2@example.com"],
    "settings": {
      "frequency": "weekly",
      "days_to_analyze": 7,
      "notification_email": "votre.email@example.com",
      "last_run": null,
      "auto_send": true,
      "schedule_day": "monday",
      "schedule_time": "09:00",
      "schedule_timezone": "UTC"
    }
  }
}
'''
```

### **Étape 4 : Redémarrer l'application**
1. Cliquez sur **"Redeploy"** dans Streamlit Cloud
2. Vos données seront maintenant persistantes !

## ✅ **Résultat :**
- **Données persistantes** : Sauvegardées dans les secrets Streamlit
- **GitHub Actions** : Peut accéder aux données via les secrets
- **Automatisation** : Fonctionne avec la planification

## 🔧 **Pour plusieurs utilisateurs :**
Ajoutez chaque utilisateur dans le même secret `user_data` :

```toml
user_data = '''
{
  "utilisateur1@example.com": {
    "newsletters": ["newsletter1@example.com"],
    "settings": { ... }
  },
  "utilisateur2@example.com": {
    "newsletters": ["newsletter2@example.com"],
    "settings": { ... }
  }
}
'''
```

## 🎉 **C'est tout !**
Vos newsletters et paramètres sont maintenant sauvegardés de façon permanente !
