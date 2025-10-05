# Générateur de SECRET_KEY pour AutoBrief

## 🎯 **Qu'est-ce que SECRET_KEY ?**

La `SECRET_KEY` est une **clé de chiffrement** qui :
- **Chiffre vos tokens** OAuth (connexion Gmail)
- **Protège vos sessions** utilisateur
- **Sécurise les données** sensibles
- **32 caractères** minimum pour la sécurité

## 🚀 **Comment générer votre SECRET_KEY :**

### **Option 1 : Script Python (RECOMMANDÉ)**
```bash
# Lancez ce script
./venv/Scripts/python.exe generate_secret_key.py

# Résultat :
SECRET_KEY=AbC123XyZ789!@#$%^&*()_+-=[]{}|;':",./<>?
```
ou
```bash
# Lancez ce script
python generate_secret_key.py

# Résultat :
SECRET_KEY=AbC123XyZ789!@#$%^&*()_+-=[]{}|;':",./<>?
```

### **Option 2 : Génération manuelle**
Créez une chaîne de **32 caractères** avec :
- Lettres majuscules : A-Z
- Lettres minuscules : a-z
- Chiffres : 0-9
- Symboles : !@#$%^&*()_+-=[]{}|;':",./<>?

**Exemple :** `MyS3cr3tK3y!2024@AutoBrief#Secure`

### **Option 3 : Générateurs en ligne**
- [RandomKeygen](https://randomkeygen.com/)
- [Password Generator](https://passwordsgenerator.net/)
- [Strong Password Generator](https://strongpasswordgenerator.com/)

## ⚠️ **IMPORTANT :**

### **Sécurité :**
- ❌ **Ne partagez JAMAIS** votre SECRET_KEY
- ❌ **Ne la commitez JAMAIS** dans Git
- ❌ **Ne l'écrivez JAMAIS** dans le code
- ✅ **Stockez-la** uniquement dans les secrets Streamlit et GitHub Actions

### **Exemples de SECRET_KEY valides :**
```
SECRET_KEY=AbC123XyZ789!@#$%^&*()_+-=[]{}|;':",./<>?
SECRET_KEY=MyS3cr3tK3y!2024@AutoBrief#Secure
SECRET_KEY=K3y!2024@AutoBrief#Secure&Strong
SECRET_KEY=AutoBrief2024!@#$%^&*()_+-=[]{}|;':",./<>?
```

## 🔧 **Configuration dans Streamlit Cloud :**

1. Allez dans votre app Streamlit Cloud
2. Cliquez sur "Settings" → "Secrets"
3. Ajoutez :
   ```
   SECRET_KEY=votre_cle_secrete_32_caracteres
   ```
4. Cliquez sur "Save"

## ✅ **Vérification :**

Votre SECRET_KEY est correcte si :
- **32 caractères** ou plus
- **Contient** lettres, chiffres, symboles
- **Unique** et **aléatoire**
- **Stockée** uniquement dans les secrets

---

**Votre SECRET_KEY est la clé de la sécurité d'AutoBrief !** 🔐
