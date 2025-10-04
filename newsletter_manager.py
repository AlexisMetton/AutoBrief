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
        self.data_dir = "user_data"
        self.user_email = st.session_state.get('user_email', 'default_user')
        self.user_data_file = os.path.join(self.data_dir, f"{self.user_email.replace('@', '_').replace('.', '_')}.json")
        
        # Créer le répertoire de données si nécessaire
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_user_data(self):
        """Charge les données utilisateur automatiquement"""
        try:
            # 1. Essayer d'abord le cache de session (données modifiées récemment)
            if 'user_data_cache' in st.session_state:
                return st.session_state['user_data_cache']
            
            # 2. Essayer de charger depuis le stockage externe
            data = self.load_from_external_storage()
            if data:
                st.session_state['user_data_cache'] = data
                return data
            
            # 3. Fallback sur les secrets Streamlit
            try:
                if hasattr(st, 'secrets') and 'user_data' in st.secrets:
                    all_users_data = st.secrets['user_data']
                    if self.user_email in all_users_data:
                        data = all_users_data[self.user_email]
                        st.session_state['user_data_cache'] = data
                        return data
            except:
                pass
            
            # 4. Fallback sur le fichier local
            if os.path.exists(self.user_data_file):
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    st.session_state['user_data_cache'] = data
                    return data
                    
        except Exception as e:
            st.warning(f"⚠️ Erreur lors du chargement des données: {e}")
        
        # Retourner des données par défaut
        default_data = {
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
        
        st.session_state['user_data_cache'] = default_data
        return default_data
    
    def load_from_external_storage(self):
        """Charge les données depuis GitHub Gist"""
        try:
            # GitHub Gist
            data = self.load_from_github_gist()
            if data:
                return data
                
            return None
        except:
            return None
    
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
            return None
        except:
            return None
    
    def save_user_data(self, data):
        """Sauvegarde les données utilisateur automatiquement"""
        try:
            # Toujours sauvegarder dans la session state pour la persistance
            st.session_state['user_data_cache'] = data
            
            # Essayer de sauvegarder automatiquement
            success = self.save_to_external_storage(data)
            
            if success:
                st.success("✅ Données sauvegardées automatiquement !")
            else:
                st.warning("⚠️ Sauvegarde locale uniquement (redémarrage effacera les données)")
            
            return True
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def save_to_external_storage(self, data):
        """Sauvegarde les données dans GitHub Gist automatiquement"""
        try:
            # GitHub Gist (gratuit et automatique)
            if self.save_to_github_gist(data):
                return True
            
            # Fallback sur fichier local si GitHub Gist échoue
            return self.save_to_local_file(data)
            
        except Exception as e:
            st.warning(f"⚠️ Sauvegarde GitHub Gist échouée: {e}")
            return False
    
    def save_to_github_gist(self, data):
        """Sauvegarde dans GitHub Gist (gratuit et automatique)"""
        try:
            import requests
            
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
                st.warning("""
                ⚠️ **Gist partagé non configuré**
                
                Pour utiliser la persistance automatique :
                1. Le développeur doit configurer un Gist partagé
                2. Ajouter le secret `GIST_ID` dans Streamlit Cloud
                3. Tous les utilisateurs partageront le même Gist
                """)
                return False
            
            # Charger les données existantes du Gist
            response = requests.get(f'https://api.github.com/gists/{gist_id}')
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    # Charger les données existantes
                    existing_content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(existing_content) if existing_content else {}
                else:
                    all_users_data = {}
                
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
                
                update_response = requests.patch(
                    f'https://api.github.com/gists/{gist_id}',
                    json=update_data,
                    headers={'Accept': 'application/vnd.github.v3+json'}
                )
                
                if update_response.status_code == 200:
                    st.success("✅ Données sauvegardées dans le Gist partagé !")
                    return True
                else:
                    st.error(f"❌ Erreur lors de la mise à jour du Gist: {update_response.status_code}")
                    return False
            else:
                st.error(f"❌ Erreur lors de l'accès au Gist: {response.status_code}")
                return False
            
        except Exception as e:
            st.error(f"❌ Erreur GitHub Gist: {e}")
            return False
    
    
    def save_to_local_file(self, data):
        """Sauvegarde dans un fichier local (fallback)"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except:
            return False
        
    def save_newsletters(self, newsletters):
        """Sauvegarde la liste des newsletters dans la session ET sur disque"""
        st.session_state['newsletters'] = newsletters
        
        # Mettre à jour aussi les données utilisateur complètes
        user_data = self.load_user_data()
        user_data['newsletters'] = newsletters
        self.save_user_data(user_data)
        
    def get_newsletters(self):
        """Récupère la liste des newsletters depuis la session ou les données utilisateur"""
        # Charger les données utilisateur complètes (qui incluent les newsletters)
        user_data = self.load_user_data()
        newsletters = user_data.get('newsletters', [])
        
        # Mettre en session pour la performance
        st.session_state['newsletters'] = newsletters
        
        return newsletters
    
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
                    return False
            
            # Vérifier l'heure (avec une marge de 1 heure pour GitHub Actions)
            target_hour = int(schedule_time.split(':')[0])
            current_hour = now.hour
            
            # GitHub Actions peut avoir un délai, on accepte +/- 1 heure
            return abs(current_hour - target_hour) <= 1
            
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
                            st.warning("⚠️ Cette newsletter est déjà dans la liste")
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
            st.info("ℹ️ Aucune newsletter configurée. Ajoutez-en une ci-dessus.")
        
        # Configuration de la planification automatique
        st.markdown("---")
        st.markdown("### ⏰ Planification automatique")
        
        st.info("""
        💡 **Comment ça fonctionne :**
        - GitHub Actions vérifie **toutes les heures** si un résumé doit être généré
        - Vous pouvez choisir le **jour** (pour hebdomadaire/mensuel) et l'**heure** de votre choix
        - L'heure est en **UTC** (GitHub Actions fonctionne en UTC)
        - **Marge de 1 heure** : Le système accepte +/- 1 heure pour la flexibilité
        """)
        
        # Note sur la persistance
        st.markdown("---")
        st.markdown("### 💾 Persistance des données")
        
        st.warning("""
        ⚠️ **Important :** Sur Streamlit Cloud, les données sont sauvegardées dans les secrets.
        
        **Pour une persistance complète :**
        1. Allez dans les **Settings** de votre app Streamlit Cloud
        2. Ajoutez le secret `user_data` (voir guide)
        3. Vos newsletters et paramètres seront sauvegardés
        """)
        
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
            
            st.info(f"""
            🔄 **Résumé automatique activé**
            - 📅 Fréquence : {frequency_text}
            - ⏰ Planifié : {schedule_text}
            - 📊 Dernière exécution : {settings.get('last_run', 'Jamais')}
            """)
        else:
            st.warning("⚠️ Résumé automatique désactivé")
    
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

