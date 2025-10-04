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
            response = requests.get(f'https://api.github.com/gists/{gist_id}')
            
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
            self.logger.info("❌ Auto-send désactivé")
            return False
        
        # Vérifier d'abord le jour et l'heure
        if not self.is_scheduled_time(user_settings):
            self.logger.info("⏰ Pas encore l'heure pour cet utilisateur")
            return False
        
        last_run = user_settings.get('last_run')
        if not last_run:
            self.logger.info("✅ Première exécution")
            return True
        
        try:
            last_run_date = datetime.fromisoformat(last_run)
            frequency = user_settings.get('frequency', 'weekly')
            
            # Pour les planifications par jour/heure, on ne vérifie pas la fréquence temporelle
            # On s'exécute si c'est le bon jour et la bonne heure
            if frequency in ['daily', 'weekly', 'monthly']:
                # Pour les planifications par jour/heure, on s'exécute toujours si c'est le bon moment
                # On ne bloque pas les exécutions multiples le même jour
                self.logger.info(f"✅ Planification par jour/heure - Exécution autorisée")
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
                    self.logger.info(f"✅ Temps d'exécution - Fréquence: {frequency}")
                else:
                    self.logger.info(f"⏳ Pas encore le temps - Fréquence: {frequency}")
                
                return should_run
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification fréquence: {e}")
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
                    self.logger.info(f"📅 Jour incorrect - Actuel: {current_day}, Attendu: {schedule_day.lower()}")
                    return False
                else:
                    self.logger.info(f"📅 Jour correct - {current_day}")
            
            # Vérifier l'heure (avec une marge de 30 minutes pour GitHub Actions)
            target_hour = int(schedule_time.split(':')[0])
            target_minute = int(schedule_time.split(':')[1])
            current_hour = now.hour
            current_minute = now.minute
            
            # GitHub Actions s'exécute à l'heure pile, on accepte +/- 30 minutes
            time_diff = abs((current_hour * 60 + current_minute) - (target_hour * 60 + target_minute))
            self.logger.info(f"⏰ Heure - Actuelle: {current_hour}:{current_minute:02d}, Cible: {target_hour}:{target_minute:02d}, Diff: {time_diff}min")
            return time_diff <= 30
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification horaire: {e}")
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
            
            self.logger.info(f"📧 Envoi email pour {to_email}")
            self.logger.info(f"📧 Sujet: {subject}")
            
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
                
                self.logger.info(f"🔧 Données utilisateur passées au NewsletterManager")
                
                # Configurer l'accès Gmail pour le NewsletterManager
                try:
                    from secure_auth import SecureAuth
                    auth = SecureAuth()
                    
                    # Passer les credentials Google depuis GitHub Actions
                    google_credentials = os.getenv('GOOGLE_CREDENTIALS')
                    if google_credentials:
                        auth.set_external_credentials(google_credentials)
                        self.logger.info(f"🔧 Credentials Google configurés pour SecureAuth")
                    else:
                        self.logger.error(f"❌ GOOGLE_CREDENTIALS non trouvé dans les variables d'environnement")
                    
                    # Configurer l'auth pour le NewsletterManager
                    newsletter_manager.auth = auth
                    
                    self.logger.info(f"🔧 Gmail auth configuré pour NewsletterManager")
                except Exception as e:
                    self.logger.error(f"❌ Erreur configuration Gmail auth: {e}")
                
                self.logger.info(f"🔧 NewsletterManager user_email: {newsletter_manager.user_email}")
                self.logger.info(f"🔧 Newsletters configurées: {len(newsletter_manager.newsletters)}")
                
                # Générer le résumé réel avec l'IA
                self.logger.info(f"🔧 Tentative de génération du résumé IA...")
                summary = newsletter_manager.process_newsletters(send_email=False)
                self.logger.info(f"🔧 Résultat process_newsletters: {summary is not None}")
                if summary:
                    self.logger.info(f"🔧 Type du résumé: {type(summary)}")
                    self.logger.info(f"🔧 Longueur: {len(str(summary))}")
                
                if summary:
                    self.logger.info(f"📄 Résumé IA généré pour {user_info['email']} le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                    self.logger.info(f"📄 Longueur du résumé: {len(summary)} caractères")
                else:
                    self.logger.error(f"❌ Échec génération résumé IA pour {user_info['email']}")
                    self.logger.error(f"❌ Vérifiez les credentials Google et les permissions Gmail")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur génération résumé IA: {e}")
                summary = f"<p>Erreur lors de la génération du résumé: {str(e)}</p>"
            
            # Envoyer l'email de résumé
            notification_email = user_info['settings'].get('notification_email')
            if notification_email and notification_email.strip():
                subject = f"📧 Résumé AutoBrief - {datetime.now().strftime('%d/%m/%Y')}"
                content = f"""
                <h2>📧 Résumé de vos newsletters</h2>
                <p>Bonjour,</p>
                <p>Voici votre résumé automatique généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} :</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                    {summary}
                </div>
                <p>---</p>
                <p><em>Généré automatiquement par AutoBrief</em></p>
                """
                
                if self.send_email(notification_email, subject, content):
                    self.logger.info(f"✅ Email de résumé envoyé à {notification_email}")
                else:
                    self.logger.error(f"❌ Échec envoi email à {notification_email}")
            else:
                self.logger.warning(f"⚠️ Aucune adresse email de notification configurée pour {user_info['email']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement {user_info['email']}: {e}")
            return False
    
    
    def update_last_run(self, user_email):
        """Met à jour la date de dernière exécution pour un utilisateur dans GitHub Gist"""
        try:
            gist_id = os.getenv('GIST_ID')
            
            if not gist_id:
                self.logger.error("GIST_ID non trouvé dans les variables d'environnement")
                return
            
            import requests
            
            # Charger les données actuelles du Gist
            response = requests.get(f'https://api.github.com/gists/{gist_id}')
            
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
                        
                        update_response = requests.patch(
                            f'https://api.github.com/gists/{gist_id}',
                            json=update_data,
                            headers={'Accept': 'application/vnd.github.v3+json'}
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
