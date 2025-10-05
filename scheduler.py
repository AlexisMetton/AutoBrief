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
        """Récupère tous les utilisateurs depuis GitHub Gist"""
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
                        settings = user_data.get('settings', {})
                        
                        # Vérifier si l'utilisateur a activé l'envoi automatique
                        if settings.get('auto_send', False):
                            users.append({
                                'email': user_email,
                                'settings': settings,
                                'newsletters': user_data.get('newsletters', [])
                            })
            else:
                self.logger.error(f"Erreur lors de la récupération du Gist: {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données utilisateur: {e}")
        
        return users
    
    def should_run_for_user(self, user_settings):
        """Vérifie si un résumé doit être généré pour cet utilisateur"""
        if not user_settings.get('auto_send', False):
            self.logger.info("Auto-send désactivé")
            return False
        
        # Vérifier d'abord le jour et l'heure
        if not self.is_scheduled_time(user_settings):
            self.logger.info("Pas encore l'heure pour cet utilisateur")
            return False
        
        last_run = user_settings.get('last_run')
        if not last_run:
            self.logger.info("Première exécution")
            return True
        
        try:
            last_run_date = datetime.fromisoformat(last_run)
            frequency = user_settings.get('frequency', 'weekly')
            
            # Pour les planifications par jour/heure, on ne vérifie pas la fréquence temporelle
            # On s'exécute si c'est le bon jour et la bonne heure
            if frequency in ['daily', 'weekly', 'monthly']:
                # Pour les planifications par jour/heure, on s'exécute toujours si c'est le bon moment
                # On ne bloque pas les exécutions multiples le même jour
                self.logger.info(f"Planification par jour/heure - Exécution autorisée")
                return True
            else:
                # Pour les autres fréquences, utiliser l'ancienne logique
                if frequency == 'daily':
                    should_run = datetime.now() - last_run_date >= timedelta(days=1)
                elif frequency == 'weekly':
                    should_run = datetime.now() - last_run_date >= timedelta(weeks=1)
                elif frequency == 'monthly':
                    should_run = datetime.now() - last_run_date >= timedelta(days=30)
                else:
                    should_run = True
                
                if should_run:
                    self.logger.info(f"Temps d'exécution - Fréquence: {frequency}")
                else:
                    self.logger.info(f"Pas encore le temps - Fréquence: {frequency}")
                
                return should_run
            
        except Exception as e:
            self.logger.error(f"Erreur vérification fréquence: {e}")
            return True
        
        return False
    
    def is_scheduled_time(self, user_settings):
        """Vérifie si c'est le bon jour et la bonne heure pour l'exécution"""
        try:
            schedule_day = user_settings.get('schedule_day', 'monday')
            schedule_time = user_settings.get('schedule_time', '09:00')
            
            now = datetime.now()
            current_day = now.strftime('%A').lower()
            current_time = now.strftime('%H:%M')
            
            # Vérifier le jour (pour les fréquences weekly/monthly)
            if user_settings.get('frequency', 'weekly') in ['weekly', 'monthly']:
                if current_day != schedule_day.lower():
                    self.logger.info(f"Jour incorrect - Actuel: {current_day}, Attendu: {schedule_day.lower()}")
                    return False
                else:
                    self.logger.info(f"Jour correct - {current_day}")
            
            # Vérifier l'heure (avec une marge de 30 minutes pour GitHub Actions)
            target_hour = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            current_hour = now.hour
            current_minute = now.minute
            
            # GitHub Actions s'exécute à l'heure pile, on accepte +/- 30 minutes
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour * 60 + target_minute))
            self.logger.info(f"Heure - Actuelle: {current_hour}:{current_minute:02d}, Cible: {target_hour}:{target_minute:02d}, Diff: {time_diff}min")
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
    
    def process_user_newsletters(self, user_info):
        """Traite les newsletters pour un utilisateur et génère le résumé"""
        try:
            self.logger.info(f"🔄 Traitement pour {user_info['email']}")
            
            newsletters = user_info['newsletters']
            if not newsletters:
                self.logger.warning(f"⚠️ Aucune newsletter pour {user_info['email']}")
                return False
            
            # En mode GitHub Actions, on simule le traitement
            # Dans un vrai déploiement, on ferait appel à l'API de l'application Streamlit
            self.logger.info(f"✅ {len(newsletters)} newsletters à traiter pour {user_info['email']}")
            self.logger.info(f"📧 Newsletters: {', '.join(newsletters)}")
            
            # Mettre à jour la date de dernière exécution
            self.update_last_run(user_info['email'])
            
            # Générer le vrai résumé avec l'IA
            try:
                # Simuler une session utilisateur pour NewsletterManager
                import streamlit as st
                st.session_state['user_email'] = user_info['email']
                st.session_state['authenticated'] = True
                
                self.logger.info(f"🔧 Configuration session: user_email={user_info['email']}")
                
                from newsletter_manager import NewsletterManager
                newsletter_manager = NewsletterManager()
                
                # Forcer l'email utilisateur dans le NewsletterManager
                newsletter_manager.user_email = user_info['email']
                
                # Passer directement les données utilisateur
                newsletter_manager.newsletters = user_info.get('newsletters', [])
                newsletter_manager.user_settings = user_info.get('settings', {})
                
                # Désactiver la sauvegarde dans le scheduler
                newsletter_manager._scheduler_mode = True
                
                # Configurer l'accès Gmail pour le NewsletterManager
                try:
                    from secure_auth import SecureAuth
                    auth = SecureAuth()
                    
                    # Récupérer les credentials de l'utilisateur depuis le Gist
                    user_credentials = self.get_user_credentials_from_gist(user_info['email'])
                    if user_credentials:
                        # Convertir les credentials en JSON string pour SecureAuth
                        import json
                        credentials_json = json.dumps(user_credentials)
                        auth.set_external_credentials(credentials_json)
                    else:
                        self.logger.error(f"❌ Aucun token OAuth2 trouvé pour {user_info['email']} dans le Gist")
                        return False
                    
                    # Configurer l'auth pour le NewsletterManager
                    newsletter_manager.auth = auth
                except Exception as e:
                    self.logger.error(f"❌ Erreur configuration Gmail auth: {e}")
                    return False
                
                # Générer le résumé avec l'IA et envoyer l'email
                days_to_analyze = user_info.get('settings', {}).get('days_to_analyze', 7)
                summary_result = newsletter_manager.process_newsletters(days=days_to_analyze, send_email=True)
                
                # Vérifier le résultat
                if summary_result is True or (isinstance(summary_result, str) and summary_result.strip()):
                    self.logger.info(f"📄 Résumé IA généré et email envoyé avec succès pour {user_info['email']} le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                    return True
                elif summary_result is None:
                    self.logger.info(f"ℹ️ Aucun email trouvé pour {user_info['email']} - Traitement réussi mais rien à traiter")
                    return True  # Pas d'erreur, juste rien à traiter
                else:
                    self.logger.error(f"❌ Échec génération résumé IA pour {user_info['email']}")
                    self.logger.error(f"❌ Vérifiez les credentials Google et les permissions Gmail")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur génération résumé IA: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement {user_info['email']}: {e}")
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
    
    def update_last_run(self, user_email):
        """Met à jour la date de dernière exécution pour un utilisateur dans GitHub Gist"""
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
                    
                    # Mettre à jour la date pour cet utilisateur
                    if user_email in all_users_data:
                        all_users_data[user_email]['settings']['last_run'] = datetime.now().isoformat()
                        
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
                            self.logger.info(f"✅ Date de dernière exécution mise à jour pour {user_email}")
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
        self.logger.info(f"👥 {len(users)} utilisateurs avec auto-send activé")
        
        processed = 0
        for user_info in users:
            if self.should_run_for_user(user_info['settings']):
                self.logger.info(f"⏰ Il est temps de traiter {user_info['email']}")
                
                if self.process_user_newsletters(user_info):
                    processed += 1
                    self.logger.info(f"✅ Traitement réussi pour {user_info['email']}")
                else:
                    self.logger.error(f"❌ Échec traitement pour {user_info['email']}")
            else:
                self.logger.info(f"⏳ Pas encore l'heure pour {user_info['email']}")
        
        self.logger.info(f"🎯 Scheduler terminé - {processed} utilisateurs traités")
        return processed

def main():
    """Point d'entrée principal"""
    scheduler = AutoBriefScheduler()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()
