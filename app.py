# -----------------------------------------------------------------------------
# 5. PLANNING HEBDOMADAIRE - DATES DE COMMANDES ET SUIVI CHECK
# -----------------------------------------------------------------------------
elif menu == "5. Planning Hebdomadaire":
    st.header("📦 Planning des Commandes à Effectuer (7 jours avant la fin)")

    # Initialisation du lundi de référence
    if "date_ref_planning" not in st.session_state:
        aujourdhui = datetime.today().date()
        st.session_state.date_ref_planning = aujourdhui - timedelta(
            days=aujourdhui.weekday()
        )

    # Navigation de semaine en semaine
    c_prev, c_curr, c_next, c_reset = st.columns([1, 2, 1, 1])

    with c_prev:
        if st.button("⬅️ Semaine précédente", use_container_width=True):
            st.session_state.date_ref_planning -= timedelta(days=7)
            st.rerun()

    with c_next:
        if st.button("Semaine suivante ➡️", use_container_width=True):
            st.session_state.date_ref_planning += timedelta(days=7)
            st.rerun()

    with c_reset:
        if st.button("📅 Aujourd'hui", use_container_width=True):
            aujourdhui = datetime.today().date()
            st.session_state.date_ref_planning = aujourdhui - timedelta(
                days=aujourdhui.weekday()
            )
            st.rerun()

    lundi_semaine = st.session_state.date_ref_planning
    dimanche_semaine = lundi_semaine + timedelta(days=6)

    with c_curr:
        st.markdown(
            f"<h4 style='text-align: center; color: #1E88E5;'>"
            f"Semaine du {lundi_semaine.strftime('%d/%m/%Y')} au {dimanche_semaine.strftime('%d/%m/%Y')}"
            f"</h4>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Dictionnaire des e-mails des hôpitaux
    map_hopitaux_email = {
        h["nom"]: h.get("email", "") for h in st.session_state.hopitaux_db
    }

    # Fenêtre Modale pour le renouvellement par Email
    @st.dialog("📩 Fiche de renouvellement par Email")
    def ouvrir_dialogue_renouvellement(o, jours_restants):
        st.markdown(f"### Patient : **{o['patient']}**")
        st.write(f"**Établissement / Praticien :** {o['hopital']}")
        st.write(f"**Traitement à renouveler :** {o['molecule']}")
        st.write(f"**Date de fin de traitement :** {o['date_fin'].strftime('%d/%m/%Y')}")
        st.write(f"**Jours restants :** {jours_restants} jour(s)")

        email_dest = map_hopitaux_email.get(o["hopital"], "")

        st.divider()
        if email_dest:
            st.success(f"📧 Adresse e-mail trouvée : `{email_dest}`")
            mailto_url = generer_lien_mailto(
                email_dest,
                o["hopital"],
                o["patient"],
                o["molecule"],
                jours_restants,
                o["date_fin"],
            )
            st.link_button(
                "🚀 Ouvrir Outlook / Mail pour envoyer",
                mailto_url,
                use_container_width=True,
            )
        else:
            st.error("⚠️ Aucune adresse e-mail renseignée pour cet établissement dans l'annuaire.")
            st.info("Rendez-vous dans le menu **'4. Gestion Établissements'** pour ajouter son e-mail.")

    # Filtre patient
    patients_dispo = ["Tous les patients"] + sorted(
        list(set([o["patient"] for o in st.session_state.ordonnances]))
    )
    filtre_patient_plan = st.selectbox(
        "🔎 Filtrer par patient :", patients_dispo
    )

    ordonnances_valid = [
        o for o in st.session_state.ordonnances if o["statut"] == "VALIDÉE"
    ]
    if filtre_patient_plan != "Tous les patients":
        ordonnances_valid = [
            o
            for o in ordonnances_valid
            if o["patient"] == filtre_patient_plan
        ]

    # Grille 7 jours
    jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    cols_jours = st.columns(7)
    aujourdhui_real = datetime.today().date()

    for i in range(7):
        jour_date = lundi_semaine + timedelta(days=i)
        nom_jour = jours_semaine[i]

        with cols_jours[i]:
            style_entete = (
                "background-color: #1E88E5; color: white;"
                if jour_date == aujourdhui_real
                else "background-color: #f0f2f6; color: #333;"
            )

            st.markdown(
                f"""
                <div style="{style_entete} text-align: center; padding: 6px; border-radius: 6px; font-weight: bold; margin-bottom: 10px;">
                    {nom_jour}<br><small>{jour_date.strftime('%d/%m')}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Identification des commandes dues ce jour-là (date de fin - 7 jours)
            commandes_du_jour = []
            for o in ordonnances_valid:
                date_commande = o["date_fin"] - timedelta(days=7)
                if date_commande == jour_date:
                    commandes_du_jour.append(o)

            if not commandes_du_jour:
                st.caption("<em>Aucune commande</em>", unsafe_allow_html=True)
            else:
                for idx_c, o in enumerate(commandes_du_jour):
                    key_cmd = f"cmd_{o['patient']}_{o['molecule']}_{o['date_fin'].strftime('%Y%m%d')}"
                    jours_restants = (o["date_fin"] - aujourdhui_real).days

                    # 1. BOUTON RENOUVELLEMENT (ouvre la fiche mail)
                    if st.button(
                        "📩 Renouveler",
                        key=f"btn_renouv_{key_cmd}_{i}",
                        use_container_width=True,
                    ):
                        ouvrir_dialogue_renouvellement(o, jours_restants)

                    # 2. CASE À COCHER (Commande faite)
                    est_fait = st.session_state.commandes_faites.get(key_cmd, False)
                    coché = st.checkbox(
                        "Commandé",
                        value=est_fait,
                        key=f"chk_{key_cmd}_{i}",
                    )
                    
                    st.session_state.commandes_faites[key_cmd] = coché

                    # Visualisation du statut
                    if coché:
                        st.markdown(
                            f"""
                            <div style="border-left: 4px solid #888; background-color: #e8e8e8; padding: 6px; border-radius: 4px; font-size: 11px; text-decoration: line-through; color: #666;">
                                <strong>✔️ {o['patient']}</strong><br>
                                💊 {o['molecule']}<br>
                                📅 Fin: {o['date_fin'].strftime('%d/%m')}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div style="border-left: 4px solid #ff4d4d; background-color: #fff0f0; padding: 6px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 11px;">
                                <strong>🛒 COMMANDER</strong><br>
                                👤 <strong>{o['patient']}</strong><br>
                                💊 {o['molecule']}<br>
                                <small style="color: #d9534f;">Fin tt: {o['date_fin'].strftime('%d/%m')}</small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    st.markdown("<br>", unsafe_allow_html=True)
