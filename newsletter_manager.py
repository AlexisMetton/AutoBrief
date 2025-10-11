import streamlit as st
import os
import json
from datetime import datetime, timedelta
from config import Config
from secure_auth import SecureAuth
import base64
import requests
import re
from openai import OpenAI
import time
import pickle

class NewsletterManager:
    def __init__(self):
        self.config = Config()
        self.auth = SecureAuth()
        self.client = OpenAI(api_key=self.config.get_openai_key())
        self.user_email = st.session_state.get('user_email', 'default_user') if hasattr(st, 'session_state') else 'default_user'
        self._scheduler_mode = False  # Mode scheduler désactivé par défaut
        
        # Détecter automatiquement la reconnexion
        self._detect_reconnection()
        
        # Désactiver la vérification du Gist au démarrage (trop intrusive)
        # self.check_gist_configuration()
    
    def _detect_reconnection(self):
        """Détecte automatiquement la reconnexion et recharge les données"""
        try:
            current_email = st.session_state.get('user_email', 'default_user')
            last_email = st.session_state.get('last_user_email', None)
            
            
            # Si l'email a changé, c'est une reconnexion
            if current_email != last_email and current_email != 'default_user':
                
                # Vider le cache des données
                if 'user_data_cache' in st.session_state:
                    del st.session_state['user_data_cache']
                
                # Mettre à jour l'email en session
                st.session_state['last_user_email'] = current_email
                
                # Recharger automatiquement les données
                self._auto_reload_data()
            
            # Si pas d'email en session mais qu'on a un token valide, restaurer la session
            elif current_email == 'default_user' and 'encrypted_token' in st.session_state:
                self._restore_session_from_token()
                
        except Exception as e:
            pass
    
    def _auto_reload_data(self):
        """Recharge automatiquement les données depuis le Gist"""
        try:
            # Forcer le rechargement depuis le Gist
            data = self.load_from_github_gist()
            if data:
                # Mettre à jour la session avec les nouvelles données
                st.session_state['user_data_cache'] = data
                # Afficher un message de succès uniquement en mode debug
                # st.success(f"Données rechargées depuis le Gist : {len(data.get('newsletter_groups', []))} groupes")
            else:
                # Ne pas afficher de warning si c'est un nouvel utilisateur
                # Le système va créer les données par défaut
                pass
        except Exception as e:
            # Ne pas afficher d'erreur si c'est juste un problème de cache
            pass
    
    def _restore_session_from_token(self):
        """Restaure la session à partir du token chiffré"""
        try:
            
            # Vérifier si le token est valide
            if self.auth.is_authenticated():
                
                # Récupérer l'email depuis le token
                credentials = self.auth.get_credentials()
                if credentials:
                    user_email = self.auth.get_user_email(credentials)
                    if user_email:
                        # Restaurer la session
                        st.session_state['user_email'] = user_email
                        st.session_state['authenticated'] = True
                        st.session_state['last_user_email'] = user_email
                        
                        st.success("Session restaurée automatiquement !")
                        return True
            
            return False
        except Exception as e:
            return False
    
    def check_gist_configuration(self):
        """Vérifie la configuration du Gist au démarrage"""
        try:
            gist_id = None
            
            # Vérifier si le Gist est configuré dans les secrets
            try:
                if hasattr(st, 'secrets') and 'GIST_ID' in st.secrets:
                    gist_id = st.secrets['GIST_ID']
            except:
                pass
            
            if not gist_id:
                st.warning("""
                **Gist partagé non configuré**
                
                Pour utiliser la persistance automatique :
                1. Créez un Gist manuellement sur [gist.github.com](https://gist.github.com)
                2. Ajoutez le secret `GIST_ID` dans Streamlit Cloud
                3. Tous les utilisateurs partageront le même Gist
                """)
                return False
            
            # Vérifier si un token Gist est configuré
            gist_token = None
            try:
                if hasattr(st, 'secrets') and 'GIST_TOKEN' in st.secrets:
                    gist_token = st.secrets['GIST_TOKEN']
            except:
                pass
            
            if gist_token:
                # Vérifier que le Gist est privé (sécurité)
                try:
                    import requests
                    headers = {'Authorization': f'token {gist_token}'}
                    response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers)
                    
                    if response.status_code == 200:
                        gist_data = response.json()
                        if gist_data.get('public', True):
                            st.error("""
                            🚨 **DANGER DE SÉCURITÉ !**
                            
                            Votre Gist est PUBLIC ! Cela expose les tokens OAuth2 de tous les utilisateurs.
                            
                            **Solution :**
                            1. Allez sur [gist.github.com](https://gist.github.com)
                            2. Trouvez votre Gist
                            3. Cliquez sur "Edit" puis "Make secret"
                            4. Sauvegardez
                            """)
                            return False
                        else:
                            # Vérifier que le token est bien configuré pour l'authentification
                            if gist_token:
                                # Configuration sécurisée - pas de message de confirmation
                                return True
                            else:
                                st.warning("""
                                **Gist secret mais non sécurisé**
                                
                                Le Gist est "secret" mais accessible via URL directe.
                                Pour une vraie sécurité, configurez un token GitHub.
                                """)
                                return False
                    else:
                        st.error(f"Gist non accessible (Status: {response.status_code})")
                        return False
                except Exception as e:
                    st.error(f"Erreur vérification sécurité Gist: {e}")
                    return False
            else:
                st.warning("""
                **Token Gist manquant**
                
                Pour la sauvegarde automatique :
                1. Créez un token GitHub avec le scope `gist`
                2. Ajoutez-le dans les secrets Streamlit : `GIST_TOKEN`
                3. La sauvegarde sera automatique
                """)
                return False
                
        except Exception as e:
            pass
            return False
    
    def load_user_data(self):
        """Charge les données utilisateur depuis le Gist uniquement"""
        try:
            
            # Vérifier d'abord le cache en session
            if 'user_data_cache' in st.session_state:
                cached_data = st.session_state['user_data_cache']
                return cached_data
            
            # Si pas de cache, charger depuis le Gist
            data = self.load_from_github_gist()
            if data:
                # Mettre en cache
                st.session_state['user_data_cache'] = data
                return data
            else:
                # Pas de données dans le Gist - retourner des données par défaut
                default_data = {
                    'newsletter_groups': []
                }
                # Mettre en cache les données par défaut
                st.session_state['user_data_cache'] = default_data
                return default_data
                    
        except Exception as e:
            # En cas d'erreur, retourner des données par défaut
            return {
                'newsletter_groups': []
            }
    
    
    def load_from_github_gist(self):
        """Charge depuis GitHub Gist partagé"""
        try:
            # Utiliser le Gist partagé depuis les secrets Streamlit
            gist_id = None
            
            # Essayer d'abord depuis les secrets Streamlit
            try:
                if hasattr(st, 'secrets') and 'GIST_ID' in st.secrets:
                    gist_id = st.secrets['GIST_ID']
                    print(f"🔍 DEBUG: GIST_ID trouvé dans secrets: {gist_id}")
            except:
                pass
            
            # Fallback sur les variables d'environnement (pour GitHub Actions)
            if not gist_id:
                gist_id = os.getenv('GIST_ID')
                if gist_id:
                    print(f"🔍 DEBUG: GIST_ID trouvé dans env: {gist_id}")
            
            # Fallback sur la session state
            if not gist_id:
                gist_id = st.session_state.get('gist_id') if hasattr(st, 'session_state') else None
                if gist_id:
                    print(f"🔍 DEBUG: GIST_ID trouvé dans session: {gist_id}")
            
            if not gist_id:
                print("❌ DEBUG: GIST_ID non trouvé")
                return None
            
            import requests
            response = requests.get(f'https://api.github.com/gists/{gist_id}')
            
            print(f"🔍 DEBUG: Réponse Gist: {response.status_code}")
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(content) if content else {}
                    
                    print(f"🔍 DEBUG: Utilisateurs dans Gist: {list(all_users_data.keys())}")
                    print(f"🔍 DEBUG: Email actuel: {self.user_email}")
                    
                    # Retourner les données de cet utilisateur spécifique
                    if self.user_email in all_users_data:
                        user_data = all_users_data[self.user_email]
                        print(f"✅ DEBUG: Données utilisateur trouvées : {len(user_data.get('newsletter_groups', []))} groupes")
                        return user_data
                    else:
                        # Utilisateur pas encore dans le Gist - retourner des données par défaut
                        print(f"⚠️ DEBUG: Utilisateur {self.user_email} pas dans le Gist")
                        return {
                            'newsletter_groups': []
                        }
                else:
                    print("❌ DEBUG: Fichier user_data.json non trouvé dans le Gist")
            else:
                print(f"❌ DEBUG: Erreur HTTP {response.status_code}")
            return None
        except Exception as e:
            print(f"❌ DEBUG: Exception lors du chargement: {e}")
            return None
    
    def save_user_data(self, data):
        """Sauvegarde les données utilisateur directement dans le Gist"""
        try:
            # En mode scheduler, ne pas sauvegarder
            if self._scheduler_mode:
                return True
            
            # Nettoyer les données en supprimant les anciens paramètres
            cleaned_data = self._clean_data_structure(data)
            
            # Sauvegarder les credentials OAuth2 si disponibles (uniquement dans Streamlit)
            if hasattr(st, 'session_state') and 'encrypted_token' in st.session_state and st.session_state['encrypted_token']:
                try:
                    # Décrypter le token pour récupérer les credentials
                    decrypted_token = self.auth.decrypt_token(st.session_state['encrypted_token'])
                    if decrypted_token:
                        # Ajouter les credentials OAuth2 aux données utilisateur (chiffrés)
                        # Chiffrer les données sensibles avant de les sauvegarder dans le Gist
                        encrypted_credentials = self.auth.encrypt_token(decrypted_token)
                        
                        cleaned_data['oauth_credentials'] = {
                            "_encrypted_data": encrypted_credentials,  # Données chiffrées
                            "_encrypted": True,  # Indicateur que les données sont chiffrées
                            "token_uri": decrypted_token.get('token_uri', 'https://oauth2.googleapis.com/token'),
                            "scopes": decrypted_token.get('scopes', [
                                "https://www.googleapis.com/auth/gmail.readonly",
                                "https://www.googleapis.com/auth/gmail.send"
                            ])
                        }
                except Exception as e:
                    if hasattr(st, 'warning'):
                        st.warning(f"Impossible de sauvegarder les credentials OAuth2: {e}")
            
            # Sauvegarder directement dans le Gist
            success = self.save_to_github_gist(cleaned_data)
            
            return success
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def _clean_data_structure(self, data):
        """Nettoie la structure de données en supprimant les anciens paramètres"""
        cleaned_data = {}
        
        # Garder seulement les paramètres nécessaires
        if 'newsletter_groups' in data:
            cleaned_data['newsletter_groups'] = data['newsletter_groups']
        
        if 'oauth_credentials' in data:
            cleaned_data['oauth_credentials'] = data['oauth_credentials']
        
        # Supprimer les anciens paramètres
        # (newsletters, settings, etc. ne sont plus nécessaires)
        
        return cleaned_data
    
    
    def save_to_github_gist(self, data):
        """Sauvegarde dans GitHub Gist (gratuit et automatique)"""
        try:
            import requests
            
            # Vérifier que le Gist est configuré dans les secrets
            gist_id = None
            
            try:
                if hasattr(st, 'secrets') and 'GIST_ID' in st.secrets:
                    gist_id = st.secrets['GIST_ID']
            except:
                pass
            
            # Fallback sur les variables d'environnement (pour GitHub Actions)
            if not gist_id:
                gist_id = os.getenv('GIST_ID')
            
            if not gist_id:
                # En mode GitHub Actions, on ne peut pas afficher de warning Streamlit
                if os.getenv('GITHUB_ACTIONS'):
                    print("❌ GIST_ID non configuré dans les variables d'environnement")
                else:
                    st.warning("""
                    **Gist partagé non configuré**
                    
                    Pour utiliser la persistance automatique :
                    1. Le développeur doit créer un Gist manuellement
                    2. Ajouter le secret `GIST_ID` dans Streamlit Cloud
                    3. Tous les utilisateurs partageront le même Gist
                    """)
                return False
            
            # Vérifier que le Gist existe et est accessible
            response = requests.get(f'https://api.github.com/gists/{gist_id}')
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    # Charger les données existantes
                    existing_content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(existing_content) if existing_content else {}
                else:
                    all_users_data = {}
            else:
                return False
            
            # Ajouter/mettre à jour les données de cet utilisateur
            all_users_data[self.user_email] = data
            
            # Mettre à jour le Gist avec toutes les données
            update_data = {
                    "files": {
                        "user_data.json": {
                            "content": json.dumps(all_users_data, indent=2, ensure_ascii=False)
                        }
                    }
                }
                
            # Essayer de mettre à jour le Gist avec authentification GitHub
            gist_token = None
            
            # Essayer d'abord depuis les secrets Streamlit
            try:
                if hasattr(st, 'secrets') and 'GIST_TOKEN' in st.secrets:
                    gist_token = st.secrets['GIST_TOKEN']
            except:
                pass
            
            # Fallback sur les variables d'environnement (pour GitHub Actions)
            if not gist_token:
                gist_token = os.getenv('GIST_TOKEN')
            
            if gist_token:
                # Utiliser le token GitHub pour l'authentification
                headers = {
                    'Accept': 'application/vnd.github.v3+json',
                    'Authorization': f'token {gist_token}'
                }
            else:
                st.error("Token GIST_TOKEN manquant dans les secrets Streamlit")
                return False
            
            if gist_token:
                update_response = requests.patch(
                    f'https://api.github.com/gists/{gist_id}',
                    json=update_data,
                    headers=headers
                )
                
                
                if update_response.status_code == 200:
                    return True
                else:
                    return False
            else:
                # Pas de token Gist - sauvegarde en session uniquement
                st.warning("""
                **Token Gist manquant**
                    
                    Pour la sauvegarde automatique :
                    1. Créez un token GitHub avec le scope `gist`
                    2. Ajoutez-le dans les secrets Streamlit : `GIST_TOKEN`
                    3. La sauvegarde sera automatique
                """)
                
                return False
            
        except Exception as e:
            st.error(f"Erreur GitHub Gist: {e}")
            return False
    
    
        
    def save_newsletters(self, newsletters):
        """Sauvegarde la liste des newsletters dans le Gist"""
        # Mettre à jour les données utilisateur complètes
        user_data = self.load_user_data()
        user_data['newsletters'] = newsletters
        self.save_user_data(user_data)
        return True
    
    def get_newsletters_text(self):
        """Récupère les emails sous forme de texte pour l'affichage"""
        newsletters = self.get_newsletters()
        if isinstance(newsletters, list):
            return '\n'.join(newsletters)
        return ''
    
    def add_newsletter_group(self, title, emails, group_settings=None):
        """Ajoute un groupe de newsletters avec paramètres individuels"""
        newsletter_groups = self.get_newsletter_groups()
        
        # Vérifier si le groupe existe déjà
        for group in newsletter_groups:
            if group.get('title') == title:
                return False
        
        # Paramètres par défaut pour le groupe
        default_group_settings = {
            'frequency': 'weekly',
            'schedule_day': 'monday',
            'schedule_time': '09:00',
            'days_to_analyze': 7,
            'notification_email': '',
            'custom_prompt': '',
            'enabled': True,
            'last_run': None
        }
        
        # Fusionner avec les paramètres fournis
        if group_settings:
            default_group_settings.update(group_settings)
        
        # Ajouter le nouveau groupe avec ses paramètres
        new_group = {
            'title': title,
            'emails': emails,
            'settings': default_group_settings
        }
        newsletter_groups.append(new_group)
        self.save_newsletter_groups(newsletter_groups)
        return True
    
    def remove_newsletter_group(self, title):
        """Supprime un groupe de newsletters"""
        newsletter_groups = self.get_newsletter_groups()
        for i, group in enumerate(newsletter_groups):
            if group.get('title') == title:
                newsletter_groups.pop(i)
                self.save_newsletter_groups(newsletter_groups)
                return True
        return False
    
    def get_newsletter_groups(self):
        """Récupère les groupes de newsletters depuis le Gist"""
        user_data = self.load_user_data()
        return user_data.get('newsletter_groups', [])
    
    def save_newsletter_groups(self, newsletter_groups):
        """Sauvegarde les groupes de newsletters dans le Gist"""
        user_data = self.load_user_data()
        user_data['newsletter_groups'] = newsletter_groups
        self.save_user_data(user_data)
    
    def update_group_settings(self, group_title, new_settings):
        """Met à jour les paramètres d'un groupe spécifique"""
        newsletter_groups = self.get_newsletter_groups()
        for group in newsletter_groups:
            if group.get('title') == group_title:
                if 'settings' not in group:
                    group['settings'] = {}
                group['settings'].update(new_settings)
                self.save_newsletter_groups(newsletter_groups)
                return True
        return False
    
    def get_group_settings(self, group_title):
        """Récupère les paramètres d'un groupe spécifique"""
        newsletter_groups = self.get_newsletter_groups()
        for group in newsletter_groups:
            if group.get('title') == group_title:
                return group.get('settings', {})
        return {}
    
    def should_group_run_automatically(self, group_title):
        """Vérifie si un groupe doit être traité automatiquement"""
        group_settings = self.get_group_settings(group_title)
        
        if not group_settings.get('enabled', True):
            return False
        
        last_run = group_settings.get('last_run')
        if not last_run:
            return True
        
        try:
            last_run_date = datetime.fromisoformat(last_run)
            frequency = group_settings.get('frequency', 'weekly')
            
            # Vérifier si c'est le bon jour et la bonne heure
            if not self.is_group_scheduled_time(group_settings):
                return False
            
            if frequency == 'daily':
                return datetime.now() - last_run_date >= timedelta(days=1)
            elif frequency == 'weekly':
                return datetime.now() - last_run_date >= timedelta(weeks=1)
        except:
            return True
        
        return False
    
    def is_group_scheduled_time(self, group_settings):
        """Vérifie si c'est le bon moment pour traiter un groupe"""
        try:
            schedule_day = group_settings.get('schedule_day', 'monday')
            schedule_time = group_settings.get('schedule_time', '09:00')
            
            now = datetime.now()
            current_day = now.strftime('%A').lower()
            current_time = now.strftime('%H:%M')
            
            # Vérifier le jour (pour la fréquence weekly)
            if group_settings.get('frequency', 'weekly') == 'weekly':
                if current_day != schedule_day.lower():
                    return False
            
            # Vérifier l'heure (avec une marge de 30 minutes)
            target_hour = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            current_hour = now.hour
            current_minute = now.minute
            
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour * 60 + target_minute))
            return time_diff <= 30
            
        except Exception as e:
            return True  # En cas d'erreur, on autorise l'exécution
        
    
    
    def should_run_automatically(self):
        """Vérifie si un résumé automatique doit être généré (basé sur les groupes)"""
        # Ne pas se déclencher en mode interface utilisateur
        if hasattr(st, 'session_state') and st.session_state.get('just_connected', False):
            return False
        
        newsletter_groups = self.get_newsletter_groups()
        if not newsletter_groups:
            return False
        
        # Vérifier si au moins un groupe doit être traité
        for group in newsletter_groups:
            group_title = group.get('title', '')
            if self.should_group_run_automatically(group_title):
                return True
        
        return False
    
    
    
    def render_newsletter_management(self):
        """Interface de gestion des newsletters"""
        st.markdown("### <i class='fas fa-home'></i> Gestion des newsletters", unsafe_allow_html=True)
        
        # Ajouter un groupe de newsletters
        with st.expander('Ajouter un nouveau groupe de newsletters', expanded=True):
            st.markdown("**Créez un nouveau groupe avec ses paramètres personnalisés**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                group_title = st.text_input(
                    "Titre du groupe",
                    placeholder="Ex: Actualités Tech",
                    help="Nom de votre groupe de newsletters"
                )
                
                emails_text = st.text_area(
                    "Emails du groupe",
                    placeholder="email1@example.com\nemail2@example.com\nemail3@example.com",
                    help="Entrez un email par ligne",
                    height=120
                )
            
            with col2:
                
                # Configuration initiale
                initial_frequency = st.selectbox(
                    "Fréquence",
                    options=['daily', 'weekly'],
                    index=1,  # weekly par défaut
                    format_func=lambda x: {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire'}[x],
                    help="Fréquence de génération des résumés"
                )
                
                # Heure d'envoi
                time_options = []
                for hour in range(24):
                    time_str = f"{hour:02d}:00"
                    time_options.append(time_str)
                
                initial_time = st.selectbox(
                    "Heure d'envoi",
                    options=time_options,
                    index=9,  # 09:00 par défaut
                    help="Heure d'envoi (GitHub Actions s'exécute à l'heure pile)"
                )
                
                initial_email = st.text_input(
                    "Email de notification",
                    placeholder="votre.email@example.com",
                    help="Email pour recevoir les résumés de ce groupe"
                )
                
                initial_days = st.slider(
                    "Période d'analyse",
                    min_value=1,
                    max_value=7,
                    value=7,
                    help="Nombre de jours à analyser"
                )
            
            if st.button("Créer le groupe", type="primary", icon=":material/add:", use_container_width=True):
                if group_title and emails_text:
                    # Parser les emails
                    emails = [email.strip() for email in emails_text.split('\n') if email.strip() and '@' in email]
                    if emails:
                        # Configuration initiale du groupe
                        initial_settings = {
                            'frequency': initial_frequency,
                            'schedule_day': 'monday',
                            'schedule_time': initial_time,
                            'days_to_analyze': initial_days,
                            'notification_email': initial_email,
                            'custom_prompt': '',
                            'enabled': True,
                            'last_run': None
                        }
                        
                        if self.add_newsletter_group(group_title, emails, initial_settings):
                            st.success(f"✅ Groupe '{group_title}' créé avec {len(emails)} emails et configuration initiale")
                        else:
                            st.error("❌ Erreur lors de la création du groupe")
                    else:
                        st.error("❌ Veuillez entrer au moins un email valide")
                else:
                    st.error("❌ Veuillez entrer un titre et des emails")
        
        # Afficher les groupes existants avec configuration individuelle
        newsletter_groups = self.get_newsletter_groups()
        if newsletter_groups:
            st.markdown("#### <i class='fas fa-envelope'></i> Vos groupes de newsletters", unsafe_allow_html=True)
            
            for group in newsletter_groups:
                group_title = group.get('title', 'Sans titre')
                group_settings = group.get('settings', {})
                emails = group.get('emails', [])
                
                with st.expander(f"📧 {group_title} ({len(emails)} emails)", expanded=False):
                    # Afficher et modifier les emails du groupe
                    if emails:
                        st.markdown("**Emails de ce groupe :**")
                        
                        # Afficher les emails avec possibilité de suppression
                        for i, email in enumerate(emails):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"• {email}")
                            with col2:
                                if st.button('🗑️', key=f"remove_email_{group_title}_{i}", help="Supprimer cet email"):
                                    # Supprimer l'email
                                    updated_emails = [e for e in emails if e != email]
                                    if self.update_group_emails(group_title, updated_emails):
                                        st.success(f"Email {email} supprimé")
                                    else:
                                        st.error("Erreur lors de la suppression")
                        
                        # Ajouter un nouvel email
                        st.markdown("**Ajouter un email :**")
                        new_email = st.text_input(
                            "Nouvel email",
                            placeholder="nouvel.email@example.com",
                            key=f"new_email_{group_title}",
                            help="Entrez un nouvel email à ajouter à ce groupe"
                        )
                        
                        if st.button("Ajouter", key=f"add_email_{group_title}", type="secondary"):
                            if new_email and '@' in new_email:
                                if new_email not in emails:
                                    updated_emails = emails + [new_email]
                                    if self.update_group_emails(group_title, updated_emails):
                                        st.success(f"Email {new_email} ajouté")
                                    else:
                                        st.error("Erreur lors de l'ajout de l'email")
                                else:
                                    st.warning("Cet email existe déjà dans le groupe")
                            else:
                                st.error("Veuillez entrer un email valide")
                    
                    st.markdown("---")
                    st.markdown("#### <i class='fas fa-cog'></i> Configuration du groupe", unsafe_allow_html=True)
                    
                    # Configuration individuelle du groupe
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Fréquence
                        frequency = st.selectbox(
                            "Fréquence",
                            options=['daily', 'weekly'],
                            index=['daily', 'weekly'].index(group_settings.get('frequency', 'weekly')),
                            format_func=lambda x: {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire'}[x],
                            help="Fréquence de génération des résumés pour ce groupe",
                            key=f"freq_{group_title}"
                        )
                        
                        # Jour de la semaine (si hebdomadaire)
                        if frequency == 'weekly':
                            schedule_day = st.selectbox(
                                "Jour de la semaine",
                                options=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                                index=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(group_settings.get('schedule_day', 'monday')),
                                format_func=lambda x: {
                                    'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                                    'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
                                }[x],
                                help="Jour de la semaine pour l'envoi du résumé",
                                key=f"day_{group_title}"
                            )
                        else:
                            schedule_day = 'daily'
                        
                        # Heure d'envoi
                        time_options = []
                        for hour in range(24):
                            time_str = f"{hour:02d}:00"
                            time_options.append(time_str)
                        
                        current_time = group_settings.get('schedule_time', '09:00')
                        try:
                            current_index = time_options.index(current_time)
                        except ValueError:
                            current_index = 9  # 09:00 par défaut
                        
                        schedule_time = st.selectbox(
                            "Heure d'envoi",
                            options=time_options,
                            index=current_index,
                            help="Heure d'envoi (GitHub Actions s'exécute à l'heure pile)",
                            key=f"time_{group_title}"
                        )
                    
                    with col2:
                        # Période d'analyse
                        days_to_analyze = st.slider(
                            "Période d'analyse",
                            min_value=1,
                            max_value=7,
                            value=group_settings.get('days_to_analyze', 7),
                            help="Nombre de jours à analyser pour ce groupe",
                            key=f"days_{group_title}"
                        )
                        
                        # Email de notification
                        notification_email = st.text_input(
                            "Email de notification",
                            value=group_settings.get('notification_email', ''),
                            placeholder="votre.email@example.com",
                            help="Email pour recevoir les résumés de ce groupe",
                            key=f"email_{group_title}"
                        )
                    
                    custom_prompt = st.text_area(
                        "Instructions supplémentaires pour l'IA",
                        value=group_settings.get('custom_prompt', ''),
                        placeholder="Ajoutez ici des instructions spécifiques pour l'analyse de ce groupe (ex: 'Focus sur les actualités tech', 'Ignorez les promotions', etc.)",
                        help="Ce texte sera ajouté au prompt de base pour personnaliser l'analyse de ce groupe",
                        height=100,
                        key=f"prompt_{group_title}"
                    )

                    # Activer/Désactiver le groupe
                    enabled = st.checkbox(
                        "Activer ce groupe",
                        value=group_settings.get('enabled', True),
                        help="Désactivez pour arrêter le traitement automatique de ce groupe",
                        key=f"enabled_{group_title}"
                    )
                    
                    # Boutons d'action
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Sauvegarder", key=f"save_{group_title}", type="primary", icon=":material/save:"):
                            new_settings = {
                                'frequency': frequency,
                                'schedule_day': schedule_day,
                                'schedule_time': schedule_time,
                                'days_to_analyze': days_to_analyze,
                                'notification_email': notification_email,
                                'custom_prompt': custom_prompt,
                                'enabled': enabled,
                                'last_run': group_settings.get('last_run')
                            }
                            
                            if self.update_group_settings(group_title, new_settings):
                                st.success("Configuration sauvegardée !")
                            else:
                                st.error("Erreur lors de la sauvegarde")
                    
                    with col2:
                        if st.button("Tester ce groupe", key=f"test_{group_title}", type="secondary", icon=":material/play_arrow:"):
                            with st.spinner(f"Test du groupe '{group_title}' en cours..."):
                                result = self.process_single_group(group_title, group_settings)
                                if result and result.strip():
                                    st.success(f"Test réussi ! Résumé généré pour le groupe '{group_title}'")
                                    st.markdown("**Aperçu du résumé :**")
                                    st.markdown(result[:500] + "..." if len(result) > 500 else result, unsafe_allow_html=True)
                                else:
                                    st.warning(f"Aucun contenu trouvé pour le groupe '{group_title}'")
                    
                    with col3:
                        if st.button("Supprimer", key=f"delete_{group_title}", type="secondary", icon=":material/delete:"):
                            if self.remove_newsletter_group(group_title):
                                st.success(f"Groupe '{group_title}' supprimé")
                            else:
                                st.error("Erreur lors de la suppression")
                    
                    # Afficher les informations de planification
                    frequency_text = {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire'}[frequency]
                    if frequency == 'weekly':
                        day_text = {
                            'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                            'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
                        }[schedule_day]
                        st.info(f'Planification : {frequency_text} le {day_text} à {schedule_time} heure française (±30min)')
                    else:
                        st.info(f'Planification : {frequency_text} à {schedule_time} heure française (±30min)')
                    
                    # Dernière exécution
                    last_run = group_settings.get('last_run')
                    if last_run:
                        try:
                            last_run_date = datetime.fromisoformat(last_run)
                            st.caption(f"Dernière exécution : {last_run_date.strftime('%d/%m/%Y %H:%M')}")
                        except:
                            st.caption(f"Dernière exécution : {last_run}")
        else:
            st.info("Aucun groupe de newsletters créé. Créez-en un ci-dessus.")
    
    def get_query_for_emails(self, emails, days=7):
        """Génère la requête Gmail pour récupérer les emails"""
        date_since = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
        query = f'after:{date_since} ('
        query += ' OR '.join([f'from:{email}' for email in emails])
        query += ')'
        return query
    
    def list_messages(self, service, query):
        """Récupère la liste des messages Gmail"""
        try:
            response = service.users().messages().list(userId='me', q=query).execute()
            return response.get('messages', [])
        except Exception as e:
            st.error(f"Erreur lors de la récupération des emails: {e}")
            return []
    
    def get_message(self, service, msg_id):
        """Récupère un message Gmail spécifique"""
        try:
            return service.users().messages().get(userId='me', id=msg_id).execute()
        except Exception as e:
            st.error(f"Erreur lors de la récupération du message: {e}")
            return None
    
    def get_message_body(self, message):
        """Extrait le contenu textuel d'un message et le nettoie"""
        try:
            parts = message['payload'].get('parts', [])
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        return self.clean_email_content(content)
            else:
                content = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
                return self.clean_email_content(content)
        except Exception as e:
            st.error(f"Erreur lors de l'extraction du contenu: {e}")
            return None
    
    def clean_email_content(self, content):
        """Nettoie le contenu email pour minimiser les tokens"""
        if not content:
            return ""
        
        import re
        from bs4 import BeautifulSoup
        
        # 1. Supprimer le HTML (garder seulement le texte)
        try:
            soup = BeautifulSoup(content, 'html.parser')
            # Supprimer les scripts, styles, et métadonnées
            for script in soup(["script", "style", "meta", "head"]):
                script.decompose()
            content = soup.get_text()
        except:
            # Si BeautifulSoup échoue, utiliser regex simple
            content = re.sub(r'<[^>]+>', '', content)
        
        # 2. Supprimer les headers d'email
        lines = content.split('\n')
        cleaned_lines = []
        in_body = False
        
        for line in lines:
            # Détecter le début du corps (après les headers)
            if not in_body and (line.strip() == '' or 
                              not line.startswith(('From:', 'To:', 'Subject:', 'Date:', 'Message-ID:', 'X-', 'Return-Path:', 'Received:'))):
                in_body = True
            
            if in_body:
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # 3. Supprimer les signatures communes
        signature_patterns = [
            r'(?i)sent from my .*',
            r'(?i)envoyé depuis mon .*',
            r'(?i)get outlook for .*',
            r'(?i)disponible sur .*',
            r'(?i)powered by .*',
            r'(?i)confidentialité.*',
            r'(?i)privacy.*',
            r'(?i)unsubscribe.*',
            r'(?i)désabonnement.*',
            r'(?i)vous recevez cet email.*',
            r'(?i)this email was sent.*',
        ]
        
        for pattern in signature_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # 4. Nettoyer les espaces et lignes vides
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Max 2 sauts de ligne
        content = re.sub(r'[ \t]+', ' ', content)  # Normaliser les espaces
        content = content.strip()
        
        # 5. Supprimer les URLs longues (garder seulement le texte des liens)
        content = re.sub(r'https?://[^\s]+', '[LIEN]', content)
        
        # 6. Supprimer les caractères de contrôle et spéciaux
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        
        print(f"🧹 DEBUG: Contenu nettoyé - Avant: {len(content)} caractères")
        
        return content
    
    def resolve_url(self, url):
        """Résout les URLs de redirection"""
        try:
            response = requests.get(url, headers=self.config.HEADERS, 
                                  allow_redirects=True, timeout=10)
            if response.url == url:
                match = re.search(r'URL=([^"]+)', response.text)
                if match:
                    return match.group(1).split('?')[0]
                else:
                    return url
            else:
                return response.url
        except requests.RequestException:
            return url
    
    def replace_redirected_links(self, summary):
        """Remplace les liens de redirection par les URLs finales"""
        pattern = re.compile(r'(https?://\S*redirect\S*)')
        matches = pattern.findall(summary)
        for match in matches:
            resolved_url = self.resolve_url(match)
            summary = summary.replace(match, resolved_url)
        return summary
    
    def is_promotional_email(self, message):
        """Détecte si un email est promotionnel en analysant le sujet"""
        try:
            # Extraire le sujet
            headers = message['payload'].get('headers', [])
            subject = ""
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                    break
            
            # Détection par mots-clés dans le sujet uniquement
            is_promotional = self.is_promotional_basic(subject, "")
            print(f"🔍 DEBUG: Classification email - Sujet: '{subject[:50]}...' → {'PROMOTIONNEL' if is_promotional else 'EDITORIAL'}")
            return is_promotional
            
        except Exception as e:
            print(f"❌ DEBUG: Erreur classification email: {e}")
            # En cas d'erreur, considérer comme non-promotionnel pour ne pas perdre de contenu
            return False
    
    def is_promotional_basic(self, subject, content):
        """Détection basique par mots-clés (fallback si l'IA échoue)"""
        promotional_keywords = [
            # Mots-clés de réduction/offre
            'offre', 'réduction', 'promo', 'code', 'rabais', 'discount', 'remise',
            'moitié prix', 'prix cassé', 'prix barré', 'économie', 'économisez',
            'profitez', 'spécial', 'limité', 'urgent', 'flash', 'éclair',
            
            # Mots-clés d'achat/vente
            'vente', 'achat', 'commander', 'boutique', 'shop', 'store', 'magasin',
            'commande', 'panier', 'ajouter au panier', 'livraison', 'expédition',
            'paiement', 'carte bancaire', 'cb', 'paypal', 'stripe',
            
            # Mots-clés promotionnels
            'gratuit', 'free', 'deal', 'bargain', 'sale', 'clearance', 'liquidation',
            'soldes', 'promotion', 'cadeau', 'gift', 'bonus', 'prime',
            'exclusif', 'exclusive', 'réservé', 'private', 'vip',
            
            # Mots-clés d'urgence/pression
            'dépêchez-vous', 'hâtez-vous', 'fin', 'dernière', 'dernières heures',
            'bientôt fini', 'stock limité', 'quantité limitée', 'plus que',
            'ne manquez pas', 'occasion unique', 'une seule fois',
            
            # Mots-clés d'abonnement
            'abonnement', 'subscription', 's\'abonner', 'subscribe', 'newsletter',
            'inscription', 'inscrivez-vous', 'rejoignez', 'join', 'adhésion',
            
            # Mots-clés commerciaux
            'client', 'customer', 'satisfaction', 'garantie', 'warranty',
            'service client', 'support', 'aide', 'help', 'contact',
            'devis', 'quote', 'estimation', 'tarif', 'prix'
        ]
        
        text_to_analyze = f"{subject}".lower()
        
        for keyword in promotional_keywords:
            if keyword in text_to_analyze:
                print(f"🔍 DEBUG: Mot-clé promotionnel détecté: '{keyword}'")
                return True
        
        print(f"🔍 DEBUG: Aucun mot-clé promotionnel détecté")
        return False
    
    def summarize_newsletter(self, content, custom_prompt=""):
        """Utilise OpenAI pour extraire les actualités IA"""
        if len(content) > 32000:
            content = content[:32000]
        
        # Template HTML pour l'email
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { padding: 20px; text-align: center; margin-bottom: 20px; }
                .header img { max-width: 80px; vertical-align: middle; margin-right: 10px; }
                .header .brand { display: inline-block; vertical-align: middle; font-weight: bold; color: #667eea; font-size: 24px; }
                .header .subtitle { color: #666; font-size: 18px; margin-top: 5px; }
                .section { background: #f8f9fa; margin: 15px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea; }
                .section-title { color: #2c3e50; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
                .section-content { color: #555; }
                .footer { padding: 15px; text-align: center; margin-top: 20px; }
                .footer .subtitle { color: #666; font-size: 14px; margin-top: 5px; }
                a { color: #667eea; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="header">
                <img src="https://raw.githubusercontent.com/AlexisMetton/AutoBrief/main/public/assets/logo_autobrief.png" alt="AutoBrief">
                <span class="brand">AutoBrief</span>
                <div class="subtitle">Actualités du {date}</div>
            </div>
            
            {sections}
            
            <div class="footer">
                <div class="subtitle">Généré automatiquement par AutoBrief</div>
            </div>
        </body>
        </html>
        """
        
        # Prompt de base amélioré
        base_prompt = f"""Analysez la newsletter suivante et extrayez toutes les actualités importantes. 
            Ne gardez AUCUN lien dans le résumé. Supprimez tous les liens d'affiliation, 
            d'auto-promotion, substack, liens vers d'autres articles du même auteur et tous les autres liens. 
            Ne gardez pas de référence à l'auteur, à la newsletter ou à substack.
            
            IMPORTANT: 
            - Le résumé doit être en français
            - Gardez toutes les informations importantes et résumez-les ou expliquez-les
            - IMPORTANT: Ne mettez AUCUN lien dans le contenu, seulement le texte des actualités
            - Vous DEVEZ utiliser EXACTEMENT ce template HTML pour votre réponse :
            
            {html_template}
            
            - Remplacez {{date}} par la date actuelle (format: DD/MM/YYYY)
            - Remplacez {{sections}} par vos sections d'actualités
            - Chaque actualité doit être dans une div avec class="section"
            - Chaque section doit avoir un titre dans une div avec class="section-title"
            - Le contenu va dans une div avec class="section-content"
            - Une actualité par section
            - IMPORTANT: Retournez TOUT le HTML complet, pas juste les sections
            - COMMENCEZ DIRECTEMENT par <!DOCTYPE html> - ne mettez rien avant
            - Si aucune actualité importante n'est trouvée, retournez une chaîne vide
            
            EXEMPLE de structure attendue :
            <div class="section">
                <div class="section-title">Titre de l'actualité</div>
                <div class="section-content">Résumé avec liens...</div>
            </div>
            
            Retournez votre réponse sous forme de JSON avec la structure suivante :
            {{"result": "votre_html_complet_ici"}}"""
        
        # Ajouter le prompt personnalisé s'il existe
        if custom_prompt and custom_prompt.strip():
            full_prompt = f"{base_prompt}\n\nInstructions supplémentaires: {custom_prompt.strip()}\n\n{content}\n\nGénérez un email HTML complet en français avec toutes les actualités importantes trouvées. COMMENCEZ DIRECTEMENT par <!DOCTYPE html>. Retournez le résultat en JSON avec la clé 'result'. Si aucune actualité importante n'est trouvée, retournez {{'result': ''}}."
        else:
            full_prompt = f"{base_prompt}\n\n{content}\n\nGénérez un email HTML complet en français avec toutes les actualités importantes trouvées. COMMENCEZ DIRECTEMENT par <!DOCTYPE html>. Retournez le résultat en JSON avec la clé 'result'. Si aucune actualité importante n'est trouvée, retournez {{'result': ''}}."
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": full_prompt}
        ]
        
        try:
            print(f"🔍 DEBUG: Appel OpenAI avec {len(full_prompt)} caractères de prompt")
            if hasattr(st, 'info'):
                st.info(f"🔍 Appel OpenAI avec {len(full_prompt)} caractères")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_format={"type": "json_object"},
                messages=messages,
            )
            
            print(f"🔍 DEBUG: Réponse OpenAI reçue")
            if hasattr(st, 'info'):
                st.info("📡 Réponse OpenAI reçue")
            
            # Vérifier que la réponse n'est pas vide
            response_content = response.choices[0].message.content
            if not response_content or response_content.strip() == "":
                print(f"❌ DEBUG: Réponse OpenAI vide")
                if hasattr(st, 'error'):
                    st.error("❌ Réponse OpenAI vide")
                return ""
            
            print(f"🔍 DEBUG: Contenu réponse: '{response_content[:100]}...'")
            if hasattr(st, 'info'):
                st.info(f"📄 Contenu reçu: '{response_content[:100]}...'")
            
            # Afficher la réponse complète de ChatGPT
            print(f"🔍 DEBUG: RÉPONSE COMPLÈTE CHATGPT:")
            print(f"'{response_content}'")
            if hasattr(st, 'write'):
                st.write("🔍 **Réponse complète ChatGPT:**")
                st.code(response_content, language="json")
            
            try:
                data = json.loads(response_content)
                print(f"🔍 DEBUG: JSON parsé: {list(data.keys())}")
                if hasattr(st, 'info'):
                    st.info(f"✅ JSON parsé: {list(data.keys())}")
            except json.JSONDecodeError as json_error:
                print(f"❌ DEBUG: Erreur parsing JSON: {json_error}")
                print(f"❌ DEBUG: Contenu reçu: '{response_content}'")
                if hasattr(st, 'error'):
                    st.error(f"❌ Erreur JSON: {json_error}")
                    st.error(f"Contenu: {response_content}")
                return ""
            
            if 'result' in data and isinstance(data['result'], str):
                result = data['result']
                print(f"🔍 DEBUG: Résultat IA: {len(result)} caractères")
                print(f"🔍 DEBUG: Premiers 200 caractères: {result[:200]}...")
                
                if len(result.strip()) == 0:
                    if hasattr(st, 'warning'):
                        st.warning("⚠️ L'IA a retourné une chaîne vide")
                    return ""
                
                # Debug pour voir ce que l'IA génère
                if hasattr(st, 'write'):
                    st.write(f"🔍 Debug: HTML généré par l'IA (premiers 500 caractères): {result[:500]}...")
                return result
            else:
                print(f"❌ DEBUG: Pas de 'result' valide dans la réponse: {data}")
                if hasattr(st, 'error'):
                    st.error(f"❌ Pas de 'result' valide: {data}")
                return ""
        except Exception as e:
            print(f"❌ DEBUG: Erreur OpenAI: {e}")
            if hasattr(st, 'error'):
                st.error(f"Erreur OpenAI: {e}")
            return ""
    
    def process_newsletters_scheduler(self, days=7, send_email=False):
        """Version simplifiée pour le scheduler (sans Streamlit)"""
        print(f"🔍 DEBUG: process_newsletters_scheduler démarré - days={days}, send_email={send_email}")
        
        # Traiter tous les groupes qui doivent être exécutés
        newsletter_groups = self.get_newsletter_groups()
        if not newsletter_groups:
            print("❌ DEBUG: Aucun groupe de newsletters configuré")
            return None
        
        results = []
        for group in newsletter_groups:
            group_title = group.get('title', '')
            group_settings = group.get('settings', {})
            
            print(f"🔄 DEBUG: Traitement du groupe '{group_title}'")
            
            # Traiter ce groupe spécifique
            group_result = self.process_single_group(group_title, group_settings)
            if group_result:
                results.append({
                    'group_title': group_title,
                    'result': group_result
                })
                
                # Mettre à jour la date de dernière exécution pour ce groupe
                self.update_group_last_run(group_title)
        
        return results if results else None
    
    def process_single_group(self, group_title, group_settings):
        """Traite un groupe de newsletters spécifique"""
        try:
            # Récupérer les emails du groupe
            newsletter_groups = self.get_newsletter_groups()
            group_emails = []
            for group in newsletter_groups:
                if group.get('title') == group_title:
                    group_emails = group.get('emails', [])
                    break
            
            if not group_emails:
                print(f"❌ DEBUG: Aucun email trouvé pour le groupe '{group_title}'")
                return None
            
            print(f"✅ DEBUG: Groupe '{group_title}' avec {len(group_emails)} emails: {group_emails}")
            
            service = self.auth.get_gmail_service()
            if not service:
                print("❌ DEBUG: Impossible d'obtenir le service Gmail")
                return None
            
            # Récupérer les paramètres du groupe
            days_to_analyze = group_settings.get('days_to_analyze', 7)
            custom_prompt = group_settings.get('custom_prompt', '')
            notification_email = group_settings.get('notification_email', '')
            
            print(f"🔍 DEBUG: Paramètres groupe - jours: {days_to_analyze}, prompt: '{custom_prompt[:50]}...'")
            
            # Créer la requête pour ce groupe
            query = self.get_query_for_emails(group_emails, days_to_analyze)
            print(f"🔍 DEBUG: Requête Gmail pour groupe: {query}")
            
            # Récupérer les messages
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            print(f"🔍 DEBUG: {len(messages)} messages trouvés pour le groupe")
            
            if not messages:
                print(f"❌ DEBUG: Aucun message trouvé pour le groupe '{group_title}'")
                return None
            
            # Filtrer les emails promotionnels
            filtered_messages = []
            for idx, msg in enumerate(messages):
                print(f"🔍 DEBUG: Analyse message {idx + 1}/{len(messages)} du groupe")
                message = self.get_message(service, msg['id'])
                
                if message:
                    is_promotional = self.is_promotional_email(message)
                    if is_promotional:
                        print(f"🚫 DEBUG: Email {idx + 1} détecté comme promotionnel - ignoré")
                    else:
                        print(f"✅ DEBUG: Email {idx + 1} validé comme contenu éditorial")
                        filtered_messages.append(msg)
                else:
                    print("❌ DEBUG: Impossible de récupérer le message")
            
            print(f"🔍 DEBUG: {len(filtered_messages)}/{len(messages)} emails non-promotionnels trouvés pour le groupe")
            
            # Traiter seulement les emails non-promotionnels
            all_content = ""
            for idx, msg in enumerate(filtered_messages):
                print(f"🔍 DEBUG: Extraction contenu éditorial {idx + 1}/{len(filtered_messages)} du groupe")
                message = self.get_message(service, msg['id'])
                
                if message:
                    body = self.get_message_body(message)
                    if body:
                        print(f"🔍 DEBUG: Corps du message extrait ({len(body)} caractères)")
                        if all_content:
                            all_content += "\n\n--- NOUVEL EMAIL ---\n\n"
                        all_content += body
                        print(f"✅ DEBUG: Contenu éditorial ajouté")
                    else:
                        print("❌ DEBUG: Impossible d'extraire le corps du message")
                else:
                    print("❌ DEBUG: Impossible de récupérer le message")
            
            print(f"🔍 DEBUG: Contenu éditorial du groupe: {len(all_content)} caractères")
            
            # Générer le résumé pour ce groupe
            if all_content.strip():
                print(f"🔍 DEBUG: Génération du résumé pour le groupe '{group_title}'...")
                output = self.summarize_newsletter(all_content, custom_prompt)
                print(f"🔍 DEBUG: Résumé du groupe généré: {len(output) if output else 0} caractères")
                
                # Envoyer par email si configuré
                if output and notification_email and notification_email.strip():
                    self.send_summary_email(output, notification_email, group_title)
                
                return output
            else:
                print(f"❌ DEBUG: Aucun contenu éditorial trouvé pour le groupe '{group_title}'")
                return None
                
        except Exception as e:
            print(f"❌ DEBUG: Erreur lors du traitement du groupe '{group_title}': {e}")
            return None
    
    def update_group_last_run(self, group_title):
        """Met à jour la date de dernière exécution d'un groupe"""
        self.update_group_settings(group_title, {'last_run': datetime.now().isoformat()})
    
    def update_group_emails(self, group_title, new_emails):
        """Met à jour les emails d'un groupe"""
        newsletter_groups = self.get_newsletter_groups()
        for group in newsletter_groups:
            if group.get('title') == group_title:
                group['emails'] = new_emails
                self.save_newsletter_groups(newsletter_groups)
                return True
        return False
    
    def cleanup_old_data(self):
        """Nettoie les anciens paramètres globaux et ne garde que la structure par groupes"""
        try:
            user_data = self.load_user_data()
            
            # Créer une nouvelle structure propre
            cleaned_data = {
                'newsletter_groups': user_data.get('newsletter_groups', []),
                'oauth_credentials': user_data.get('oauth_credentials', {})
            }
            
            # Sauvegarder les données nettoyées
            if self.save_user_data(cleaned_data):
                if hasattr(st, 'success'):
                    st.success("✅ Données nettoyées ! Anciens paramètres globaux supprimés.")
                return True
            else:
                if hasattr(st, 'error'):
                    st.error("❌ Erreur lors du nettoyage des données")
                return False
                
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"❌ Erreur lors du nettoyage: {e}")
            return False

    def process_newsletters(self, days=7, send_email=False):
        """Traite toutes les newsletters et génère le résumé (version compatible avec l'ancien système)"""
        # Vérifier l'authentification avant de continuer
        if not hasattr(st, 'session_state') or not st.session_state.get('authenticated', False):
            # Si on n'est pas dans un contexte Streamlit ou pas authentifié, 
            # on est probablement dans le scheduler - continuer silencieusement
            if hasattr(st, 'error'):
                return None
        
        # Utiliser la nouvelle logique par groupes
        newsletter_groups = self.get_newsletter_groups()
        if not newsletter_groups:
            if hasattr(st, 'error'):
                st.error("Aucun groupe de newsletters configuré")
            else:
                print("❌ Aucun groupe de newsletters configuré")
            return None
        
        # Traiter tous les groupes qui doivent être exécutés
        results = []
        for group in newsletter_groups:
            group_title = group.get('title', '')
            group_settings = group.get('settings', {})
                        
            if hasattr(st, 'info'):
                st.info(f"🔄 Traitement du groupe '{group_title}'")
            
            # Traiter ce groupe spécifique
            group_result = self.process_single_group(group_title, group_settings)
            if group_result:
                results.append({
                    'group_title': group_title,
                    'result': group_result
                })
                
                # Mettre à jour la date de dernière exécution pour ce groupe
                self.update_group_last_run(group_title)
        
        # Retourner le premier résultat pour la compatibilité avec l'ancien système
        if results:
            return results[0]['result']
        else:
            return None
    
    
    def send_summary_email(self, summary, notification_email, group_title=None):
        """Envoie le résumé par email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            # Configuration Gmail (utilise les mêmes credentials OAuth2)
            service = self.auth.get_gmail_service()
            if not service:
                if hasattr(st, 'error'):
                    st.error("Impossible d'accéder à Gmail pour l'envoi")
                return False
            
            # Créer le message
            message = MIMEMultipart()
            message['From'] = service.users().getProfile(userId='me').execute()['emailAddress']
            message['To'] = notification_email
            
            # Sujet avec nom du groupe si fourni
            if group_title:
                message['Subject'] = f"Résumé AutoBrief - {group_title} - {datetime.now().strftime('%d/%m/%Y')}"
            else:
                message['Subject'] = f"Résumé AutoBrief - {datetime.now().strftime('%d/%m/%Y')}"
            
            # Corps du message HTML
            # Si le summary contient déjà du HTML, l'utiliser directement
            if '<html>' in summary.lower() or '<body>' in summary.lower():
                # Le summary est déjà en HTML, l'utiliser directement
                message.attach(MIMEText(summary, 'html', 'utf-8'))
            else:
                # Sinon, créer un HTML basique
                group_info = f" - {group_title}" if group_title else ""
                body = f"""
                <html>
                <body>
                <h2>Résumé AutoBrief{group_info} - {datetime.now().strftime('%d/%m/%Y')}</h2>
                <p>Bonjour,</p>
                <p>Voici votre résumé automatique des newsletters :</p>
                <div>{summary}</div>
                <hr>
                <p><em>Généré automatiquement par AutoBrief</em></p>
                <img src="https://raw.githubusercontent.com/AlexisMetton/AutoBrief/main/public/assets/logo_autobrief.png" alt="AutoBrief" style="max-width: 200px;">
                </body>
                </html>
                """
                message.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Encoder le message
            raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            
            # Envoyer l'email
            sent_message = service.users().messages().send(userId='me', body=raw_message).execute()
            
            if hasattr(st, 'success'):
                st.success(f"Résumé envoyé par email à {notification_email}")
            return True
            
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"Erreur lors de l'envoi: {e}")
            return False

