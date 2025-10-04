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
        self.user_email = st.session_state.get('user_email', 'default_user')
        
        # Vérifier la configuration du Gist au démarrage
        self.check_gist_configuration()
    
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
                ⚠️ **Gist partagé non configuré**
                
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
                st.success("✅ Gist partagé configuré avec token (sauvegarde automatique) !")
                return True
            else:
                st.warning("""
                ⚠️ **Token Gist manquant**
                
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
            # Charger uniquement depuis le Gist
            data = self.load_from_github_gist()
            if data:
                return data
            else:
                # Pas de données dans le Gist - retourner des données par défaut
                return {
                    'newsletters': [],
                    'settings': {
                        'frequency': 'weekly',
                        'days_to_analyze': 7,
                        'notification_email': '',
                        'last_run': None,
                        'auto_send': False,
                        'schedule_day': 'monday',
                        'schedule_time': '09:00',
                        'schedule_timezone': 'UTC'
                    }
                }
                    
        except Exception as e:
            # En cas d'erreur, retourner des données par défaut
            return {
                'newsletters': [],
                'settings': {
                    'frequency': 'weekly',
                    'days_to_analyze': 7,
                    'notification_email': '',
                    'last_run': None,
                    'auto_send': False,
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
                                'auto_send': False,
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
            print(f"DEBUG: save_user_data appelé avec data: {data}")
            print(f"DEBUG: save_user_data - user_email: {self.user_email}")
            # Sauvegarder directement dans le Gist
            success = self.save_to_github_gist(data)
            print(f"DEBUG: save_to_github_gist retourne: {success}")
            
            if success:
                st.success("✅ Données sauvegardées automatiquement !")
            else:
                st.error("❌ Erreur lors de la sauvegarde dans le Gist")
            
            return success
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde: {e}")
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
            
            if not gist_id:
                st.warning("""
                ⚠️ **Gist partagé non configuré**
                
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
                print(f"DEBUG: Erreur lecture Gist - Status: {response.status_code}, Response: {response.text}")
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
            gist_token = st.secrets.get('GIST_TOKEN')
            
            if gist_token:
                print(f"DEBUG: Token trouvé - {gist_token[:10]}...")
                print(f"DEBUG: Token complet - {gist_token}")
                # Utiliser le token GitHub pour l'authentification
                headers = {
                    'Accept': 'application/vnd.github.v3+json',
                    'Authorization': f'token {gist_token}'
                }
                print(f"DEBUG: Headers - {headers}")
            else:
                print("DEBUG: Aucun token GIST_TOKEN trouvé")
                st.error("❌ Token GIST_TOKEN manquant dans les secrets Streamlit")
                return False
            
            if gist_token:
                update_response = requests.patch(
                    f'https://api.github.com/gists/{gist_id}',
                    json=update_data,
                    headers=headers
                )
                
                print(f"DEBUG: Response status - {update_response.status_code}")
                print(f"DEBUG: Response text - {update_response.text}")
                
                if update_response.status_code == 200:
                    st.success("✅ Données sauvegardées automatiquement dans le Gist !")
                    return True
                else:
                    st.error(f"❌ Erreur lors de la mise à jour du Gist: {update_response.status_code}")
                    st.info("Vérifiez que le token Gist est correct dans les secrets")
                    return False
            else:
                # Pas de token Gist - sauvegarde en session uniquement
                st.warning("""
                ⚠️ **Token Gist manquant**
                    
                    Pour la sauvegarde automatique :
                    1. Créez un token GitHub avec le scope `gist`
                    2. Ajoutez-le dans les secrets Streamlit : `GIST_TOKEN`
                    3. La sauvegarde sera automatique
                """)
                
                return False
            
        except Exception as e:
            st.error(f"❌ Erreur GitHub Gist: {e}")
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
            'auto_send': False
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
                    print(f"DEBUG: Jour incorrect - Actuel: {current_day}, Attendu: {schedule_day.lower()}")
                    return False
                else:
                    print(f"DEBUG: Jour correct - {current_day}")
            
            # Vérifier l'heure (avec une marge de 30 minutes pour GitHub Actions)
            target_hour = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            current_hour = now.hour
            current_minute = now.minute
            
            # GitHub Actions s'exécute à l'heure pile, on accepte +/- 30 minutes
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour * 60 + target_minute))
            print(f"DEBUG: Heure - Actuelle: {current_hour}:{current_minute:02d}, Cible: {target_hour}:{target_minute:02d}, Diff: {time_diff}min")
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
        st.markdown("### 📧 Gestion des Newsletters")
        
        # Ajouter une newsletter
        with st.expander("➕ Ajouter une newsletter", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_email = st.text_input(
                    "Email de la newsletter:",
                    placeholder="exemple@newsletter.com",
                    help="Entrez l'adresse email qui vous envoie les newsletters"
                )
            with col2:
                if st.button("Ajouter", type="primary"):
                    if new_email and "@" in new_email:
                        if self.add_newsletter(new_email):
                            st.success(f"✅ Newsletter {new_email} ajoutée")
                            st.rerun()
                        else:
                            pass
                    else:
                        st.error("❌ Veuillez entrer une adresse email valide")
        
        # Liste des newsletters
        newsletters = self.get_newsletters()
        if newsletters:
            st.markdown("#### 📋 Newsletters surveillées")
            for i, email in enumerate(newsletters):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📧 {email}")
                with col2:
                    if st.button("🗑️", key=f"delete_{i}", help="Supprimer"):
                        self.remove_newsletter(email)
                        st.rerun()
        else:
            pass
        
        # Configuration de la planification automatique
        st.markdown("---")
        st.markdown("### ⏰ Planification automatique")
        
        pass
        
        # Note sur la persistance
        st.markdown("---")
        st.markdown("### 💾 Persistance des données")
        
        pass
        
        settings = self.get_user_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_send = st.checkbox(
                "🔄 Génération automatique",
                value=settings.get('auto_send', False),
                help="Active la génération automatique des résumés"
            )
            
            frequency = st.selectbox(
                "📅 Fréquence",
                options=['daily', 'weekly', 'monthly'],
                index=['daily', 'weekly', 'monthly'].index(settings.get('frequency', 'weekly')),
                format_func=lambda x: {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire', 'monthly': 'Mensuelle'}[x],
                help="Fréquence de génération des résumés"
            )
            
            # Configuration du jour et de l'heure
            if frequency in ['weekly', 'monthly']:
                schedule_day = st.selectbox(
                    "📆 Jour de la semaine",
                    options=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                    index=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(settings.get('schedule_day', 'monday')),
                    format_func=lambda x: {
                        'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                        'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
                    }[x],
                    help="Jour de la semaine pour l'envoi du résumé"
                )
            else:
                schedule_day = 'daily'
            
            schedule_time = st.time_input(
                "⏰ Heure d'envoi (UTC)",
                value=datetime.strptime(settings.get('schedule_time', '09:00'), '%H:%M').time(),
                help="Heure d'envoi en UTC (GitHub Actions s'exécute à 09:00 UTC par défaut)"
            )
        
        with col2:
            days_to_analyze = st.slider(
                "📊 Période d'analyse",
                min_value=1,
                max_value=30,
                value=settings.get('days_to_analyze', 7),
                help="Nombre de jours à analyser pour chaque résumé"
            )
            
            notification_email = st.text_input(
                "📧 Email de notification",
                value=settings.get('notification_email', ''),
                placeholder="votre.email@example.com",
                help="Email pour recevoir les résumés automatiques (optionnel)"
            )
        
        # Sauvegarder les paramètres
        if st.button("💾 Sauvegarder les paramètres", type="primary"):
            new_settings = {
                'auto_send': auto_send,
                'frequency': frequency,
                'days_to_analyze': days_to_analyze,
                'notification_email': notification_email,
                'last_run': settings.get('last_run'),
                'schedule_day': schedule_day,
                'schedule_time': schedule_time.strftime('%H:%M'),
                'schedule_timezone': 'UTC'
            }
            
            if self.save_user_settings(new_settings):
                st.success("✅ Paramètres sauvegardés !")
                st.rerun()
            else:
                st.error("❌ Erreur lors de la sauvegarde")
        
        # Statut de la planification
        if auto_send:
            frequency_text = {'daily': 'Quotidienne', 'weekly': 'Hebdomadaire', 'monthly': 'Mensuelle'}[frequency]
            if frequency in ['weekly', 'monthly']:
                day_text = {
                    'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi', 
                    'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
                }[schedule_day]
                schedule_text = f"{day_text} à {schedule_time.strftime('%H:%M')} UTC"
            else:
                schedule_text = f"Tous les jours à {schedule_time.strftime('%H:%M')} UTC"
            
            pass
        else:
            pass
    
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
            st.error(f"❌ Erreur lors de la récupération des emails: {e}")
            return []
    
    def get_message(self, service, msg_id):
        """Récupère un message Gmail spécifique"""
        try:
            return service.users().messages().get(userId='me', id=msg_id).execute()
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération du message: {e}")
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
            st.error(f"❌ Erreur lors de l'extraction du contenu: {e}")
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
    
    def summarize_newsletter(self, content):
        """Utilise OpenAI pour extraire les actualités IA"""
        if len(content) > 32000:
            content = content[:32000]
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"""From the following newsletter, extract all the news related to AI while keeping the 
            links to sources of information. Do not keep any affiliate links, self-promotion links, substack links and links to other articles by 
            the same author. Do not keep reference to the author, the newsletter or substack:\n\n{content}\nYou will output result as a JSON object, a dictionary with a single key 'result' 
            which yields the extraction as a string. If there is no AI news in the newsletter, output an empty string."""}
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
            st.error(f"❌ Erreur OpenAI: {e}")
            return ""
    
    def process_newsletters(self, days=7, send_email=False):
        """Traite toutes les newsletters et génère le résumé"""
        newsletters = self.get_newsletters()
        if not newsletters:
            st.error("❌ Aucune newsletter configurée")
            return None
        
        service = self.auth.get_gmail_service()
        if not service:
            return None
        
        # Créer la requête
        query = self.get_query_for_emails(newsletters, days)
        
        # Récupérer les messages
        with st.spinner("🔍 Recherche des emails..."):
            messages = self.list_messages(service, query)
        
        if not messages:
            st.warning("⚠️ Aucun email trouvé pour la période sélectionnée")
            return None
        
        st.success(f"✅ {len(messages)} emails trouvés")
        
        # Traiter chaque message
        output = ""
        progress_bar = st.progress(0)
        
        for idx, msg in enumerate(messages):
            with st.spinner(f"📧 Traitement de l'email {idx + 1}/{len(messages)}..."):
                message = self.get_message(service, msg['id'])
                if message:
                    body = self.get_message_body(message)
                    if body:
                        summary = self.summarize_newsletter(body)
                        if summary and len(summary.strip()) > 0:
                            summary = self.replace_redirected_links(summary)
                            output += f"**Source {idx + 1}:**\n{summary}\n\n"
            
            progress_bar.progress((idx + 1) / len(messages))
        
        # Mettre à jour la date de dernière exécution
        if output:
            self.update_last_run()
            
            # Envoyer par email seulement si demandé (génération automatique)
            if send_email:
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
                st.error("❌ Impossible d'accéder à Gmail pour l'envoi")
                return False
            
            # Créer le message
            message = MIMEMultipart()
            message['From'] = service.users().getProfile(userId='me').execute()['emailAddress']
            message['To'] = notification_email
            message['Subject'] = f"📰 Résumé AutoBrief - {datetime.now().strftime('%d/%m/%Y')}"
            
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
            
            st.success(f"✅ Résumé envoyé par email à {notification_email}")
            return True
            
        except Exception as e:
            st.error(f"❌ Erreur lors de l'envoi: {e}")
            return False

