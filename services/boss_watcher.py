import requests
from bs4 import BeautifulSoup
import re
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

def check_boss_updates():
    """
    Lit le flux RSS BOSS et renvoie TOUJOURS :
    (html_message, link)
    """
    try:
        url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            return "<div style='color:red;'>⚠️ Flux RSS inaccessible.</div>", ""

        content = response.content.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")
        latest_item = soup.find("item")

        if not latest_item:
            return "<div style='padding:10px; background-color:#f0f2f6; border-radius:5px;'>✅ Veille BOSS : Aucune actualité détectée.</div>", ""

        # 1) Titre
        title_tag = latest_item.find("title")
        title = title_tag.text.strip() if title_tag else "Actualité BOSS"

        # 2) Lien (Regex, plus robuste)
        link_match = re.search(r"<link>(.*?)</link>", str(latest_item))
        link = link_match.group(1).strip() if link_match else "https://boss.gouv.fr"

        # 3) Date
        date_tag = latest_item.find("pubdate") or latest_item.find("pubDate")

        style_alert = "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border: 1px solid #f5c6cb; margin-bottom: 10px;"
        style_success = "background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; border: 1px solid #c3e6cb; margin-bottom: 10px;"

        # Lien HTML (nouvel onglet)
        html_link = f'<a href="{link}" target="_blank" style="text-decoration:underline; font-weight:bold; color:inherit;">{title}</a>'

        if date_tag:
            try:
                pub_date_obj = parsedate_to_datetime(date_tag.text.strip())
                now = datetime.now(timezone.utc)
                days_old = (now - pub_date_obj).days
                date_str = pub_date_obj.strftime("%d/%m/%Y")

                if days_old < 8:
                    html = f"<div style='{style_alert}'>🚨 <strong>NOUVELLE MISE À JOUR BOSS ({date_str})</strong> : {html_link} (Il y a {days_old} jours)</div>"
                    return html, link

                html = f"<div style='{style_success}'>✅ <strong>Veille BOSS (R.A.S)</strong> : Dernière actu du {date_str} : {html_link}</div>"
                return html, link

            except Exception:
                # Si parsing date échoue, on tombe sur un message générique
                pass

        # Fallback si pas de date exploitable
        html = f"<div style='{style_alert}'>📢 ALERTE BOSS : {html_link}</div>"
        return html, link

    except Exception as e:
        return f"<div style='color:red;'>⚠️ Erreur Module Veille : {e}</div>", ""
