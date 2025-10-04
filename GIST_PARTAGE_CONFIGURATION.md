# 🔗 Configuration Gist Partagé - Multi-utilisateurs

## 🎯 **Problème résolu :**
Maintenant **tous les utilisateurs partagent le même Gist**, même depuis différents ordinateurs !

## 🔧 **Configuration requise :**

### **1. Créer un Gist partagé (une seule fois) :**

#### **Option A : Automatique (recommandé)**
1. **Premier utilisateur** configure ses newsletters
2. **Gist créé automatiquement** avec l'ID affiché
3. **Notez l'ID** du Gist créé

#### **Option B : Manuel**
1. Allez sur [gist.github.com](https://gist.github.com)
2. Créez un nouveau Gist :
   - **Description** : "AutoBrief User Data"
   - **Fichier** : `user_data.json`
   - **Contenu** : `{}`
   - **Visibilité** : Privé
3. **Notez l'ID** du Gist (dans l'URL)

### **2. Configurer le Gist partagé :**

#### **Secrets Streamlit Cloud :**
```toml
OPENAI_API_KEY = "sk-votre-cle-openai"
SECRET_KEY = "votre-cle-secrete"
GOOGLE_CREDENTIALS = '{"type":"service_account",...}'
GIST_ID = "abc123def456"  # ← ID du Gist partagé
```

#### **Secrets GitHub (pour l'automatisation) :**
```toml
OPENAI_API_KEY = "sk-votre-cle-openai"
SECRET_KEY = "votre-cle-secrete"
GOOGLE_CREDENTIALS = '{"type":"service_account",...}'
GIST_ID = "abc123def456"  # ← Même ID du Gist partagé
```

## 🎯 **Fonctionnement multi-utilisateurs :**

### **Structure du Gist partagé :**
```json
{
  "utilisateur1@example.com": {
    "newsletters": ["newsletter1@example.com"],
    "settings": {
      "frequency": "weekly",
      "auto_send": true,
      "notification_email": "utilisateur1@example.com"
    }
  },
  "utilisateur2@example.com": {
    "newsletters": ["newsletter2@example.com"],
    "settings": {
      "frequency": "daily",
      "auto_send": true,
      "notification_email": "utilisateur2@example.com"
    }
  }
}
```

### **Sauvegarde :**
- **Utilisateur 1** sauvegarde → Ajouté au Gist partagé
- **Utilisateur 2** sauvegarde → Ajouté au Gist partagé
- **Pas de conflit** : Chaque utilisateur a ses propres données

### **Chargement :**
- **Utilisateur 1** se connecte → Charge ses données du Gist
- **Utilisateur 2** se connecte → Charge ses données du Gist
- **Même Gist** : Tous utilisent le même Gist partagé

## ✅ **Avantages :**

### **✅ Multi-utilisateurs :**
- **Même Gist** : Tous les utilisateurs partagent le même Gist
- **Données séparées** : Chaque utilisateur a ses propres données
- **Pas de conflit** : Sauvegarde/chargement sécurisé

### **✅ Multi-appareils :**
- **Ordinateur 1** : Utilise le Gist partagé
- **Ordinateur 2** : Utilise le même Gist partagé
- **Synchronisation** : Données identiques partout

### **✅ GitHub Actions :**
- **Un seul Gist** : Lit toutes les données utilisateurs
- **Traitement** : Génère les résumés pour tous les utilisateurs
- **Efficace** : Une seule source de données

## 🚀 **Résultat :**

**Configuration unique → Tous les utilisateurs → Même Gist partagé → Données synchronisées → Automatisation multi-utilisateurs !**

**Plus besoin de créer un Gist par utilisateur !** 🎉
