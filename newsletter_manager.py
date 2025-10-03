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

class NewsletterManager:
    def __init__(self):
        self.config = Config()
        self.auth = SecureAuth()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        
    def save_newsletters(self, newsletters):
        """Sauvegarde la liste des newsletters dans la session"""
        st.session_state['newsletters'] = newsletters
        
    def get_newsletters(self):
        """Récupère la liste des newsletters depuis la session"""
        return st.session_state.get('newsletters', [])
    
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
    
    def process_newsletters(self, days=7):
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
        
        return output

