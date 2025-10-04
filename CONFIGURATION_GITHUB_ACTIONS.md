# ⚙️ Configuration GitHub Actions - Automatisation

## 🎯 **Objectif :**
Automatiser l'envoi des résumés de newsletters avec GitHub Actions.

## 📊 **Limites GitHub Actions :**

### **✅ Version gratuite :**
- **2,000 minutes/mois** disponibles
- **Exécution toutes les heures** : 720 minutes/mois
- **Marge de sécurité** : 1,280 minutes restantes
- **✅ Parfaitement faisable !**

## 🔧 **Configuration automatique :**

### **1. Workflow GitHub Actions :**
```yaml
# .github/workflows/auto-brief-scheduler.yml
name: AutoBrief Scheduler

# Exécute toutes les heures pour vérifier les planifications
on:
  schedule:
    - cron: '0 * * * *'  # Toutes les heures à l'heure pile
  workflow_dispatch:     # Déclenchement manuel

jobs:
  auto-brief:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run scheduler
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
        GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
        GIST_ID: ${{ secrets.GIST_ID }}
        GIST_TOKEN: ${{ secrets.GIST_TOKEN }}
      run: python scheduler.py
```

### **2. Secrets GitHub requis :**
```toml
OPENAI_API_KEY = "sk-votre-cle-openai"
SECRET_KEY = "votre-cle-secrete"
GOOGLE_CREDENTIALS = '{"type":"service_account",...}'
GIST_ID = "abc123def456"
GIST_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
```

## ⏰ **Logique de planification :**

### **✅ Vérification toutes les heures :**
- **GitHub Actions** : S'exécute à l'heure pile (ex: 09:00, 10:00, 11:00...)
- **Marge de tolérance** : +/- 30 minutes
- **Cohérence** : Parfaitement synchronisé

### **📅 Types de planification :**
- **Quotidien** : Tous les jours à l'heure choisie
- **Hebdomadaire** : Un jour spécifique à l'heure choisie
- **Mensuel** : Un jour spécifique à l'heure choisie

## 🎯 **Avantages :**

### **✅ Fiabilité :**
- **Exécution garantie** : GitHub Actions est très fiable
- **Synchronisation** : Heure pile respectée
- **Logs** : Traçabilité complète

### **✅ Économique :**
- **Gratuit** : Dans les limites GitHub
- **Efficace** : 720 minutes/mois seulement
- **Scalable** : Peut gérer plusieurs utilisateurs

## 🚀 **Résultat :**

**Configuration automatique → Exécution toutes les heures → Envoi automatique des résumés → Plus de tâche manuelle !**

**Automatisation complète et fiable !** 🎉
