import streamlit as st
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
import base64
from cryptography.fernet import Fernet

class SecureAuth:
    def __init__(self):
        self.config = Config()
        self.encryption = self.config.get_encryption_key()
        self.external_credentials = None  # Pour les credentials externes (GitHub Actions)
        
    
    def get_credentials_file(self):
        """Récupère le fichier credentials.json sécurisé"""
        # Vérifier d'abord les secrets Streamlit (si disponibles)
        try:
            if 'GOOGLE_CREDENTIALS' in st.secrets:
                try:
                    # Créer un fichier temporaire depuis les secrets
                    credentials_data = st.secrets['GOOGLE_CREDENTIALS']
                    temp_file = 'temp_credentials.json'
                    with open(temp_file, 'w') as f:
                        f.write(credentials_data)
                    return temp_file
                except Exception as e:
                    st.error(f"❌ Erreur lors de la lecture des credentials: {e}")
                    return None
        except Exception:
            # Pas de secrets Streamlit disponibles, continuer avec le fallback
            pass
        
        # Fallback vers le fichier local
        if not os.path.exists(self.config.CREDENTIALS_PATH):
            st.error("❌ Fichier credentials.json manquant. Veuillez le placer dans le répertoire du projet.")
            return None
        return self.config.CREDENTIALS_PATH
    
    def encrypt_token(self, token_data):
        """Chiffre les données du token"""
        try:
            # Debug: afficher la SECRET_KEY utilisée pour le chiffrement
            secret_key = self.config.get_secret_key()
            if hasattr(st, 'info'):
                st.info(f"🔧 SECRET_KEY utilisée pour chiffrement: {secret_key[:10]}...")
            
            json_data = json.dumps(token_data)
            encrypted_data = self.encryption.encrypt(json_data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            st.error(f"Erreur de chiffrement: {e}")
            return None
    
    def decrypt_token(self, encrypted_data):
        """Déchiffre les données du token"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.encryption.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            st.error(f"Erreur de déchiffrement: {e}")
            return None
    
    def save_encrypted_token(self, credentials):
        """Sauvegarde le token chiffré dans la session Streamlit"""
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        encrypted_token = self.encrypt_token(token_data)
        if encrypted_token:
            st.session_state['encrypted_token'] = encrypted_token
            st.session_state['token_expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
            return True
        return False
    
    def load_encrypted_token(self):
        """Charge le token chiffré depuis la session Streamlit ou credentials externes"""
        
        # Si on a des credentials externes (GitHub Actions), les utiliser
        if self.external_credentials:
            try:
                credentials_data = json.loads(self.external_credentials)
                
                # Créer l'objet Credentials
                credentials = Credentials(
                    token=credentials_data['token'],
                    refresh_token=credentials_data['refresh_token'],
                    token_uri=credentials_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=credentials_data['client_id'],
                    client_secret=credentials_data['client_secret'],
                    scopes=credentials_data.get('scopes', self.config.SCOPES)
                )
                
                return credentials
            except Exception as e:
                print(f"❌ Erreur chargement credentials externes: {e}")
                return None
        
        # Sinon, utiliser la session Streamlit
        if 'encrypted_token' not in st.session_state:
            return None
            
        try:
            token_data = self.decrypt_token(st.session_state['encrypted_token'])
            if not token_data:
                return None
                
            # Créer l'objet Credentials
            credentials = Credentials(
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                token_uri=token_data['token_uri'],
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data['scopes']
            )
            
            # Vérifier si le token est expiré
            if st.session_state.get('token_expiry'):
                from datetime import datetime
                expiry = datetime.fromisoformat(st.session_state['token_expiry'])
                if datetime.now() >= expiry:
                    return None
                    
            return credentials
        except Exception as e:
            st.error(f"Erreur lors du chargement du token: {e}")
            return None
    
    def set_external_credentials(self, credentials_json):
        """Définit les credentials externes (pour GitHub Actions)"""
        self.external_credentials = credentials_json
    
    def authenticate_user(self):
        """Authentifie l'utilisateur avec Google OAuth"""
        if 'authenticated' in st.session_state and st.session_state['authenticated']:
            return True
            
        st.markdown("### 🔐 Authentification Google")
        st.info("Pour utiliser AutoBrief, vous devez vous connecter avec votre compte Google.")
        
        # Vérifier si credentials.json existe
        if not self.get_credentials_file():
            return False
            
        # Bouton de connexion
        if st.button("🔑 Se connecter avec Google", type="primary"):
            try:
                # Obtenir le fichier credentials (secrets Streamlit en priorité)
                credentials_file = self.get_credentials_file()
                if not credentials_file:
                    return False
                
                # Utiliser le flux OAuth natif (plus fiable)
                flow = Flow.from_client_secrets_file(
                    credentials_file,
                    scopes=self.config.SCOPES,
                    redirect_uri="urn:ietf:wg:oauth:2.0:oob"  # Flux natif
                )
                
                # Obtenir l'URL d'autorisation
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                st.markdown(f"""
                **Étapes de connexion :**
                
                1. Cliquez sur le lien ci-dessous
                2. Connectez-vous avec votre compte Google
                3. Copiez le code d'autorisation affiché
                4. Collez-le dans le champ ci-dessous
                
                [🔗 Se connecter avec Google]({auth_url})
                """)
                
                # Champ pour le code d'autorisation
                auth_code = st.text_input("Code d'autorisation:", type="password", 
                                        help="Collez ici le code que vous avez reçu après la connexion")
                
                if auth_code:
                    try:
                        # Échanger le code contre les tokens
                        flow.fetch_token(code=auth_code)
                        credentials = flow.credentials
                        
                        # Sauvegarder le token chiffré
                        if self.save_encrypted_token(credentials):
                            st.session_state['authenticated'] = True
                            st.session_state['user_email'] = self.get_user_email(credentials)
                            st.success("✅ Connexion réussie !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde des credentials")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur d'authentification: {e}")
                        st.write(f"🔍 Détails de l'erreur: {str(e)}")
                        
                        # Proposer de réessayer
                        if st.button("🔄 Réessayer la connexion"):
                            st.session_state.pop('authenticated', None)
                            st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erreur de configuration: {e}")
                st.info("Vérifiez que le fichier credentials.json est présent et correct.")
                
        return False
    
    def get_user_email(self, credentials):
        """Récupère l'email de l'utilisateur connecté"""
        try:
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress', 'Utilisateur inconnu')
        except Exception:
            return 'Utilisateur connecté'
    
    def get_gmail_service(self):
        """Récupère le service Gmail authentifié"""
        credentials = self.load_encrypted_token()
        
        if not credentials:
            st.error("❌ Session expirée. Veuillez vous reconnecter.")
            st.session_state['authenticated'] = False
            return None
            
        try:
            # Rafraîchir le token si nécessaire
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self.save_encrypted_token(credentials)
                
            service = build('gmail', 'v1', credentials=credentials)
            return service
        except Exception as e:
            st.error(f"❌ Erreur de connexion Gmail: {e}")
            return None
    
    def logout(self):
        """Déconnecte l'utilisateur"""
        for key in ['authenticated', 'encrypted_token', 'token_expiry', 'user_email']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

