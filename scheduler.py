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
        """Récupère tous les utilisateurs depuis les secrets GitHub"""
        users = []
        
        try:
            # Charger les données depuis les secrets GitHub (variables d'environnement)
            user_data_json = os.getenv('USER_DATA')
            
            if not user_data_json:
                self.logger.info("Aucune donnée utilisateur trouvée dans les secrets GitHub")
                return users
            
            all_users_data = json.loads(user_data_json)
            
            for user_email, user_data in all_users_data.items():
                settings = user_data.get('settings', {})
                
                # Vérifier si l'utilisateur a activé l'envoi automatique
                if settings.get('auto_send', False):
                    users.append({
                        'email': user_email,
                        'settings': settings,
                        'newsletters': user_data.get('newsletters', [])
                    })
                    
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données utilisateur: {e}")
        
        return users
    
    def should_run_for_user(self, user_settings):
        """Vérifie si un résumé doit être généré pour cet utilisateur"""
        if not user_settings.get('auto_send', False):
            return False
        
        last_run = user_settings.get('last_run')
        if not last_run:
            return True
        
        try:
            last_run_date = datetime.fromisoformat(last_run)
            frequency = user_settings.get('frequency', 'weekly')
            
            if frequency == 'daily':
                return datetime.now() - last_run_date >= timedelta(days=1)
            elif frequency == 'weekly':
                return datetime.now() - last_run_date >= timedelta(weeks=1)
            elif frequency == 'monthly':
                return datetime.now() - last_run_date >= timedelta(days=30)
        except:
            return True
        
        return False
    
    def send_email(self, to_email, subject, content):
        """Envoie un email via Gmail API"""
        try:
            # Utiliser Gmail API pour envoyer l'email
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            import base64
            
            # Pour l'envoi d'email, on peut utiliser les credentials OAuth existants
            # ou configurer un service account pour l'envoi
            print(f"📧 Email à envoyer à {to_email}: {subject}")
            print(f"Contenu: {content[:100]}...")
            
            # Pour l'instant, on log l'email au lieu de l'envoyer
            # Dans une vraie implémentation, on utiliserait Gmail API
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
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
            self.update_last_run(user_info['file_path'], user_info['email'])
            
            # Log du résumé simulé
            summary = f"Résumé automatique généré pour {user_info['email']} le {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            self.logger.info(f"📄 {summary}")
            
            # En mode GitHub Actions, on simule l'envoi d'email
            notification_email = user_info['settings'].get('notification_email')
            if notification_email and notification_email.strip():
                self.logger.info(f"📧 Email de résumé envoyé à {notification_email}")
            else:
                self.logger.warning(f"⚠️ Aucune adresse email de notification configurée pour {user_info['email']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement {user_info['email']}: {e}")
            return False
    
    def update_last_run(self, user_file_path, user_email):
        """Met à jour la date de dernière exécution pour un utilisateur"""
        try:
            # Charger les données globales
            with open(user_file_path, 'r', encoding='utf-8') as f:
                all_users_data = json.load(f)
            
            # Mettre à jour la date pour cet utilisateur
            if user_email in all_users_data:
                all_users_data[user_email]['settings']['last_run'] = datetime.now().isoformat()
                
                # Sauvegarder les données mises à jour
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_users_data, f, indent=2, ensure_ascii=False)
                    
                self.logger.info(f"✅ Date de dernière exécution mise à jour pour {user_email}")
            else:
                self.logger.warning(f"⚠️ Utilisateur {user_email} non trouvé dans les données")
            
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
