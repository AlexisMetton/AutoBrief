#!/usr/bin/env python3
"""
Générateur de clé secrète pour AutoBrief
Génère une clé de 32 caractères sécurisée
"""

import secrets
import string

def generate_secret_key(length=32):
    """Génère une clé secrète sécurisée"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("🔐 Générateur de clé secrète pour AutoBrief")
    print("=" * 50)
    
    # Générer une clé de 32 caractères
    secret_key = generate_secret_key(32)
    
    print(f"✅ Votre SECRET_KEY générée :")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("📋 Instructions :")
    print("1. Copiez cette clé")
    print("2. Collez-la dans les secrets Streamlit Cloud")
    print("3. Gardez-la secrète !")
    print()
    print("⚠️  IMPORTANT : Ne partagez JAMAIS cette clé !")

if __name__ == "__main__":
    main()
