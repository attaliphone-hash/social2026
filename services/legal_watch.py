import requests
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re
import streamlit as st
from utils.helpers import logger  # ✅ Import du logger centralisé

def get_headers():
    """Headers complets pour éviter le blocage par les sites gouvernementaux"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

def parse_rss_date(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e: 
        logger.warning(f"Veille : Erreur parsing date '{date_str}' : {e}")
        return datetime.now(timezone.utc)

def format_feed_alert(source_name, title, link, pub_date, color_bg_alert="#f8d7da", color_text_alert="#721c24", color_bg_ok="#d4edda", color_text_ok="#155724"):
    days = (datetime.now(timezone.utc) - pub_date).days
    date_str = pub_date.strftime("%d/%m")
    
    if days < 3:
        return f"<div style='background-color:{color_bg_alert}; color:{color_text_alert}; padding:10px; border-radius:6px; border:1px solid {color_bg_alert}; margin-bottom:8px; font-size:13px;'>🚨 <strong>NOUVEAU {source_name} ({date_str})</strong> : <a href='{link}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>{title}</a></div>"
    else:
        return f"<div style='background-color:{color_bg_ok}; color:{color_text_ok}; padding:10px; border-radius:6px; border:1px solid {color_bg_ok}; margin-bottom:8px; font-size:13px; opacity:0.9;'>✅ <strong>Veille {source_name} (R.A.S)</strong> : Dernière actu du {date_str} <a href='{link}' target='_blank' style='margin-left:5px; text-decoration:underline; color:inherit; font-size:11px;'>[Voir]</a></div>"

def get_robust_link(item, default_url):
    try:
        link = item.find('link')
        if link and link.text.strip(): return link.text.strip()
    except Exception as e:
        logger.debug(f"Veille : Impossible d'extraire le lien RSS : {e}")
    return default_url

# --- BOSS (C'est lui qui posait problème de Timeout) ---
def get_boss_status_html():
    target_url = "https://boss.gouv.fr/portail/accueil/actualites.html"
    rss_url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
    try:
        # ✅ CORRECTION ICI : Timeout passé de 20 à 30 secondes pour Cloud Run
        response = requests.get(rss_url, headers=get_headers(), timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                link = get_robust_link(item, target_url)
                date_tag = item.find('pubDate') or item.find('pubdate')
                pub_date = parse_rss_date(date_tag.text) if date_tag else datetime.now(timezone.utc)
                return format_feed_alert("BOSS", title, link, pub_date)
    except Exception as e:
        # On log mais on affiche un message "clean"
        logger.warning(f"Veille BOSS : Échec de récupération du flux - {e}")
    
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille BOSS</strong> : Flux indisponible (Timeout)</div>"

# --- SERVICE PUBLIC ---
def get_service_public_status():
    target_url = "https://entreprendre.service-public.gouv.fr/actualites"
    rss_url = "https://www.service-public.fr/abonnements/rss/actu-actu-pro.rss"
    try:
        # Timeout sécurisé à 10s
        response = requests.get(rss_url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                link = get_robust_link(item, target_url)
                date_tag = item.find('pubDate') or item.find('pubdate')
                pub_date = parse_rss_date(date_tag.text) if date_tag else datetime.now(timezone.utc)
                return format_feed_alert("Service-Public", title, link, pub_date, color_bg_ok="#d1ecf1", color_text_ok="#0c5460")
    except Exception as e:
        logger.warning(f"Veille Service-Public : Échec flux - {e}")
    return ""

# --- NET ENTREPRISES ---
def get_net_entreprises_status():
    target_url = "https://www.net-entreprises.fr/actualites/"
    rss_url = "https://www.net-entreprises.fr/feed/"
    try:
        # Timeout sécurisé à 10s
        response = requests.get(rss_url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                link = get_robust_link(item, target_url)
                date_tag = item.find('pubDate') or item.find('pubdate')
                pub_date = parse_rss_date(date_tag.text) if date_tag else datetime.now(timezone.utc)
                return format_feed_alert("Net-Entreprises", title, link, pub_date, color_bg_ok="#fff3cd", color_text_ok="#856404")
    except Exception as e:
        logger.warning(f"Veille Net-Entreprises : Échec flux - {e}")
    return ""

def show_legal_watch_bar():
    """Affiche la barre de veille complète"""
    if "news_closed" not in st.session_state: st.session_state.news_closed = False
    if st.session_state.news_closed: return

    c1, c2 = st.columns([0.95, 0.05])
    with c1:
        st.markdown(get_boss_status_html(), unsafe_allow_html=True)
        st.markdown(get_service_public_status(), unsafe_allow_html=True)
        st.markdown(get_net_entreprises_status(), unsafe_allow_html=True)
    with c2: 
        if st.button("✖️", key="btn_close_news", help="Masquer"): 
            st.session_state.news_closed = True
            st.rerun()