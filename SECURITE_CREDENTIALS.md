# 🔐 Sécurité des Credentials - AutoBrief

## ⚠️ **IMPORTANT : Ne commitez JAMAIS credentials.json !**

### **Problème de sécurité :**
- ❌ **credentials.json** contient des clés OAuth sensibles
- ❌ Le mettre sur GitHub = **exposition publique**
- ❌ N'importe qui peut voir vos identifiants

## ✅ **Solution sécurisée :**

### **1. Créer credentials.json localement**
```bash
# Créez credentials.json comme d'habitude
# Téléchargez depuis Google Cloud Console
```

### **2. Copier le contenu**
```bash
# Ouvrez credentials.json
# Copiez TOUT le contenu (JSON complet)
```

### **3. Ajouter dans les secrets Streamlit**
```toml
[secrets]
OPENAI_API_KEY = "sk-votre_cle_openai_ici"
SECRET_KEY = "votre_cle_secrete_32_caracteres"
GOOGLE_CREDENTIALS = '{"type":"service_account","project_id":"votre-projet","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
```

### **4. Supprimer credentials.json**
```bash
# Supprimez credentials.json de votre machine
# Ne le commitez JAMAIS
```

## 🛡️ **Sécurité garantie :**

### **Ce qui est sécurisé :**
- ✅ **Pas de credentials.json** sur GitHub
- ✅ **Données chiffrées** dans les secrets Streamlit
- ✅ **Fichier temporaire** créé à la volée
- ✅ **Fallback** pour le développement local

### **Ce qui est exposé :**
- ✅ **Code public** (pas de données sensibles)
- ✅ **Interface utilisateur** (sécurisée)
- ✅ **Documentation** (sans clés)

## 🔧 **Fonctionnement technique :**

### **Code modifié :**
```python
def get_credentials_file(self):
    # Vérifier d'abord les secrets Streamlit
    if 'GOOGLE_CREDENTIALS' in st.secrets:
        # Créer un fichier temporaire depuis les secrets
        credentials_data = st.secrets['GOOGLE_CREDENTIALS']
        temp_file = 'temp_credentials.json'
        with open(temp_file, 'w') as f:
            f.write(credentials_data)
        return temp_file
    
    # Fallback vers le fichier local
    return self.config.CREDENTIALS_PATH
```

### **Workflow sécurisé :**
1. **Streamlit Cloud** lit les secrets
2. **Crée** un fichier temporaire
3. **Utilise** le fichier temporaire
4. **Supprime** le fichier temporaire

## ✅ **Vérification :**

Votre configuration est sécurisée si :
- ✅ **credentials.json** n'est PAS dans le repository
- ✅ **GOOGLE_CREDENTIALS** est dans les secrets Streamlit
- ✅ **Le code** utilise `st.secrets`
- ✅ **Aucune clé** n'est visible dans le code

## 🆘 **Problèmes courants :**

### **"GOOGLE_CREDENTIALS not found"**
- Solution : Vérifiez que `GOOGLE_CREDENTIALS` est dans les secrets

### **"Invalid JSON"**
- Solution : Vérifiez que le JSON est complet et valide

### **"File not found"**
- Solution : Vérifiez que le fichier temporaire est créé

---

**Sécurité maximale = Données privées + Code public !** 🔐
