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
        
        # Vérifier la configuration du Gist au démarrage
        self.check_gist_configuration()
    
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
            else:
                st.warning("Aucune donnée trouvée dans le Gist")
        except Exception as e:
            st.error(f"Erreur lors du rechargement automatique: {e}")
    
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
                    'newsletters': [],
                    'settings': {
                        'frequency': 'weekly',
                        'days_to_analyze': 7,
                        'notification_email': '',
                        'last_run': None,
                        'auto_send': True,
                        'schedule_day': 'monday',
                        'schedule_time': '09:00',
                        'schedule_timezone': 'UTC'
                    }
                }
                # Mettre en cache les données par défaut
                st.session_state['user_data_cache'] = default_data
                return default_data
                    
        except Exception as e:
            # En cas d'erreur, retourner des données par défaut
            return {
                'newsletters': [],
                'settings': {
                    'frequency': 'weekly',
                    'days_to_analyze': 7,
                    'notification_email': '',
                    'last_run': None,
                    'auto_send': True,
                    'schedule_day': 'monday',
                    'schedule_time': '09:00',
                    'schedule_timezone': 'UTC'
                }
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
            except:
                pass
            
            # Fallback sur les variables d'environnement (pour GitHub Actions)
            if not gist_id:
                gist_id = os.getenv('GIST_ID')
            
            # Fallback sur la session state
            if not gist_id:
                gist_id = st.session_state.get('gist_id')
            
            if not gist_id:
                return None
            
            import requests
            response = requests.get(f'https://api.github.com/gists/{gist_id}')
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(content) if content else {}
                    
                    # Retourner les données de cet utilisateur spécifique
                    if self.user_email in all_users_data:
                        return all_users_data[self.user_email]
                    else:
                        # Utilisateur pas encore dans le Gist - retourner des données par défaut
                        return {
                            'newsletters': [],
                            'settings': {
                                'frequency': 'weekly',
                                'days_to_analyze': 7,
                                'notification_email': '',
                                'last_run': None,
                                'auto_send': True,
                                'schedule_day': 'monday',
                                'schedule_time': '09:00',
                                'schedule_timezone': 'UTC'
                            }
                        }
            return None
        except:
            return None
    
    def save_user_data(self, data):
        """Sauvegarde les données utilisateur directement dans le Gist"""
        try:
            # En mode scheduler, ne pas sauvegarder
            if self._scheduler_mode:
                return True
            
            # Sauvegarder les credentials OAuth2 si disponibles (uniquement dans Streamlit)
            if hasattr(st, 'session_state') and 'encrypted_token' in st.session_state and st.session_state['encrypted_token']:
                try:
                    # Décrypter le token pour récupérer les credentials
                    decrypted_token = self.auth.decrypt_token(st.session_state['encrypted_token'])
                    if decrypted_token:
                        # Ajouter les credentials OAuth2 aux données utilisateur (chiffrés)
                        # Chiffrer les données sensibles avant de les sauvegarder dans le Gist
                        encrypted_credentials = self.auth.encrypt_token(decrypted_token)
                        
                        data['oauth_credentials'] = {
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
            success = self.save_to_github_gist(data)
            
            if success:
                if hasattr(st, 'success'):
                    st.success("Données sauvegardées automatiquement !")
            else:
                if hasattr(st, 'error'):
                    st.error("Erreur lors de la sauvegarde dans le Gist")
            
            return success
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    
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
                    if hasattr(st, 'success'):
                        st.success("Données sauvegardées automatiquement dans le Gist !")
                    return True
                else:
                    if hasattr(st, 'error'):
                        st.error(f"Erreur lors de la mise à jour du Gist: {update_response.status_code}")
                        st.info("Vérifiez que le token Gist est correct dans les secrets")
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
        
    def get_newsletters(self):
        """Récupère la liste des newsletters depuis le Gist"""
        # Charger les données utilisateur depuis le Gist
        user_data = self.load_user_data()
        return user_data.get('newsletters', [])
    
    def get_user_settings(self):
        """Récupère les paramètres utilisateur"""
        user_data = self.load_user_data()
        return user_data.get('settings', {
            'frequency': 'weekly',
            'days_to_analyze': 7,
            'notification_email': '',
            'last_run': None,
            'auto_send': True
        })
    
    def save_user_settings(self, settings):
        """Sauvegarde les paramètres utilisateur"""
        user_data = self.load_user_data()
        user_data['settings'] = settings
        return self.save_user_data(user_data)
    
    def should_run_automatically(self):
        """Vérifie si un résumé automatique doit être généré"""
        settings = self.get_user_settings()
        
        if not settings.get('auto_send', False):
            return False
        
        last_run = settings.get('last_run')
        if not last_run:
            return True
        
        try:
            last_run_date = datetime.fromisoformat(last_run)
            frequency = settings.get('frequency', 'weekly')
            
            # Vérifier si c'est le bon jour et la bonne heure
            if not self.is_scheduled_time(settings):
                return False
            
            if frequency == 'daily':
                return datetime.now() - last_run_date >= timedelta(days=1)
            elif frequency == 'weekly':
                return datetime.now() - last_run_date >= timedelta(weeks=1)
            elif frequency == 'monthly':
                return datetime.now() - last_run_date >= timedelta(days=30)
        except:
            return True
        
        return False
    
    def is_scheduled_time(self, settings):
        """Vérifie si c'est le bon jour et la bonne heure pour l'exécution"""
        try:
            schedule_day = settings.get('schedule_day', 'monday')
            schedule_time = settings.get('schedule_time', '09:00')
            
            now = datetime.now()
            current_day = now.strftime('%A').lower()
            current_time = now.strftime('%H:%M')
            
            # Vérifier le jour (pour les fréquences weekly/monthly)
            if settings.get('frequency', 'weekly') in ['weekly', 'monthly']:
                if current_day != schedule_day.lower():
                    return False
            
            # Vérifier l'heure (avec une marge de 30 minutes pour GitHub Actions)
            target_hour = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            current_hour = now.hour
            current_minute = now.minute
            
            # GitHub Actions s'exécute à l'heure pile, on accepte +/- 30 minutes
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour * 60 + target_minute))
            return time_diff <= 30
            
        except Exception as e:
            st.error(f"Erreur vérification horaire: {e}")
            return True  # En cas d'erreur, on autorise l'exécution
    
    def add_newsletter(self, email):
        """Ajoute une newsletter à la liste"""
        newsletters = self.get_newsletters()
        if email and email not in newsletters:
            newsletters.append(email)
            self.save_newsletters(newsletters)
            return True
        return False
    
    def remove_newsletter(self, email):
        """Supprime une newsletter de la liste"""
        newsletters = self.get_newsletters()
        if email in newsletters:
            newsletters.remove(email)
            self.save_newsletters(newsletters)
            return True
        return False
    
    def render_newsletter_management(self):
        """Interface de gestion des newsletters"""
        
        # Ajouter une newsletter
        with st.expander('Ajouter une newsletter', expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_email = st.text_input(
                    "Email de la newsletter:",
                    placeholder="exemple@newsletter.com",
                    help="Entrez l'adresse email qui vous envoie les newsletters"
                )
            with col2:
                if st.button("Ajouter", type="primary", icon=":material/add:"):
                    if new_email and "@" in new_email:
                        if self.add_newsletter(new_email):
                            st.success(f"Newsletter {new_email} ajoutée")
                            st.rerun()
                        else:
                            pass
                    else:
                        st.error("Veuillez entrer une adresse email valide")
        
        # Liste des newsletters
        newsletters = self.get_newsletters()
        if newsletters:
            st.markdown("#### <i class='fas fa-envelope'></i> Newsletters surveillées", unsafe_allow_html=True)
            for i, email in enumerate(newsletters):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{email}")
                with col2:
                    if st.button("Supprimer", key=f"delete_{i}", icon=":material/delete:"):
                        self.remove_newsletter(email)
                        st.rerun()
        else:
            pass
        
        
        settings = self.get_user_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            
            frequency = st.selectbox(
                "Fréquence",
                options=['daily', 'weekly'],
                index=['daily', 'weekly'].index(settings.get('frequency', 'weekly')),
                format_func=lambda x: {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire'}[x],
                help="Fréquence de génération des résumés"
            )
            
            # Configuration du jour et de l'heure
            if frequency == 'weekly':
                schedule_day = st.selectbox(
                    "Jour de la semaine",
                    options=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                    index=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(settings.get('schedule_day', 'monday')),
                    format_func=lambda x: {
                        'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                        'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
                    }[x],
                    help="Jour de la semaine pour l'envoi du résumé"
                )
                schedule_days = [schedule_day]
            else:
                schedule_day = 'daily'
                schedule_days = ['daily']
            
            schedule_time = st.time_input(
                "Heure d'envoi (UTC)",
                value=datetime.strptime(settings.get('schedule_time', '09:00'), '%H:%M').time(),
                help="Heure d'envoi en UTC (GitHub Actions s'exécute à 09:00 UTC par défaut)"
            )
        
        with col2:
            days_to_analyze = st.slider(
                "Période d'analyse",
                min_value=1,
                max_value=30,
                value=settings.get('days_to_analyze', 7),
                help="Nombre de jours à analyser pour chaque résumé"
            )
            
            notification_email = st.text_input(
                "Email de notification",
                value=settings.get('notification_email', ''),
                placeholder="votre.email@example.com",
                help="Email pour recevoir les résumés automatiques (optionnel)"
            )
        
        # Prompt personnalisé
        st.markdown("#### <i class='fas fa-edit'></i> Prompt personnalisé", unsafe_allow_html=True)
        custom_prompt = st.text_area(
            "Instructions supplémentaires pour l'IA",
            value=settings.get('custom_prompt', ''),
            placeholder="Ajoutez ici des instructions spécifiques pour l'analyse des newsletters (ex: 'Focus sur les actualités tech', 'Ignorez les promotions', etc.)",
            help="Ce texte sera ajouté au prompt de base pour personnaliser l'analyse des newsletters",
            height=100
        )
        
        # Sauvegarder les paramètres
        if st.button("Sauvegarder les paramètres", type="primary", icon=":material/save:"):
            new_settings = {
                'auto_send': True,  # Toujours activé
                'frequency': frequency,
                'days_to_analyze': days_to_analyze,
                'notification_email': notification_email,
                'custom_prompt': custom_prompt,
                'last_run': settings.get('last_run'),
                'schedule_day': schedule_day,
                'schedule_time': schedule_time.strftime('%H:%M'),
                'schedule_timezone': 'UTC'
            }
            
            if self.save_user_settings(new_settings):
                st.success("Paramètres sauvegardés !")
                st.rerun()
            else:
                st.error("Erreur lors de la sauvegarde")
        
        # Statut de la planification
        frequency_text = {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire'}[frequency]
        
        # Convertir l'heure UTC vers l'heure de Paris (UTC+1/+2)
        import pytz
        utc_time = pytz.UTC.localize(datetime.combine(datetime.today(), schedule_time))
        paris_tz = pytz.timezone('Europe/Paris')
        paris_time = utc_time.astimezone(paris_tz)
        
        if frequency == 'weekly':
            day_text = {
                'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
            }[schedule_day]
            st.info(f"Planification : {frequency_text} le {day_text} à {paris_time.strftime('%H:%M')} heure de Paris (±30min)")
        else:
            st.info(f"Planification : {frequency_text} à {paris_time.strftime('%H:%M')} heure de Paris (±30min)")
        
        # Note sur la tolérance
        st.caption("Tolérance de ±30 minutes pour compenser les délais d'automatisation GitHub Actions")
    
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
        """Extrait le contenu textuel d'un message"""
        try:
            parts = message['payload'].get('parts', [])
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            else:
                return base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        except Exception as e:
            st.error(f"Erreur lors de l'extraction du contenu: {e}")
            return None
    
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
    
    def summarize_newsletter(self, content, custom_prompt=""):
        """Utilise OpenAI pour extraire les actualités IA"""
        if len(content) > 32000:
            content = content[:32000]
        
        # Prompt de base
        base_prompt = """From the following newsletter, extract all the news related to AI while keeping the 
            links to sources of information. Do not keep any affiliate links, self-promotion links, substack links and links to other articles by 
            the same author. Do not keep reference to the author, the newsletter or substack:"""
        
        # Ajouter le prompt personnalisé s'il existe
        if custom_prompt and custom_prompt.strip():
            full_prompt = f"{base_prompt}\n\nAdditional instructions: {custom_prompt.strip()}\n\n{content}\nYou will output result as a JSON object, a dictionary with a single key 'result' which yields the extraction as a string. If there is no AI news in the newsletter, output an empty string."
        else:
            full_prompt = f"{base_prompt}\n\n{content}\nYou will output result as a JSON object, a dictionary with a single key 'result' which yields the extraction as a string. If there is no AI news in the newsletter, output an empty string."
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": full_prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_format={"type": "json_object"},
                messages=messages,
            )
            
            data = json.loads(response.choices[0].message.content)
            if 'result' in data and isinstance(data['result'], str):
                return data['result']
            else:
                return ""
        except Exception as e:
            st.error(f"Erreur OpenAI: {e}")
            return ""
    
    def process_newsletters_scheduler(self, days=7, send_email=False):
        """Version simplifiée pour le scheduler (sans Streamlit)"""
        newsletters = self.get_newsletters()
        if not newsletters:
            return None
        
        service = self.auth.get_gmail_service()
        if not service:
            return None
        
        # Récupérer le prompt personnalisé
        settings = self.get_user_settings()
        custom_prompt = settings.get('custom_prompt', '')
        
        # Créer la requête
        query = self.get_query_for_emails(newsletters, days)
        
        # Récupérer les messages
        try:
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return None
            
            # Traiter chaque message
            output = ""
            for idx, msg in enumerate(messages):
                message = self.get_message(service, msg['id'])
                
                if message:
                    body = self.get_message_body(message)
                    if body:
                        summary = self.summarize_newsletter(body, custom_prompt)
                        if summary and len(summary.strip()) > 0:
                            summary = self.replace_redirected_links(summary)
                            output += f"**Source {idx + 1}:**\n{summary}\n\n"
            
            # Envoyer par email si demandé
            if output and send_email:
                notification_email = settings.get('notification_email')
                if notification_email and notification_email.strip():
                    self.send_summary_email(output, notification_email)
            
            return output if output.strip() else None
        except Exception as e:
            return None

    def process_newsletters(self, days=7, send_email=False):
        """Traite toutes les newsletters et génère le résumé"""
        # Vérifier l'authentification avant de continuer
        if not hasattr(st, 'session_state') or not st.session_state.get('authenticated', False):
            # Si on n'est pas dans un contexte Streamlit ou pas authentifié, 
            # on est probablement dans le scheduler - continuer silencieusement
            if hasattr(st, 'error'):
                return None
        
        newsletters = self.get_newsletters()
        if not newsletters:
            if hasattr(st, 'error'):
                st.error("Aucune newsletter configurée")
            else:
                print("❌ Aucune newsletter configurée")
            return None
        
        service = self.auth.get_gmail_service()
        if not service:
            if hasattr(st, 'error'):
                st.error("Impossible de se connecter à Gmail")
            else:
                print("❌ Impossible de se connecter à Gmail")
            return None
        
        # Récupérer le prompt personnalisé
        settings = self.get_user_settings()
        custom_prompt = settings.get('custom_prompt', '')
        
        # Créer la requête
        query = self.get_query_for_emails(newsletters, days)
        
        
        # Récupérer les messages
        if hasattr(st, 'spinner'):
            with st.spinner("Recherche des emails..."):
                messages = self.list_messages(service, query)
        else:
            messages = self.list_messages(service, query)
        
        if not messages:
            if hasattr(st, 'warning'):
                st.warning("Aucun email trouvé pour la période sélectionnée")
            else:
                print("Aucun email trouvé pour la période sélectionnée")
            return None
        
        if hasattr(st, 'success'):
            st.success(f"{len(messages)} emails trouvés")
        else:
            print(f"{len(messages)} emails trouvés")
        
        # Traiter chaque message
        output = ""
        if hasattr(st, 'progress'):
            progress_bar = st.progress(0)
        else:
            progress_bar = None
        
        for idx, msg in enumerate(messages):
            if hasattr(st, 'spinner'):
                with st.spinner(f"Traitement de l'email {idx + 1}/{len(messages)}..."):
                    message = self.get_message(service, msg['id'])
            else:
                message = self.get_message(service, msg['id'])
            
                if message:
                    body = self.get_message_body(message)
                    if body:
                        summary = self.summarize_newsletter(body, custom_prompt)
                        if summary and len(summary.strip()) > 0:
                            summary = self.replace_redirected_links(summary)
                            output += f"**Source {idx + 1}:**\n{summary}\n\n"
            
            if progress_bar:
                progress_bar.progress((idx + 1) / len(messages))
        
        # Mettre à jour la date de dernière exécution
        if output:
            self.update_last_run()
        
        # Envoyer par email seulement si demandé ET s'il y a du contenu
        if send_email and output and output.strip():
            settings = self.get_user_settings()
            notification_email = settings.get('notification_email')
            if notification_email and notification_email.strip():
                self.send_summary_email(output, notification_email)
        
        return output
    
    def update_last_run(self):
        """Met à jour la date de dernière exécution"""
        settings = self.get_user_settings()
        settings['last_run'] = datetime.now().isoformat()
        self.save_user_settings(settings)
    
    def send_summary_email(self, summary, notification_email):
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
                st.error("Impossible d'accéder à Gmail pour l'envoi")
                return False
            
            # Créer le message
            message = MIMEMultipart()
            message['From'] = service.users().getProfile(userId='me').execute()['emailAddress']
            message['To'] = notification_email
            message['Subject'] = f"Résumé AutoBrief - {datetime.now().strftime('%d/%m/%Y')}"
            
            # Corps du message
            body = f"""
            Bonjour,
            
            Voici votre résumé automatique des newsletters :
            
            {summary}
            
            ---
            Généré automatiquement par AutoBrief
            """
            
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Encoder le message
            raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            
            # Envoyer l'email
            sent_message = service.users().messages().send(userId='me', body=raw_message).execute()
            
            st.success(f"Résumé envoyé par email à {notification_email}")
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de l'envoi: {e}")
            return False

