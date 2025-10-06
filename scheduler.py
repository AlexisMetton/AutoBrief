#!/usr/bin/env python3
"""
Script de planification pour GitHub Actions
Vérifie et génère automatiquement les résumés selon la planification des utilisateurs
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_results.log'),
        logging.StreamHandler()
    ]
)

# Ajouter le répertoire parent au path pour importer nos modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from newsletter_manager import NewsletterManager

class AutoBriefScheduler:
    def __init__(self):
        self.config = Config()
        self.data_dir = "user_data"
        self.logger = logging.getLogger(__name__)
        
    def get_all_users(self):
        """Récupère tous les utilisateurs depuis GitHub Gist avec leurs groupes"""
        users = []
        
        try:
            # Charger les données depuis GitHub Gist
            gist_id = os.getenv('GIST_ID')
            
            if not gist_id:
                self.logger.info("Aucun GIST_ID trouvé dans les secrets GitHub")
                return users
            
            import requests
            headers = {'Accept': 'application/vnd.github.v3+json'}
            gist_token = os.getenv('GIST_TOKEN')
            if gist_token:
                headers['Authorization'] = f'token {gist_token}'
            
            response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(content)
                    
                    for user_email, user_data in all_users_data.items():
                        newsletter_groups = user_data.get('newsletter_groups', [])
                        
                        # Vérifier si l'utilisateur a des groupes actifs
                        if newsletter_groups:
                            users.append({
                                'email': user_email,
                                'newsletter_groups': newsletter_groups,
                                'oauth_credentials': user_data.get('oauth_credentials', {})
                            })
            else:
                self.logger.error(f"Erreur lors de la récupération du Gist: {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données utilisateur: {e}")
        
        return users
    
    def should_group_run_automatically(self, group_settings):
        """Vérifie si un groupe doit être traité automatiquement"""
        if not group_settings.get('enabled', True):
            self.logger.info("Groupe désactivé")
            return False
        
        last_run = group_settings.get('last_run')
        frequency = group_settings.get('frequency', 'daily')
        
        # Vérifier si c'est le bon jour et la bonne heure
        if not self.is_group_scheduled_time(group_settings):
            return False
        
        # Si pas de dernière exécution, on peut traiter
        if not last_run:
            self.logger.info("Première exécution du groupe")
            return True
        
        try:
            last_run_date = datetime.fromisoformat(last_run)
            now = datetime.now()
            
            if frequency == 'daily':
                # Pour les groupes quotidiens, vérifier qu'au moins 20h se sont écoulées
                # (pour éviter les exécutions multiples le même jour)
                time_since_last = now - last_run_date
                should_run = time_since_last >= timedelta(hours=20)
                
                if should_run:
                    self.logger.info(f"Groupe quotidien prêt - Dernière exécution: {last_run_date.strftime('%d/%m/%Y %H:%M')}, Écoulé: {time_since_last}")
                else:
                    self.logger.info(f"Groupe quotidien pas encore prêt - Dernière exécution: {last_run_date.strftime('%d/%m/%Y %H:%M')}, Écoulé: {time_since_last}")
                
                return should_run
                
            elif frequency == 'weekly':
                # Pour les groupes hebdomadaires, vérifier qu'au moins 6 jours se sont écoulés
                time_since_last = now - last_run_date
                should_run = time_since_last >= timedelta(days=6)
                
                if should_run:
                    self.logger.info(f"Groupe hebdomadaire prêt - Dernière exécution: {last_run_date.strftime('%d/%m/%Y %H:%M')}, Écoulé: {time_since_last}")
                else:
                    self.logger.info(f"Groupe hebdomadaire pas encore prêt - Dernière exécution: {last_run_date.strftime('%d/%m/%Y %H:%M')}, Écoulé: {time_since_last}")
                
                return should_run
        except Exception as e:
            self.logger.error(f"Erreur vérification fréquence: {e}")
            return True
        
        return False
    
    def is_group_scheduled_time(self, group_settings):
        """Vérifie si c'est le bon moment pour traiter un groupe"""
        try:
            schedule_day = group_settings.get('schedule_day', 'monday')
            schedule_time = group_settings.get('schedule_time', '09:00')
            frequency = group_settings.get('frequency', 'daily')
            
            now = datetime.now()
            current_day = now.strftime('%A').lower()
            
            # Pour les groupes quotidiens, on ignore le jour et on vérifie seulement l'heure
            # Pour les groupes hebdomadaires, on vérifie le jour ET l'heure
            if frequency == 'weekly':
                if current_day != schedule_day.lower():
                    self.logger.info(f"Jour incorrect pour groupe hebdomadaire - Actuel: {current_day}, Attendu: {schedule_day.lower()}")
                    return False
            
            # Convertir l'heure française vers UTC (soustraire 2h en été, 1h en hiver)
            # Pour simplifier, on utilise UTC+2 (été) - ajustez si nécessaire
            target_hour_france = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            
            # Conversion France -> UTC (UTC+2 en été)
            target_hour_utc = target_hour_france - 2
            if target_hour_utc < 0:
                target_hour_utc += 24
            
            current_hour = now.hour
            current_minute = now.minute
            
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour_utc * 60 + target_minute))
            
            # Marge de 30 minutes pour GitHub Actions
            is_scheduled = time_diff <= 30
            
            if is_scheduled:
                self.logger.info(f"✅ Groupe programmé - Heure actuelle (UTC): {current_hour}:{current_minute:02d}, Heure cible (France->UTC): {target_hour_france}:{target_minute:02d}->{target_hour_utc}:{target_minute:02d}, Différence: {time_diff}min")
            else:
                self.logger.info(f"⏰ Pas encore l'heure - Heure actuelle (UTC): {current_hour}:{current_minute:02d}, Heure cible (France->UTC): {target_hour_france}:{target_minute:02d}->{target_hour_utc}:{target_minute:02d}, Différence: {time_diff}min")
            
            return is_scheduled
            
        except Exception as e:
            self.logger.error(f"Erreur vérification horaire: {e}")
            return True  # En cas d'erreur, on autorise l'exécution
    
    def is_scheduled_time(self, user_settings):
        """Vérifie si c'est le bon jour et la bonne heure pour l'exécution"""
        try:
            schedule_day = user_settings.get('schedule_day', 'monday')
            schedule_time = user_settings.get('schedule_time', '09:00')
            
            now = datetime.now()
            current_day = now.strftime('%A').lower()
            current_time = now.strftime('%H:%M')
            
            # Vérifier le jour (pour la fréquence weekly)
            frequency = user_settings.get('frequency', 'weekly')
            if frequency == 'weekly':
                if current_day != schedule_day.lower():
                    self.logger.info(f"Jour incorrect - Actuel: {current_day}, Attendu: {schedule_day.lower()}")
                    return False
                else:
                    self.logger.info(f"Jour correct - {current_day}")
            
            # Convertir l'heure française vers UTC (soustraire 2h en été, 1h en hiver)
            target_hour = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            
            # Conversion France -> UTC (UTC+2 en été, UTC+1 en hiver)
            # Pour simplifier, on utilise UTC+2 (été) - ajustez si nécessaire
            target_hour_utc = target_hour - 2
            if target_hour_utc < 0:
                target_hour_utc += 24
            
            current_hour = now.hour
            current_minute = now.minute
            
            # GitHub Actions s'exécute à l'heure pile, on accepte +/- 30 minutes
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour_utc * 60 + target_minute))
            self.logger.info(f"Heure - Actuelle (UTC): {current_hour}:{current_minute:02d}, Cible (France->UTC): {target_hour}:{target_minute:02d}->{target_hour_utc}:{target_minute:02d}, Diff: {time_diff}min")
            return time_diff <= 30
            
        except Exception as e:
            self.logger.error(f"Erreur vérification horaire: {e}")
            return True  # En cas d'erreur, on autorise l'exécution
    
    def send_email(self, to_email, subject, content):
        """Envoie un email via le script d'envoi"""
        try:
            import subprocess
            
            # Définir les variables d'environnement pour le script
            # Sauvegarder le contenu dans un fichier temporaire
            temp_content_file = 'temp_email_content.html'
            with open(temp_content_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Préparer les variables d'environnement pour le script
            env = os.environ.copy()
            env['TO_EMAIL'] = to_email
            env['SUBJECT'] = subject
            env['CONTENT_FILE'] = temp_content_file
            
            self.logger.info(f"Envoi email pour {to_email}")
            self.logger.info(f"Sujet: {subject}")
            
            # Exécuter le script d'envoi d'email final
            result = subprocess.run(
                ['python', 'send_email_final.py'],
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Afficher les logs
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    self.logger.info(f"📧 {line}")
            
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    self.logger.error(f"❌ {line}")
            
            if result.returncode == 0:
                self.logger.info(f"✅ Email envoyé avec succès à {to_email}")
                return True
            else:
                self.logger.error(f"❌ Échec envoi email (code: {result.returncode})")
                return False
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Timeout lors de l'envoi d'email")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi email: {e}")
            return False
    
    def process_user_groups(self, user_info):
        """Traite les groupes de newsletters pour un utilisateur"""
        try:
            self.logger.info(f"🔄 Traitement des groupes pour {user_info['email']}")
            
            newsletter_groups = user_info.get('newsletter_groups', [])
            if not newsletter_groups:
                self.logger.warning(f"⚠️ Aucun groupe de newsletters pour {user_info['email']}")
                return False
            
            processed_groups = 0
            
            # Traiter chaque groupe individuellement
            for group in newsletter_groups:
                group_title = group.get('title', 'Sans titre')
                group_settings = group.get('settings', {})
                group_emails = group.get('emails', [])
                
                # Vérifier si ce groupe doit être traité
                if not self.should_group_run_automatically(group_settings):
                    self.logger.info(f"⏳ Groupe '{group_title}' pas encore prêt")
                    continue
                
                if not group_emails:
                    self.logger.warning(f"⚠️ Aucun email dans le groupe '{group_title}'")
                    continue
                
                self.logger.info(f"📧 Traitement du groupe '{group_title}' avec {len(group_emails)} emails")
                
                # Traiter ce groupe spécifique
                if self.process_single_group(user_info, group):
                    processed_groups += 1
                    self.logger.info(f"✅ Groupe '{group_title}' traité avec succès")
                else:
                    self.logger.error(f"❌ Échec traitement du groupe '{group_title}'")
            
            return processed_groups > 0
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement groupes {user_info['email']}: {e}")
            return False
    
    def process_single_group(self, user_info, group):
        """Traite un groupe spécifique"""
        try:
            group_title = group.get('title', 'Sans titre')
            group_settings = group.get('settings', {})
            group_emails = group.get('emails', [])
            
            # Simuler une session utilisateur pour NewsletterManager
            import streamlit as st
            st.session_state['user_email'] = user_info['email']
            st.session_state['authenticated'] = True
            
            from newsletter_manager import NewsletterManager
            newsletter_manager = NewsletterManager()
            
            # Forcer l'email utilisateur dans le NewsletterManager
            newsletter_manager.user_email = user_info['email']
            
            # Désactiver la sauvegarde dans le scheduler
            newsletter_manager._scheduler_mode = True
            
            # Configurer l'accès Gmail pour le NewsletterManager
            try:
                from secure_auth import SecureAuth
                auth = SecureAuth()
                
                # Récupérer les credentials de l'utilisateur depuis le Gist
                user_credentials = self.get_user_credentials_from_gist(user_info['email'])
                if user_credentials:
                    import json
                    credentials_json = json.dumps(user_credentials)
                    auth.set_external_credentials(credentials_json)
                else:
                    self.logger.error(f"❌ Aucun token OAuth2 trouvé pour {user_info['email']}")
                    return False
                
                newsletter_manager.auth = auth
            except Exception as e:
                self.logger.error(f"❌ Erreur configuration Gmail auth: {e}")
                return False
            
            # Traiter ce groupe spécifique
            result = newsletter_manager.process_single_group(group_title, group_settings)
            
            # Vérifier si un résumé a vraiment été généré et envoyé
            if result and isinstance(result, str) and result.strip():
                # Mettre à jour la date de dernière exécution seulement si un email a été envoyé
                self.update_group_last_run(user_info['email'], group_title)
                self.logger.info(f"📄 Résumé généré et email envoyé pour le groupe '{group_title}'")
                return True
            elif result is True:
                # Résumé généré mais pas de contenu (cas normal)
                self.logger.info(f"📄 Résumé généré pour le groupe '{group_title}' (pas de nouveau contenu)")
                # Ne pas mettre à jour last_run car pas de nouveau contenu
                return True
            else:
                self.logger.warning(f"ℹ️ Aucun contenu trouvé pour le groupe '{group_title}'")
                # Ne pas mettre à jour last_run car pas de contenu
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement groupe '{group_title}': {e}")
            return False
    
    
    def get_user_credentials_from_gist(self, user_email):
        """Récupère les credentials OAuth2 de l'utilisateur depuis le Gist"""
        try:
            import requests
            import json
            
            gist_id = os.getenv('GIST_ID')
            gist_token = os.getenv('GIST_TOKEN')
            
            
            if not gist_id or not gist_token:
                self.logger.error("❌ GIST_ID ou GIST_TOKEN manquant")
                return None
            
            # Récupérer le Gist
            headers = {
                'Authorization': f'token {gist_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(content) if content else {}
                    
                    # Récupérer les données de l'utilisateur
                    if user_email in all_users_data:
                        user_data = all_users_data[user_email]
                        # Vérifier si l'utilisateur a des credentials OAuth2 stockés
                        if 'oauth_credentials' in user_data:
                            oauth_creds = user_data['oauth_credentials']
                            
                            # Vérifier si les données sont chiffrées
                            if oauth_creds.get('_encrypted', False) and '_encrypted_data' in oauth_creds:
                                # Les données sont chiffrées, on peut les déchiffrer avec SECRET_KEY
                                try:
                                    from cryptography.fernet import Fernet
                                    import base64
                                    import json
                                    
                                    # Récupérer SECRET_KEY depuis les variables d'environnement
                                    secret_key = os.getenv('SECRET_KEY')
                                    if not secret_key:
                                        self.logger.error("❌ SECRET_KEY manquante pour déchiffrer les credentials")
                                        return None
                                    
                                    
                                    # Générer la clé Fernet (même méthode que dans config.py)
                                    key = base64.urlsafe_b64encode(secret_key.encode()[:32].ljust(32, b'0'))
                                    fernet = Fernet(key)
                                    
                                    # Déchiffrer les credentials
                                    encrypted_data = oauth_creds['_encrypted_data']
                                    
                                    # Essayer de déchiffrer avec différentes méthodes
                                    try:
                                        # Méthode 1: Direct
                                        decrypted_data = fernet.decrypt(encrypted_data.encode())
                                    except Exception:
                                        # Méthode 2: Avec données pré-décodées
                                        try:
                                            import base64
                                            decoded_data = base64.b64decode(encrypted_data)
                                            decrypted_data = fernet.decrypt(decoded_data)
                                        except Exception:
                                            return None
                                    
                                    decrypted_creds = json.loads(decrypted_data.decode())
                                    
                                    return decrypted_creds
                                    
                                except Exception as e:
                                    self.logger.error(f"❌ Erreur déchiffrement credentials pour {user_email}: {e}")
                                    self.logger.error(f"❌ Type d'erreur: {type(e).__name__}")
                                    self.logger.error(f"❌ Message détaillé: {str(e)}")
                                    return None
                            else:
                                # Ancien format non chiffré (pour compatibilité)
                                return oauth_creds
                        else:
                            self.logger.warning(f"⚠️ Aucun token OAuth2 stocké pour {user_email}")
                            return None
                    else:
                        self.logger.warning(f"⚠️ Utilisateur {user_email} non trouvé dans le Gist")
                        return None
                else:
                    self.logger.error("❌ Fichier user_data.json non trouvé dans le Gist")
                    return None
            else:
                self.logger.error(f"❌ Erreur accès Gist: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération credentials utilisateur: {e}")
            return None
    
    def update_group_last_run(self, user_email, group_title):
        """Met à jour la date de dernière exécution pour un groupe spécifique"""
        try:
            gist_id = os.getenv('GIST_ID')
            
            if not gist_id:
                self.logger.error("GIST_ID non trouvé dans les variables d'environnement")
                return
            
            import requests
            
            # Charger les données actuelles du Gist
            headers = {'Accept': 'application/vnd.github.v3+json'}
            gist_token = os.getenv('GIST_TOKEN')
            if gist_token:
                headers['Authorization'] = f'token {gist_token}'
            
            response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                if 'user_data.json' in gist_data['files']:
                    content = gist_data['files']['user_data.json']['content']
                    all_users_data = json.loads(content)
                    
                    # Mettre à jour la date pour ce groupe spécifique
                    if user_email in all_users_data:
                        user_data = all_users_data[user_email]
                        newsletter_groups = user_data.get('newsletter_groups', [])
                        
                        for group in newsletter_groups:
                            if group.get('title') == group_title:
                                group['settings']['last_run'] = datetime.now().isoformat()
                                break
                        
                        # Mettre à jour le Gist
                        update_data = {
                            "files": {
                                "user_data.json": {
                                    "content": json.dumps(all_users_data, indent=2, ensure_ascii=False)
                                }
                            }
                        }
                        
                        # Headers avec authentification
                        headers = {'Accept': 'application/vnd.github.v3+json'}
                        gist_token = os.getenv('GIST_TOKEN')
                        if gist_token:
                            headers['Authorization'] = f'token {gist_token}'
                        
                        update_response = requests.patch(
                            f'https://api.github.com/gists/{gist_id}',
                            json=update_data,
                            headers=headers
                        )
                        
                        if update_response.status_code == 200:
                            self.logger.info(f"✅ Date de dernière exécution mise à jour pour le groupe '{group_title}' de {user_email}")
                        else:
                            self.logger.error(f"❌ Erreur lors de la mise à jour du Gist: {update_response.status_code}")
                    else:
                        self.logger.warning(f"⚠️ Utilisateur {user_email} non trouvé dans les données")
                else:
                    self.logger.error("Fichier user_data.json non trouvé dans le Gist")
            else:
                self.logger.error(f"❌ Erreur lors de la récupération du Gist: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur mise à jour: {e}")
    
    def run_scheduler(self):
        """Fonction principale du scheduler"""
        self.logger.info(f"🚀 Démarrage du scheduler AutoBrief - {datetime.now()}")
        
        users = self.get_all_users()
        self.logger.info(f"👥 {len(users)} utilisateurs avec des groupes de newsletters")
        
        processed = 0
        for user_info in users:
            self.logger.info(f"🔄 Vérification des groupes pour {user_info['email']}")
            
            if self.process_user_groups(user_info):
                processed += 1
                self.logger.info(f"✅ Traitement réussi pour {user_info['email']}")
            else:
                self.logger.info(f"ℹ️ Aucun groupe à traiter pour {user_info['email']}")
        
        self.logger.info(f"🎯 Scheduler terminé - {processed} utilisateurs traités")
        return processed

def main():
    """Point d'entrée principal"""
    scheduler = AutoBriefScheduler()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()
