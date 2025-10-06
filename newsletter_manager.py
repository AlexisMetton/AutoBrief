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
        
    def get_newsletters(self):
        """Récupère la liste des newsletters depuis le Gist"""
        # Charger les données utilisateur depuis le Gist
        user_data = self.load_user_data()
        
        # D'abord essayer les newsletters individuelles
        individual_newsletters = user_data.get('newsletters', [])
        if individual_newsletters:
            return individual_newsletters
        
        # Sinon, essayer les anciens groupes
        newsletter_groups = user_data.get('newsletter_groups', [])
        if newsletter_groups:
            return newsletter_groups
        
        return []
    
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
    
    def create_newsletter(self, title):
        """Crée une nouvelle newsletter vide"""
        newsletters = self.get_newsletters()
        if title and title not in [newsletter.get('title', newsletter.get('name', '')) for newsletter in newsletters]:
            newsletter_data = {
                'title': title,
                'emails': []
            }
            newsletters.append(newsletter_data)
            self.save_newsletters(newsletters)
            return True
        return False
    
    def add_emails_to_newsletter(self, newsletter_title, emails):
        """Ajoute des emails à une newsletter existante"""
        newsletters = self.get_newsletters()
        for newsletter in newsletters:
            if newsletter.get('title', newsletter.get('name', '')) == newsletter_title:
                existing_emails = newsletter.get('emails', [])
                # Ajouter seulement les nouveaux emails
                for email in emails:
                    if email not in existing_emails:
                        existing_emails.append(email)
                newsletter['emails'] = existing_emails
            self.save_newsletters(newsletters)
            return True
        return False
    
    def remove_email_from_newsletter(self, newsletter_title, email):
        """Supprime un email d'une newsletter"""
        newsletters = self.get_newsletters()
        for newsletter in newsletters:
            if newsletter.get('title', newsletter.get('name', '')) == newsletter_title:
                emails = newsletter.get('emails', [])
                if email in emails:
                    emails.remove(email)
                    newsletter['emails'] = emails
            self.save_newsletters(newsletters)
            return True
        return False
    
    def remove_newsletter(self, newsletter_title):
        """Supprime une newsletter entière"""
        newsletters = self.get_newsletters()
        for i, newsletter in enumerate(newsletters):
            if newsletter.get('title', newsletter.get('name', '')) == newsletter_title:
                newsletters.pop(i)
            self.save_newsletters(newsletters)
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
    
    def render_newsletter_management(self):
        """Interface de gestion des newsletters avec onglets"""
        
        # Créer une nouvelle newsletter
        with st.expander('Créer une nouvelle newsletter', expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                new_newsletter_title = st.text_input(
                    "Nom de la newsletter:",
                    placeholder="ex: Actualités Tech",
                    help="Nom de votre newsletter"
                )
            with col2:
                st.write("")  # Espacement
                st.write("")  # Espacement
                if st.button("Créer la newsletter", type="primary", icon=":material/add:", key="create_newsletter_btn"):
                    if new_newsletter_title:
                        if self.create_newsletter(new_newsletter_title):
                            st.success(f"Newsletter '{new_newsletter_title}' créée")
                            st.rerun()
                        else:
                            st.error("Cette newsletter existe déjà")
                    else:
                        st.error("Veuillez entrer un nom de newsletter")
        
        # Récupérer les newsletters existantes
        newsletters = self.get_newsletters()
        if newsletters:
            st.markdown("#### <i class='fas fa-envelope'></i> Vos newsletters", unsafe_allow_html=True)
            
            # Créer des onglets pour chaque newsletter
            newsletter_names = [newsletter.get('title', newsletter.get('name', 'Sans nom')) for newsletter in newsletters]
            selected_newsletter = st.selectbox(
                "Choisir une newsletter:",
                options=newsletter_names,
                help="Sélectionnez une newsletter pour la gérer"
            )
            
            if selected_newsletter:
                # Trouver la newsletter sélectionnée
                selected_newsletter_data = None
                for newsletter in newsletters:
                    if newsletter.get('title', newsletter.get('name', '')) == selected_newsletter:
                        selected_newsletter_data = newsletter
                        break
                
                if selected_newsletter_data:
                    st.markdown(f"### 📧 {selected_newsletter}")
                    
                    # Ajouter des emails à cette newsletter
                    with st.expander('Ajouter des emails à cette newsletter', expanded=True):
                        emails_text = st.text_area(
                            "Emails à ajouter (un par ligne):",
                            placeholder="email1@example.com\nemail2@example.com\nemail3@example.com",
                            help="Entrez un email par ligne",
                            height=100
                        )
                        
                        if st.button("Ajouter les emails", type="primary", icon=":material/add:", key=f"add_emails_{selected_newsletter}"):
                            if emails_text:
                                # Parser les emails
                                new_emails = [email.strip() for email in emails_text.split('\n') if email.strip() and '@' in email]
                                if new_emails:
                                    if self.add_emails_to_newsletter(selected_newsletter, new_emails):
                                        st.success(f"{len(new_emails)} emails ajoutés à '{selected_newsletter}'")
                                        st.rerun()
                                    else:
                                        st.error("Erreur lors de l'ajout des emails")
                                else:
                                    st.error("Veuillez entrer au moins un email valide")
                            else:
                                st.error("Veuillez entrer des emails")
                    
                    # Afficher les emails de cette newsletter
                    emails = selected_newsletter_data.get('emails', [])
                    if emails:
                        st.markdown(f"**Emails de cette newsletter ({len(emails)}):**")
                        for i, email in enumerate(emails):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"• {email}")
                            with col2:
                                if st.button("Supprimer", key=f"delete_email_{i}_{selected_newsletter}", icon=":material/delete:"):
                                    self.remove_email_from_newsletter(selected_newsletter, email)
                        st.rerun()
                    else: 
                        st.info("Aucun email dans cette newsletter")
                    
                    # Bouton pour supprimer la newsletter entière
                    if st.button("Supprimer cette newsletter", type="secondary", icon=":material/delete:", key=f"delete_newsletter_{selected_newsletter}"):
                        self.remove_newsletter(selected_newsletter)
                        st.rerun()
        else:
            st.info("Aucune newsletter créée. Créez-en une ci-dessus.")
        
        
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
            
            # Créer une liste d'heures pile (00:00, 01:00, 02:00, etc.)
            time_options = []
            for hour in range(24):
                time_str = f"{hour:02d}:00"
                time_options.append(time_str)
            
            # Trouver l'index de l'heure actuelle
            current_time = settings.get('schedule_time', '09:00')
            try:
                current_index = time_options.index(current_time)
            except ValueError:
                current_index = 9  # 09:00 par défaut
            
            schedule_time_str = st.selectbox(
                "Heure d'envoi",
                options=time_options,
                index=current_index,
                help="Heure d'envoi (GitHub Actions s'exécute à 09:00 UTC par défaut)"
            )
            
            # Convertir en objet time pour la compatibilité
            schedule_time = datetime.strptime(schedule_time_str, '%H:%M').time()
        
        with col2:
            days_to_analyze = st.slider(
                "Période d'analyse",
                min_value=1,
                max_value=7,
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
        
        # Afficher directement l'heure programmée (déjà en heure française)
        if frequency == 'weekly':
            day_text = {
                'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
            }[schedule_day]
            st.info(f"Planification : {frequency_text} le {day_text} à {schedule_time} heure française (±30min)")
        else:
            st.info(f"Planification : {frequency_text} à {schedule_time} heure française (±30min)")
        
        # Note sur la tolérance et conversion
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
        
        newsletters = self.get_newsletters()
        if not newsletters:
            print("❌ DEBUG: Aucune newsletter configurée")
            return None
        
        # Extraire tous les emails de toutes les newsletters
        all_emails = []
        for newsletter in newsletters:
            emails = newsletter.get('emails', [])
            all_emails.extend(emails)
        
        print(f"✅ DEBUG: {len(newsletters)} newsletters trouvées avec {len(all_emails)} emails au total: {all_emails}")
        
        service = self.auth.get_gmail_service()
        if not service:
            print("❌ DEBUG: Impossible d'obtenir le service Gmail")
            return None
        print("✅ DEBUG: Service Gmail obtenu")
        
        # Récupérer le prompt personnalisé
        settings = self.get_user_settings()
        custom_prompt = settings.get('custom_prompt', '')
        print(f"🔍 DEBUG: Custom prompt: '{custom_prompt[:50]}...'")
        
        # Créer la requête
        query = self.get_query_for_emails(all_emails, days)
        print(f"🔍 DEBUG: Requête Gmail: {query}")
        
        # Récupérer les messages
        try:
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            print(f"🔍 DEBUG: {len(messages)} messages trouvés")
        
            if not messages:
                print("❌ DEBUG: Aucun message trouvé")
                return None
        
            # Filtrer les emails promotionnels
            filtered_messages = []
            for idx, msg in enumerate(messages):
                print(f"🔍 DEBUG: Analyse message {idx + 1}/{len(messages)}")
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
            
            print(f"🔍 DEBUG: {len(filtered_messages)}/{len(messages)} emails non-promotionnels trouvés")
            
            # Traiter seulement les emails non-promotionnels
            all_content = ""
            for idx, msg in enumerate(filtered_messages):
                print(f"🔍 DEBUG: Extraction contenu éditorial {idx + 1}/{len(filtered_messages)}")
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
            
            print(f"🔍 DEBUG: Contenu éditorial global: {len(all_content)} caractères")
            
            # Générer un seul résumé pour tous les emails non-promotionnels
            if all_content.strip():
                print(f"🔍 DEBUG: Génération du résumé global...")
                output = self.summarize_newsletter(all_content, custom_prompt)
                print(f"🔍 DEBUG: Résumé global généré: {len(output) if output else 0} caractères")
            else:
                output = ""
                print("❌ DEBUG: Aucun contenu éditorial à traiter")
            
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
        
        # Extraire tous les emails de toutes les newsletters
        all_emails = []
        for newsletter in newsletters:
            emails = newsletter.get('emails', [])
            all_emails.extend(emails)
        
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
        query = self.get_query_for_emails(all_emails, days)
        
        
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
        
        # Filtrer les emails promotionnels avant le traitement
        filtered_messages = []
        if hasattr(st, 'progress'):
            progress_bar = st.progress(0)
        else:
            progress_bar = None
        
        print(f"🔍 DEBUG: Filtrage de {len(messages)} messages")
        
        for idx, msg in enumerate(messages):
            print(f"🔍 DEBUG: Analyse message {idx + 1}/{len(messages)}")
            if hasattr(st, 'spinner'):
                with st.spinner(f"Analyse de l'email {idx + 1}/{len(messages)}..."):
                    message = self.get_message(service, msg['id'])
            else:
                message = self.get_message(service, msg['id'])
            
            if message:
                # Analyser le message pour détecter s'il est promotionnel
                is_promotional = self.is_promotional_email(message)
                if is_promotional:
                    print(f"🚫 DEBUG: Email {idx + 1} détecté comme promotionnel - ignoré")
                else:
                    print(f"✅ DEBUG: Email {idx + 1} validé comme contenu éditorial")
                    filtered_messages.append(msg)
            else:
                print("❌ DEBUG: Impossible de récupérer le message")
            
            if progress_bar:
                progress_bar.progress((idx + 1) / len(messages))
        
        print(f"🔍 DEBUG: {len(filtered_messages)}/{len(messages)} emails non-promotionnels trouvés")
        if hasattr(st, 'info'):
            st.info(f"📊 {len(filtered_messages)}/{len(messages)} emails non-promotionnels trouvés")
        
        # Traiter seulement les emails non-promotionnels
        all_content = ""
        for idx, msg in enumerate(filtered_messages):
            print(f"🔍 DEBUG: Extraction contenu éditorial {idx + 1}/{len(filtered_messages)}")
            message = self.get_message(service, msg['id'])
            
            if message:
                body = self.get_message_body(message)
                if body:
                    print(f"🔍 DEBUG: Corps du message extrait ({len(body)} caractères)")
                    # Ajouter un séparateur entre les emails
                    if all_content:
                        all_content += "\n\n--- NOUVEL EMAIL ---\n\n"
                    all_content += body
                    print(f"✅ DEBUG: Contenu éditorial ajouté")
                else:
                    print("❌ DEBUG: Impossible d'extraire le corps du message")
            else:
                print("❌ DEBUG: Impossible de récupérer le message")
        
        print(f"🔍 DEBUG: Contenu éditorial global: {len(all_content)} caractères")
        if hasattr(st, 'info'):
            st.info(f"📄 Contenu éditorial global: {len(all_content)} caractères")
        
        # Générer un seul résumé pour tous les emails non-promotionnels
        if all_content.strip():
            print(f"🔍 DEBUG: Génération du résumé global...")
            print(f"🔍 DEBUG: Contenu à traiter: {len(all_content)} caractères")
            if hasattr(st, 'info'):
                st.info(f"🤖 Génération du résumé IA...")
            output = self.summarize_newsletter(all_content, custom_prompt)
            print(f"🔍 DEBUG: Résumé global généré: {len(output) if output else 0} caractères")
            if output:
                print(f"🔍 DEBUG: Résumé non vide - traitement réussi")
                if hasattr(st, 'success'):
                    st.success(f"✅ Résumé IA généré: {len(output)} caractères")
            else:
                print(f"❌ DEBUG: Résumé vide - problème avec l'IA")
                if hasattr(st, 'error'):
                    st.error("❌ L'IA n'a pas généré de contenu")
        else:
            output = ""
            print("❌ DEBUG: Aucun contenu éditorial à traiter")
            if hasattr(st, 'warning'):
                st.warning("⚠️ Aucun contenu éditorial trouvé")
        
        # Mettre à jour la date de dernière exécution
        if output:
            self.update_last_run()
        
        # Envoyer par email seulement si demandé ET s'il y a du contenu
        if send_email and output and output.strip():
            settings = self.get_user_settings()
            notification_email = settings.get('notification_email')
            if notification_email and notification_email.strip():
                self.send_summary_email(output, notification_email)
        
        print(f"🔍 DEBUG: Valeur finale retournée: '{output}' (type: {type(output)}, longueur: {len(output) if output else 0})")
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
            
            # Corps du message HTML
            # Si le summary contient déjà du HTML, l'utiliser directement
            if '<html>' in summary.lower() or '<body>' in summary.lower():
                # Le summary est déjà en HTML, l'utiliser directement
                message.attach(MIMEText(summary, 'html', 'utf-8'))
            else:
                # Sinon, créer un HTML basique
                body = f"""
                <html>
                <body>
                <h2>Résumé AutoBrief - {datetime.now().strftime('%d/%m/%Y')}</h2>
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
            
            st.success(f"Résumé envoyé par email à {notification_email}")
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de l'envoi: {e}")
            return False

