import requests
from bs4 import BeautifulSoup
import re
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

def check_boss_updates():
    """
    Scrape le FLUX RSS avec extraction ROBUSTE (Regex) pour le lien.
    Renvoie du HTML pour permettre l'ouverture dans un nouvel onglet.
    URL : https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss
    """
    try:
        url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            # On récupère le contenu brut pour l'extraction Regex
            content = response.content.decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            latest_item = soup.find('item')
            
            if latest_item:
                # 1. Extraction Titre (Via Soup)
                title_tag = latest_item.find('title')
                title = title_tag.text.strip() if title_tag else "Actualité BOSS"
                
                # 2. Extraction Lien (Via REGEX car html.parser casse la balise <link> du RSS)
                # On cherche le pattern <link>...</link> dans la chaine brute de l'item
                link_match = re.search(r"<link>(.*?)</link>", str(latest_item))
                link = link_match.group(1).strip() if link_match else "https://boss.gouv.fr"
                
                # 3. Extraction Date
                date_tag = latest_item.find('pubdate') or latest_item.find('pubDate')
                
                # Styles CSS pour l'affichage HTML (similaire à st.error/st.success)
                style_alert = "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border: 1px solid #f5c6cb; margin-bottom: 10px;"
                style_success = "background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; border: 1px solid #c3e6cb; margin-bottom: 10px;"
                
                if date_tag:
                    try:
                        pub_date_obj = parsedate_to_datetime(date_tag.text.strip())
                        now = datetime.now(timezone.utc)
                        days_old = (now - pub_date_obj).days
                        date_str = pub_date_obj.strftime("%d/%m/%Y")
                        
                        # Création du lien HTML avec target="_blank" pour ouvrir un nouvel onglet
                        html_link = f'<a href="{link}" target="_blank" style="text-decoration:underline; font-weight:bold; color:inherit;">{title}</a>'
                        
                        # Seuil 8 jours
                        if days_old < 8:
                            # ALERTE ROUGE
                            return f"""<div style='{style_alert}'>🚨 <strong>NOUVELLE MISE À JOUR BOSS ({date_str})</strong> : {html_link} (Il y a {days_old} jours)</div>"""
                        else:
                            # INFO VERTE
                            return f"""<div style='{style_success}'>✅ <strong>Veille BOSS (R.A.S)</strong> : Dernière actu du {date_str} : {html_link}</div>"""
                            
                    except:
                        pass # Si erreur date, on passe au fallback
                
                # Fallback simple (si pas de date ou erreur)
                return f"""<div style='{style_alert}'>📢 ALERTE BOSS : <a href="{link}" target="_blank" style="color:inherit; font-weight:bold;">{title}</a></div>"""
            
            return "<div style='padding:10px; background-color:#f0f2f6; border-radius:5px;'>✅ Veille BOSS : Aucune actualité détectée.</div>"
            
        return "<div style='color:red;'>⚠️ Flux RSS inaccessible.</div>"
    except Exception as e:
        return f"<div style='color:red;'>⚠️ Erreur Module Veille : {e}</div>"