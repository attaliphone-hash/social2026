import streamlit as st

class UIComponents:
    
    # --- 1. LE HEADER (TITRE EXACT) ---
    @staticmethod
    def render_header_title():
        """Affiche le Titre et le Sous-titre (Alignement Gauche comme Capture 1)"""
        st.markdown("""
            <h1 style='text-align: left; color: #253E92; margin-top: 10px;'>
                EXPERT SOCIAL PRO — VOTRE COPILOTE RH & PAIE EN 2026.
            </h1>
            <h2 style='text-align: left; text-transform: none !important; color: #253E92; font-family: "Open Sans", sans-serif; font-size: 20px; font-weight: 600; margin-bottom: 20px; line-height: 1.5;'>
                Des règles officielles. Des calculs sans erreur. Des décisions que vous pouvez défendre.
            </h2>
        """, unsafe_allow_html=True)

    # --- 2. LA BARRE DE RÉASSURANCE (TEXTES COMPLETS & LAYOUT COLONNES) ---
    @staticmethod
    def render_top_arguments():
        """Affiche la barre de réassurance avec les TEXTES LONGS"""
        st.markdown("""
        <style>
        /* MOBILE */
        .mobile-header-text { 
            display: block !important; 
            text-align: left;
            font-family: 'Source Sans Pro', sans-serif;
            font-size: 11px;
            color: #555;
            margin-bottom: 20px;
            line-height: 1.6;
            padding: 0 5px;
        }
        .desktop-container { display: none !important; }

        /* DESKTOP (VOTRE LAYOUT EXACT) */
        @media (min-width: 768px) {
            .mobile-header-text { display: none !important; }
            .desktop-container { 
                display: flex !important;
                flex-direction: row;
                justify-content: space-between;
                gap: 20px;
                width: 100%;
                margin-bottom: 30px;
            }
        }
        .desktop-col { flex: 1; text-align: left; }
        .arg-title { color: #024c6f; font-weight: 700; font-size: 13px; margin-bottom: 5px; }
        .arg-desc { color: #555; font-size: 11px; line-height: 1.4; }
        .sep { color: #ccc; margin: 0 5px; }
        </style>

        <div class="mobile-header-text">
            Données Certifiées 2026 <span class="sep">-</span>
            Sources Officielles <span class="sep">-</span>
            Mise à jour Agile <span class="sep">-</span>
            Traçabilité <span class="sep">-</span>
            Confidentialité
        </div>

        <div class="desktop-container">
            <div class="desktop-col">
                <div class="arg-title">Données Certifiées 2026 :</div>
                <div class="arg-desc">Intégration prioritaire des nouveaux textes pour une précision chirurgicale.</div>
            </div>
            <div class="desktop-col">
                <div class="arg-title">Sources officielles :</div>
                <div class="arg-desc">Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux.</div>
            </div>
            <div class="desktop-col">
                <div class="arg-title">Mise à Jour Agile :</div>
                <div class="arg-desc">Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente.</div>
            </div>
            <div class="desktop-col">
                <div class="arg-title">Traçabilité Totale :</div>
                <div class="arg-desc">Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique.</div>
            </div>
            <div class="desktop-col">
                <div class="arg-title">Confidentialité Garantie :</div>
                <div class="arg-desc">Aucun cookie publicitaire. Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais utilisées pour entraîner des modèles d'IA.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 3. LES ABONNEMENTS (COMPACT & HAUTEUR RÉDUITE) ---
    @staticmethod
    def render_subscription_cards():
        """Affiche les cartes de prix - Version Ultra Compacte (Hauteur mini)"""
        # Toujours le ratio [1, 1, 2] pour l'alignement gauche
        col1, col2, col_vide = st.columns([1, 1, 2], gap="small")

        with col1:
            # J'ai passé le padding à 10px et mis margin:0 partout
            st.markdown("""
            <div style="background-color: #e3f2fd; padding: 10px 15px; border-radius: 8px; border: 1px solid #90caf9;">
                <h3 style="color: #1565c0; margin: 0; font-size: 16px;">Mensuel</h3>
                <div style="margin-top: 5px; margin-bottom: 5px;">
                    <span style="color: #0d47a1; font-size: 20px; font-weight: bold;">35 €</span> 
                    <span style="font-size:12px; color:#555;">HT / MOIS</span>
                </div>
                <p style="color: #444; font-size: 11px; margin: 0; line-height: 1.2;">Sans engagement</p>
            </div>
            """, unsafe_allow_html=True)
            # Le bouton Streamlit ajoute sa propre hauteur qu'on ne peut pas réduire facilement
            st.link_button("Je m'abonne (35€)", "https://buy.stripe.com/6oUeVf4U0enk1g07Q77AI01", use_container_width=True)

        with col2:
            st.markdown("""
            <div style="background-color: #e8f5e9; padding: 10px 15px; border-radius: 8px; border: 1px solid #a5d6a7;">
                <h3 style="color: #2e7d32; margin: 0; font-size: 16px;">Annuel</h3>
                <div style="margin-top: 5px; margin-bottom: 5px;">
                    <span style="color: #1b5e20; font-size: 20px; font-weight: bold;">350 €</span> 
                    <span style="font-size:12px; color:#555;">HT / AN</span>
                </div>
                <p style="color: #444; font-size: 11px; margin: 0; line-height: 1.2;">✅ 2 mois offerts</p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("Je m'abonne (350€)", "https://buy.stripe.com/8x25kFgCIgvscYI2vN7AI00", use_container_width=True)

    # --- 4. LE MANIFESTE (TEXTE VALIDÉ) ---
    @staticmethod
    @st.dialog("Pourquoi Expert Social Pro existe ?")
    def modal_manifesto():
        st.markdown("""
        <style>
            .manifesto-box { font-family: 'Open Sans', sans-serif; color: #1e293b; line-height: 1.6; font-size: 14px; }
            .manifesto-title { color: #024c6f; font-size: 16px; font-weight: 700; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }
            .manifesto-intro { font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 15px; font-style: italic; }
            .manifesto-highlight { color: #b91c1c; font-weight: 700; }
            .manifesto-list { margin-left: 20px; margin-bottom: 15px; }
            .manifesto-check { color: #15803d; font-weight: bold; font-size: 15px; }
            .manifesto-punchline { margin-top: 20px; padding-top: 15px; border-top: 1px dashed #cbd5e1; text-align: center; font-size: 16px; font-weight: 800; color: #024c6f; }
        </style>
        <div class="manifesto-box">
            <p>Pendant des années, j’ai vu des professionnels RH passer des heures à chercher la bonne règle...</p>
            <p>Le problème n’était pas le manque d’information.<br>
            <span class="manifesto-highlight">C’était l’excès d’information.</span></p>
            <div class="manifesto-title">Aujourd’hui :</div>
            <ul class="manifesto-list">
                <li>Tout existe,</li>
                <li>Tout est accessible,</li>
                <li>Mais rien n’est centralisé intelligemment.</li>
            </ul>
            <p>👉 <strong>Résultat :</strong> des décisions prises avec un doute permanent.</p>
            <div class="manifesto-title">Une seule mission</div>
            <p>J’ai créé Expert Social Pro pour répondre à une seule question :</p>
            <div class="manifesto-intro">“Est-ce que je peux décider sereinement ?”</div>
            <p style="margin-left: 10px;">
            <span class="manifesto-check">✅ Mais : “Est-ce que c’est juridiquement sûr ?”</span>
            </p>
            <div class="manifesto-punchline">
                Expert Social Pro n’est pas une IA qui répond.<br>
                <span style="color: #b91c1c;">C’est une IA qui sécurise.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. MENTIONS LÉGALES & RGPD ---
    @staticmethod
    @st.dialog("Mentions Légales")
    def modal_mentions():
        st.markdown(f"""
        <div style='font-size: 12px; color: #1e293b; font-family: sans-serif;'>
            <p>ÉDITEUR DU SITE<br>Le site <em>socialexpertfrance.fr</em> est édité par <strong>Sylvain Attal EI (BUSINESS AGENT AI)</strong>.<br>SIREN : 948253711</p>
            <p>HÉBERGEMENT<br>Google Cloud EMEA Limited</p>
            <p>LIMITATION DE RESPONSABILITÉ (IA)<br>Ne remplace pas une consultation juridique.</p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    @st.dialog("Politique de Confidentialité")
    def modal_rgpd():
        st.markdown(f"""
        <div style='font-size: 13px; color: #1e293b; font-family: sans-serif;'>
            <p><strong>PROTECTION DES DONNÉES :</strong></p>
            <ul>
                <li><strong>Cookies :</strong> Technique uniquement.</li>
                <li><strong>Traçage :</strong> Aucun traceur publicitaire.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # --- 6. LE FOOTER ---
    @staticmethod
    def render_footer():
        """Affiche le footer avec le bouton Manifeste et les liens légaux"""
        st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
        c_line = st.columns([2.2, 0.8, 0.8, 2.2], vertical_alignment="center")

        with c_line[0]: 
            if st.button("Pourquoi Expert Social Pro existe", type="primary", key="btn_manif"):
                UIComponents.modal_manifesto()
        with c_line[1]: 
            if st.button("Mentions Légales", type="tertiary", key="btn_mentions"):
                UIComponents.modal_mentions()
        with c_line[2]: 
            if st.button("Confidentialité", type="tertiary", key="btn_rgpd"):
                 UIComponents.modal_rgpd()
        st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)
        
    @staticmethod
    def render_user_profile(user_info):
        """Petit encart profil"""
        st.write(f"👤 {user_info.get('email', 'Invité')}")