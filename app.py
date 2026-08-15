from datetime import datetime, timedelta
import hashlib
import json
import os
import re
import urllib.parse
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st

# ==============================================================================
# CONFIGURATION DE LA PAGE
# ==============================================================================
st.set_page_config(
    page_title="PharmaScan & Planning Hospitalier",
    page_icon="🏥",
    layout="wide",
)

# ==============================================================================
# INITIALISATION DU SESSION STATE
# ==============================================================================
if "hopitaux_db" not in st.session_state:
    st.session_state.hopitaux_db = [
        {"nom": "CH de la Côte Basque", "email": "contact@ch-cotebasque.fr"},
        {"nom": "Clinique Belharra", "email": "pharmacist@belharra.fr"},
        {"nom": "CHU de Bordeaux", "email": "ordonnances@chu-bordeaux.fr"},
    ]

if "ordonnances" not in st.session_state:
    st.session_state.ordonnances = [
        {
            "patient": "Dupont Jean",
            "hopital": "CH de la Côte Basque",
            "molecule": "Morfina 10mg",
            "date_fin": datetime.today().date() + timedelta(days=5),
            "statut": "VALIDÉE",
            "ordonnance_valide": True,
        },
        {
            "patient": "Martin Sophie",
            "hopital": "Clinique Belharra",
            "molecule": "Ketanest 50mg",
            "date_fin": datetime.today().date() + timedelta(days=2),
            "statut": "VALIDÉE",
            "ordonnance_valide": True,
        },
    ]

if "renouvellements_faits" not in st.session_state:
    st.session_state.renouvellements_faits = {}


# ==============================================================================
# FONCTIONS AUXILIAIRES
# ==============================================================================
def extraire_texte(fichier):
    try:
        img = Image.open(fichier)
        texte = pytesseract.image_to_string(img, lang="fra")
        return texte, img
    except Exception as e:
        st.warning(f"Note OCR : Tesseract non disponible ou erreur ({e}).")
        return "Texte simulé pour démonstration", None


def parser_texte(texte):
    def chercher_cle(cle, defaut="Non renseigné"):
        m = re.search(f"{cle}\\s*:\\s*(.*)", texte, re.IGNORECASE)
        return m.group(1).strip() if m else defaut

    date_fin_str = chercher_cle("Date de fin")
    try:
        date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y").date()
    except ValueError:
        date_fin = datetime.today().date() + timedelta(days=30)

    return {
        "patient": chercher_cle("Nom du patient"),
        "hopital": chercher_cle("Établissement"),
        "molecule": chercher_cle("Médicament / Molécule"),
        "date_fin": date_fin,
    }


def generer_lien_mailto(
    email, hopital, patient, molecule, jours_restants, date_fin
):
    sujet = f"Demande de renouvellement d'ordonnance - Patient {patient}"
    corps = (
        f"Bonjour,\n\n"
        f"Nous sollicitons le renouvellement de l'ordonnance pour le patient suivant :\n"
        f"- Patient : {patient}\n"
        f"- Établissement / Praticien : {hopital}\n"
        f"- Traitement : {molecule}\n"
        f"- Date de fin de traitement : {date_fin.strftime('%d/%m/%Y')} (Jours restants : {jours_restants})\n\n"
        f"Merci de bien vouloir nous transmettre la nouvelle ordonnance signée.\n\n"
        f"Cordialement,\n"
        f"L'équipe Pharmacie"
    )
    return f"mailto:{email}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"


# ==============================================================================
# BARRE LATÉRALE DE NAVIGATION
# ==============================================================================
st.sidebar.title("🏥 Navigation")
menu = st.sidebar.radio(
    "Aller à",
    [
        "1. Numérisation Ordonnance",
        "2. Validation Pro",
        "3. Planning de Roulement",
        "4. Liste des Ordonnances",
        "5. Annuaire Établissements",
    ],
)

# ==============================================================================
# MENU 1 : NUMÉRISATION ORDONNANCE
# ==============================================================================
if menu == "1. Numérisation Ordonnance":
    st.title("📷 Numériser une nouvelle ordonnance")
    fichier = st.file_uploader(
        "Importer l'ordonnance (JPG, PNG)", type=["jpg", "jpeg", "png"]
    )

    if fichier:
        texte_extrait, img = extraire_texte(fichier)
        donnees = parser_texte(texte_extrait)

        st.session_state["temp_ordonnance"] = {
            "image": fichier,
            "data": donnees,
        }

        col1, col2 = st.columns(2)
        with col1:
            if img:
                st.image(img, use_container_width=True)
            else:
                st.info("Aperçu de l'image non disponible.")
        with col2:
            st.success("Extrait récapitulatif :")
            st.json(donnees)
            st.info(
                "Allez dans le menu **2. Validation Pro** pour enregistrer cette ordonnance."
            )

# ==============================================================================
# MENU 2 : VALIDATION PRO
# ==============================================================================
elif menu == "2. Validation Pro":
    st.title("✅ Validation Professionnelle")

    if "temp_ordonnance" in st.session_state:
        temp = st.session_state["temp_ordonnance"]
        data = temp["data"]

        with st.form("form_valider"):
            st.subheader("Vérification des informations")
            patient = st.text_input("Nom du Patient", value=data["patient"])

            hopitaux_noms = [h["nom"] for h in st.session_state.hopitaux_db]
            idx_h = (
                hopitaux_noms.index(data["hopital"])
                if data["hopital"] in hopitaux_noms
                else 0
            )
            hopital = st.selectbox(
                "Établissement / Praticien",
                hopitaux_noms,
                index=idx_h if hopitaux_noms else 0,
            )

            molecule = st.text_input(
                "Traitement / Molécule", value=data["molecule"]
            )
            date_fin = st.date_input(
                "Date de fin de traitement", value=data["date_fin"]
            )

            valider = st.form_submit_button("Valider et Enregistrer")

            if valider:
                st.session_state.ordonnances.append(
                    {
                        "patient": patient,
                        "hopital": hopital,
                        "molecule": molecule,
                        "date_fin": date_fin,
                        "statut": "VALIDÉE",
                        "ordonnance_valide": True,
                    }
                )
                del st.session_state["temp_ordonnance"]
                st.success("Ordonnance enregistrée avec succès !")
                st.rerun()
    else:
        st.info("Aucune ordonnance en attente de validation.")

# ==============================================================================
# MENU 3 : PLANNING DE ROULEMENT
# ==============================================================================
elif menu == "3. Planning de Roulement":
    st.title("🗓️ Planning de Roulement & Renouvellements")

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

    # Modale 1 : Demande de renouvellement par Email
    @st.dialog("📩 Fiche de renouvellement par Email")
    def ouvrir_dialogue_renouvellement(o, jours_restants, key_cmd):
        st.markdown(f"### Patient : **{o['patient']}**")
        st.write(f"**Établissement / Praticien :** {o['hopital']}")
        st.write(f"**Traitement à renouveler :** {o['molecule']}")
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
                "⚠️ Aucune adresse e-mail renseignée pour cet établissement dans l'annuaire."
            )
            st.info(
                "Rendez-vous dans le menu **'5. Annuaire Établissements'** pour ajouter son e-mail."
            )

    # Modale 2 : Dépôt du fichier de reconduction
    @st.dialog("📁 Nouvelle ordonnance - reconduction")
    def ouvrir_dialogue_reconduction(o):
        st.markdown(f"### Reconduction pour : **{o['patient']}**")
        st.write(f"**Traitement :** {o['molecule']}")
        st.write(f"**Établissement :** {o['hopital']}")

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

            st.session_state["temp_ordonnance"] = {
                "image": fichier_nouveau,
                "data": donnees,
            }
            st.success("Nouvelle ordonnance chargée avec succès !")
            st.info(
                "Rendez-vous dans le menu **'2. Validation Pro'** pour valider la reconduction."
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
                            📅 Fin tt: <strong>{o['date_fin'].strftime('%d/%m/%Y')}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "📩 Renouveler auprès établissement de santé",
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

# ==============================================================================
# MENU 4 : LISTE DES ORDONNANCES
# ==============================================================================
elif menu == "4. Liste des Ordonnances":
    st.title("📋 Liste des Ordonnances")
    if st.session_state.ordonnances:
        df_ord = pd.DataFrame(st.session_state.ordonnances)
        st.dataframe(df_ord, use_container_width=True)
    else:
        st.info("Aucune ordonnance enregistrée.")

# ==============================================================================
# MENU 5 : ANNUAIRE ÉTABLISSEMENTS
# ==============================================================================
elif menu == "5. Annuaire Établissements":
    st.title("🏥 Annuaire des Établissements de Santé")

    with st.form("ajouter_hopital"):
        st.subheader("Ajouter un nouvel établissement")
        nom = st.text_input("Nom de l'établissement")
        email = st.text_input("Adresse e-mail")
        submit = st.form_submit_button("Ajouter")

        if submit and nom and email:
            st.session_state.hopitaux_db.append({"nom": nom, "email": email})
            st.success(f"Établissement {nom} ajouté !")
            st.rerun()

    st.subheader("Liste des établissements enregistrés")
    df_hopitaux = pd.DataFrame(st.session_state.hopitaux_db)
    st.dataframe(df_hopitaux, use_container_width=True)
