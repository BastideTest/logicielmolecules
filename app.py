import base64
from datetime import datetime, timedelta
import urllib.parse
import streamlit as st

# ==========================================
# 1. CONFIGURATION ET STYLES STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Gestion des Ordonnances & Planning",
    page_icon="💊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stButton > button {
        border-radius: 6px;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. INITIALISATION DU SESSION STATE
# ==========================================
if "hopitaux_db" not in st.session_state:
    st.session_state.hopitaux_db = [
        {"nom": "CH de la Côte Basque", "email": "contact@ch-cotebasque.fr"},
        {"nom": "Clinique Belharra", "email": "pharmacist@belharra.fr"},
        {"nom": "CHU de Bordeaux", "email": "ordonnances@chu-bordeaux.fr"},
    ]

if "molecules_db" not in st.session_state:
    st.session_state.molecules_db = [
        {"nom": "Doliprane 1000mg", "forme": "Comprimé"},
        {"nom": "Ketanest 50mg", "forme": "Injectable"},
        {"nom": "Morfina 10mg", "forme": "Gélule"},
        {"nom": "Paracétamol 500mg", "forme": "Comprimé"},
    ]

if "ordonnances" not in st.session_state:
    aujourdhui_ref = datetime.today().date()
    st.session_state.ordonnances = [
        {
            "patient": "Jean Dupont",
            "hopital": "CH de la Côte Basque",
            "molecule": "Doliprane 1000mg",
            "statut": "VALIDÉE",
            "posologie_freq": "3x/jour",
            "posologie_moments": "Matin / Midi / Soir",
            "date_fin": aujourdhui_ref + timedelta(days=5),
        },
        {
            "patient": "Marie Martin",
            "hopital": "Clinique Belharra",
            "molecule": "Ketanest 50mg",
            "statut": "VALIDÉE",
            "posologie_freq": "1x/jour",
            "posologie_moments": "Matin",
            "date_fin": aujourdhui_ref + timedelta(days=9),
        },
        {
            "patient": "Jean Dupont",
            "hopital": "CH de la Côte Basque",
            "molecule": "Morfina 10mg",
            "statut": "VALIDÉE",
            "posologie_freq": "2x/jour",
            "posologie_moments": "Matin / Soir",
            "date_fin": aujourdhui_ref + timedelta(days=12),
        },
    ]

if "renouvellements_faits" not in st.session_state:
    st.session_state.renouvellements_faits = {}

if "date_ref_planning" not in st.session_state:
    aujourdhui = datetime.today().date()
    st.session_state.date_ref_planning = aujourdhui - timedelta(
        days=aujourdhui.weekday()
    )


# ==========================================
# 3. FONCTIONS AUXILIAIRES
# ==========================================
def generer_lien_mailto(
    email, hopital, patient, molecule, jours_restants, date_fin
):
    sujet = f"Demande de renouvellement d'ordonnance - {patient}"
    corps = (
        f"Bonjour,\n\n"
        f"Nous sollicitons le renouvellement du traitement pour le patient suivant :\n"
        f"- Patient : {patient}\n"
        f"- Établissement/Praticien : {hopital}\n"
        f"- Traitement : {molecule}\n"
        f"- Date de fin actuelle : {date_fin.strftime('%d/%m/%Y')} (il reste {jours_restants} jour(s))\n\n"
        f"Merci d'avance pour le retour du document signé.\n\nCordialement,"
    )
    return f"mailto:{email}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"


def extraire_texte(fichier):
    return "Texte extrait de la nouvelle ordonnance", None


def parser_texte(texte):
    return {
        "date_fin": datetime.today().date() + timedelta(days=30),
    }


# ==========================================
# 4. BARRE LATÉRALE DE NAVIGATION
# ==========================================
with st.sidebar:
    st.title("📌 Navigation")
    menu = st.radio(
        "Aller vers :",
        [
            "1. Planning de Roulement",
            "2. Validation Pro",
            "3. Gestion Référentiels (Établissements & Molécules)",
            "4. Liste des Ordonnances",
        ],
    )

# ==========================================
# 5. PLANNING DE ROULEMENT (SECTION 1)
# ==========================================
if menu == "1. Planning de Roulement":
    st.title("🗓️ Planning de Roulement & Renouvellements")

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

    map_hopitaux_email = {
        h["nom"]: h.get("email", "") for h in st.session_state.hopitaux_db
    }

    # Modale 1 : Demande de renouvellement par Email
    @st.dialog("📩 Fiche de renouvellement par Email")
    def ouvrir_dialogue_renouvellement(o, jours_restants, key_cmd):
        st.markdown(f"### Patient : **{o['patient']}**")
        st.write(f"**Établissement / Praticien :** {o['hopital']}")
        st.write(f"**Traitement à renouveler :** {o['molecule']}")
        st.write(
            f"**Posologie :** {o.get('posologie_freq', '')} ({o.get('posologie_moments', '')})"
        )
        st.write(
            f"**Date de fin de traitement :** {o['date_fin'].strftime('%d/%m/%Y')}"
        )
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

            if st.link_button(
                "🚀 Envoyer l'e-mail de renouvellement",
                mailto_url,
                use_container_width=True,
            ):
                st.session_state.renouvellements_faits[key_cmd] = True
                st.toast(
                    "Demande transmise ! La fiche est retirée du planning."
                )
                st.rerun()

            if st.button(
                "Marquer comme envoyé / Retirer du planning",
                use_container_width=True,
            ):
                st.session_state.renouvellements_faits[key_cmd] = True
                st.toast("Demande effectuée et fiche retirée.")
                st.rerun()
        else:
            st.error(
                "⚠️ Aucune adresse e-mail renseignée pour cet établissement."
            )
            st.info(
                "Rendez-vous dans la section **'Gestion Référentiels'** pour ajouter l'e-mail."
            )

    # Modale 2 : Dépôt du fichier de reconduction & choix posologie / molécule
    @st.dialog("📁 Nouvelle ordonnance - reconduction")
    def ouvrir_dialogue_reconduction(o):
        st.markdown(f"### Reconduction pour : **{o['patient']}**")
        st.write(f"**Établissement :** {o['hopital']}")

        st.divider()

        # Choix des molécules existantes
        liste_molecules_noms = [
            m["nom"] for m in st.session_state.molecules_db
        ]
        # Si la molécule actuelle n'est pas dans la liste, on l'ajoute provisoirement pour éviter une erreur
        if o["molecule"] not in liste_molecules_noms:
            liste_molecules_noms.append(o["molecule"])

        index_mol_def = (
            liste_molecules_noms.index(o["molecule"])
            if o["molecule"] in liste_molecules_noms
            else 0
        )
        molecule_choisie = st.selectbox(
            "🧪 Sélectionner la molécule :",
            options=liste_molecules_noms,
            index=index_mol_def,
        )

        col_f, col_m = st.columns(2)
        with col_f:
            freq_choisie = st.selectbox(
                "⏰ Fréquence :",
                options=["1x/jour", "2x/jour", "3x/jour"],
                index=["1x/jour", "2x/jour", "3x/jour"].index(
                    o.get("posologie_freq", "1x/jour")
                )
                if o.get("posologie_freq") in ["1x/jour", "2x/jour", "3x/jour"]
                else 0,
            )

        with col_m:
            moments_options = [
                "Matin",
                "Matin / Midi",
                "Matin / Midi / Soir",
                "Midi / Soir",
                "Matin / Soir",
                "Soir",
            ]
            moment_choisi = st.selectbox(
                "🌅 Moment(s) de prise :",
                options=moments_options,
                index=moments_options.index(o.get("posologie_moments", "Matin"))
                if o.get("posologie_moments") in moments_options
                else 0,
            )

        st.divider()

        fichier_nouveau = st.file_uploader(
            "Déposez la nouvelle ordonnance scannée (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            key=f"file_reconduction_{o['patient']}_{o['molecule']}",
        )

        if fichier_nouveau is not None:
            texte_extrait, img = extraire_texte(fichier_nouveau)
            donnees = parser_texte(texte_extrait)
            donnees["patient"] = o["patient"]
            donnees["hopital"] = o["hopital"]
            donnees["molecule"] = molecule_choisie
            donnees["posologie_freq"] = freq_choisie
            donnees["posologie_moments"] = moment_choisi

            st.session_state["temp_ordonnance"] = {
                "image": fichier_nouveau,
                "data": donnees,
            }
            st.success("Nouvelle ordonnance chargée avec succès !")
            st.info(
                "Rendez-vous dans la section **'2. Validation Pro'** pour valider la reconduction."
            )

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
    jours_semaine = [
        "Lundi",
        "Mardi",
        "Mercredi",
        "Jeudi",
        "Vendredi",
        "Samedi",
        "Dimanche",
    ]
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

            commandes_du_jour = []
            for o in ordonnances_valid:
                date_commande = o["date_fin"] - timedelta(days=7)
                if date_commande == jour_date:
                    commandes_du_jour.append(o)

            commandes_a_afficher = []
            for o in commandes_du_jour:
                key_cmd = f"cmd_{o['patient']}_{o['molecule']}_{o['date_fin'].strftime('%Y%m%d')}"
                if not st.session_state.renouvellements_faits.get(
                    key_cmd, False
                ):
                    commandes_a_afficher.append((o, key_cmd))

            if not commandes_a_afficher:
                st.caption("<em>Aucune commande</em>", unsafe_allow_html=True)
            else:
                for idx_c, (o, key_cmd) in enumerate(commandes_a_afficher):
                    jours_restants = (o["date_fin"] - aujourdhui_real).days

                    st.markdown(
                        f"""
                        <div style="border-left: 4px solid #d9534f; background-color: #fff0f0; padding: 8px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 12px; margin-bottom: 8px;">
                            <strong style="color: #d9534f;">🛒 ROULEMENT À PASSER</strong><br>
                            👤 <strong>{o['patient']}</strong><br>
                            🏥 <small>{o['hopital']}</small><br>
                            💊 {o['molecule']}<br>
                            ⏱️ <small>{o.get('posologie_freq', '')} - {o.get('posologie_moments', '')}</small><br>
                            📅 Fin tt: <strong>{o['date_fin'].strftime('%d/%m/%Y')}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "📩 Renouveler auprès établissement",
                        key=f"btn_renouv_{key_cmd}_{i}",
                        use_container_width=True,
                        type="secondary",
                    ):
                        ouvrir_dialogue_renouvellement(
                            o, jours_restants, key_cmd
                        )

                    if st.button(
                        "📁 Nouvelle ordonnance - reconduction",
                        key=f"btn_reconduct_{key_cmd}_{i}",
                        use_container_width=True,
                        type="primary",
                    ):
                        ouvrir_dialogue_reconduction(o)

                    st.markdown(
                        "<hr style='margin: 10px 0;'>", unsafe_allow_html=True
                    )

# ==========================================
# 6. VALIDATION PRO (SECTION 2)
# ==========================================
elif menu == "2. Validation Pro":
    st.title("📑 Validation des Ordonnances")
    if "temp_ordonnance" in st.session_state:
        temp = st.session_state["temp_ordonnance"]
        st.success("Une ordonnance de reconduction est en attente de validation !")
        
        st.subheader("Détails pré-remplis :")
        st.write(f"**Patient :** {temp['data']['patient']}")
        st.write(f"**Établissement :** {temp['data']['hopital']}")
        st.write(f"**Molécule retenue :** {temp['data']['molecule']}")
        st.write(
            f"**Posologie retenue :** {temp['data'].get('posologie_freq', '')} - {temp['data'].get('posologie_moments', '')}"
        )
        st.write(
            f"**Nouvelle Date de Fin :** {temp['data']['date_fin'].strftime('%d/%m/%Y')}"
        )

        if st.button("✅ Valider l'ordonnance et l'ajouter au système", type="primary"):
            st.session_state.ordonnances.append(
                {
                    "patient": temp["data"]["patient"],
                    "hopital": temp["data"]["hopital"],
                    "molecule": temp["data"]["molecule"],
                    "statut": "VALIDÉE",
                    "posologie_freq": temp["data"].get("posologie_freq", ""),
                    "posologie_moments": temp["data"].get("posologie_moments", ""),
                    "date_fin": temp["data"]["date_fin"],
                }
            )
            del st.session_state["temp_ordonnance"]
            st.success("Ordonnance enregistrée avec succès !")
            st.rerun()
    else:
        st.info("Aucune ordonnance en attente de validation pour le moment.")

# ==========================================
# 7. GESTION DES RÉFÉRENTIELS (SECTION 3)
# ==========================================
elif menu == "3. Gestion Référentiels (Établissements & Molécules)":
    st.title("⚙️ Gestion des Référentiels")

    tab_hopitaux, tab_molecules = st.tabs(
        ["🏥 Établissements de Santé", "🧬 Molécules"]
    )

    # Onglet 1: Hôpitaux
    with tab_hopitaux:
        st.subheader("Liste des Établissements")
        st.dataframe(st.session_state.hopitaux_db, use_container_width=True)

        st.divider()
        st.subheader("➕ Ajouter un Établissement")
        with st.form("form_add_hopital"):
            nouveau_nom = st.text_input("Nom de l'établissement")
            nouvel_email = st.text_input("Adresse E-mail")
            submitted = st.form_submit_button("Ajouter l'établissement")

            if submitted:
                if nouveau_nom and nouvel_email:
                    st.session_state.hopitaux_db.append(
                        {"nom": nouveau_nom, "email": nouvel_email}
                    )
                    st.success(f"Établissement '{nouveau_nom}' ajouté avec succès !")
                    st.rerun()
                else:
                    st.error("Veuillez remplir tous les champs.")

    # Onglet 2: Molécules
    with tab_molecules:
        st.subheader("Liste des Molécules Référencées")
        st.dataframe(st.session_state.molecules_db, use_container_width=True)

        st.divider()
        st.subheader("➕ Ajouter une Molécule")
        with st.form("form_add_molecule"):
            nom_mol = st.text_input("Nom de la molécule (ex: Paracétamol 1g)")
            forme_mol = st.selectbox(
                "Forme galénique",
                ["Comprimé", "Gélule", "Injectable", "Sirop", "Sachet", "Autre"],
            )
            submitted_mol = st.form_submit_button("Ajouter la molécule")

            if submitted_mol:
                if nom_mol:
                    st.session_state.molecules_db.append(
                        {"nom": nom_mol, "forme": forme_mol}
                    )
                    st.success(f"Molécule '{nom_mol}' ajoutée avec succès !")
                    st.rerun()
                else:
                    st.error("Veuillez indiquer au moins le nom de la molécule.")

# ==========================================
# 8. LISTE DES ORDONNANCES (SECTION 4)
# ==========================================
elif menu == "4. Liste des Ordonnances":
    st.title("📋 Liste Globale des Ordonnances")
    st.dataframe(st.session_state.ordonnances, use_container_width=True)
