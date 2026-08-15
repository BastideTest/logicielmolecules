from datetime import datetime, timedelta
import re
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st

# --- CONFIGURATION DE LA PAGE STREAMLIT ---
st.set_page_config(
    page_title="Gestionnaire d'Ordonnances", page_icon="💊", layout="wide"
)

# --- INITIALISATION DE LA BASE DE DONNÉES EN MÉMOIRE ---
if "ordonnances" not in st.session_state:
    st.session_state.ordonnances = []


# --- FONCTIONS DE TRAITEMENT (BACKEND) ---
def extraire_texte(fichier_image):
    """Ouvre l'image avec PIL et extrait le texte via Tesseract."""
    img = Image.open(fichier_image)
    texte = pytesseract.image_to_string(img, lang="fra")
    return texte, img


def parser_texte(texte):
    """Extraction intelligente adaptée aux formats d'ordonnance complexes."""
    donnees = {
        "patient": "",
        "hopital": "",
        "molecule": "",
        "date_debut": datetime.today().date(),
        "frequence": 1,
        "duree": 30,  # 1 mois par défaut en milieu médical
    }

    # 1. Extraction du Médecin / Établissement
    m_doc = re.search(
        r"((?:Docteur|Dr|Hôpital|Hopital|Clinique|CH)\s+[A-Za-zÀ-ÿ\s]+)",
        texte,
        re.IGNORECASE,
    )
    if m_doc:
        donnees["hopital"] = m_doc.group(1).split("\n")[0].strip()

    # 2. Extraction du Patient (Cherche les lignes avec prénom/nom + âge ou structure isolée)
    m_patient = re.search(
        r"([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)(?:,\s*\d+\s*ans)?", texte
    )
    if m_patient:
        nom_trouve = m_patient.group(1).strip()
        # Évite de confondre le nom du médecin avec celui du patient
        if "Docteur" not in nom_trouve and "Dr" not in nom_trouve:
            donnees["patient"] = nom_trouve

    # 3. Extraction de toutes les Molécules et Dosages (ex: Zolpidem 10 mg / Alprazolam 0,25 mg)
    m_molecules = re.findall(
        r"([A-Z][a-zà-ÿ]+\s+\d+(?:[\.,]\d+)?\s*(?:mg|g|ml))", texte
    )
    if m_molecules:
        donnees["molecule"] = " + ".join(m_molecules)

    # 4. Conversion des Durées (Gestion de "1 mois", "2 mois", ou "X jours")
    texte_lower = texte.lower()
    if "1 mois" in texte_lower or "un mois" in texte_lower:
        donnees["duree"] = 30
    elif "2 mois" in texte_lower:
        donnees["duree"] = 60
    elif "3 mois" in texte_lower:
        donnees["duree"] = 90
    else:
        m_duree = re.search(r"pendant\s+(\d+)\s*jours", texte_lower)
        if m_duree:
            donnees["duree"] = int(m_duree.group(1))

    # 5. Calcul de la Fréquence
    if "matin" in texte_lower and "midi" in texte_lower and "soir" in texte_lower:
        donnees["frequence"] = 3
    elif "matin" in texte_lower and "soir" in texte_lower:
        donnees["frequence"] = 2
    elif "soir" in texte_lower or "matin" in texte_lower:
        donnees["frequence"] = 1

    return donnees


# --- INTERFACE GRAPHIQUE (FRONTEND) ---
st.title("💊 Centre Médical - Suivi & Récapitulatif des Ordonnances")

# Menu de Navigation
menu = st.sidebar.radio(
    "Navigation",
    ["1. Nouvelle Ordonnance", "2. Validation Pro", "3. Tableau de Bord & Alertes"],
)

# -----------------------------------------------------------------------------
# ONGLET 1 : UPLOAD D'ORDONNANCE
# -----------------------------------------------------------------------------
if menu == "1. Nouvelle Ordonnance":
    st.header("Upload de l'ordonnance")
    fichier = st.file_uploader(
        "Déposez l'ordonnance scannée (PNG, JPG)", type=["png", "jpg", "jpeg"]
    )

    if fichier is not None:
        texte_extrait, img = extraire_texte(fichier)
        donnees_preremplies = parser_texte(texte_extrait)

        # Sauvegarde temporaire pour la relecture
        st.session_state["temp_ordonnance"] = {
            "image": fichier,
            "data": donnees_preremplies,
        }
        st.success(
            "Ordonnance lue avec succès ! Rendez-vous dans l'onglet '2. Validation Pro'."
        )

# -----------------------------------------------------------------------------
# ONGLET 2 : RELECTURE ET VALIDATION PRO
# -----------------------------------------------------------------------------
elif menu == "2. Validation Pro":
    st.header("Relecture & Validation Professionnelle")

    if "temp_ordonnance" not in st.session_state:
        st.info("Aucune ordonnance en attente de relecture. Veuillez d'abord en téléverser une.")
    else:
        col_img, col_form = st.columns([1, 1])

        # Colonne de Gauche : Affichage de l'ordonnance
        with col_img:
            st.image(
                st.session_state["temp_ordonnance"]["image"],
                caption="Ordonnance originale",
                use_container_width=True,
            )

        # Colonne de Droite : Formulaire pré-rempli
        with col_form:
            st.subheader("Champs extraits")
            d = st.session_state["temp_ordonnance"]["data"]

            patient = st.text_input("Nom du Patient", value=d["patient"])
            hopital = st.text_input("Hôpital / Praticien", value=d["hopital"])
            molecule = st.text_input("Molécule & Dosage", value=d["molecule"])
            date_debut = st.date_input("Date de début", value=d["date_debut"])
            frequence = st.number_input(
                "Fréquence (par jour)", value=d["frequence"], min_value=1
            )
            duree = st.number_input(
                "Durée du traitement (jours)", value=d["duree"], min_value=1
            )

            date_fin = date_debut + timedelta(days=int(duree))
            st.info(f"Date de fin calculée : **{date_fin.strftime('%d/%m/%Y')}**")

            col_val, col_rej = st.columns(2)

            with col_val:
                if st.button("✅ Valider l'ordonnance", use_container_width=True):
                    st.session_state.ordonnances.append(
                        {
                            "patient": patient,
                            "hopital": hopital,
                            "molecule": molecule,
                            "date_debut": date_debut,
                            "frequence": frequence,
                            "duree": duree,
                            "date_fin": date_fin,
                            "statut": "VALIDÉE",
                            "motif_rejet": "",
                        }
                    )
                    del st.session_state["temp_ordonnance"]
                    st.success("Ordonnance validée et enregistrée !")
                    st.rerun()

            with col_rej:
                motif = st.text_input("Motif du rejet")
                if st.button("❌ Rejeter", use_container_width=True):
                    if not motif:
                        st.error("Veuillez saisir un motif de rejet.")
                    else:
                        st.session_state.ordonnances.append(
                            {
                                "patient": patient,
                                "hopital": hopital,
                                "molecule": molecule,
                                "date_debut": date_debut,
                                "frequence": frequence,
                                "duree": duree,
                                "date_fin": date_fin,
                                "statut": "REJETÉE",
                                "motif_rejet": motif,
                            }
                        )
                        del st.session_state["temp_ordonnance"]
                        st.warning("Ordonnance rejetée.")
                        st.rerun()

# -----------------------------------------------------------------------------
# ONGLET 3 : TABLEAU DE BORD ET ALERTES
# -----------------------------------------------------------------------------
elif menu == "3. Tableau de Bord & Alertes":
    st.header("Suivi du renouvellement & Alertes quotidiennes")

    if not st.session_state.ordonnances:
        st.write("Aucune donnée enregistrée pour le moment.")
    else:
        df = pd.DataFrame(st.session_state.ordonnances)
        aujourdhui = datetime.today().date()

        # Alertes de renouvellement
        st.subheader("🚨 Alertes de renouvellement (Échéance < 3 jours)")
        alertes = []

        for idx, row in df.iterrows():
            if row["statut"] == "VALIDÉE":
                jours_restants = (row["date_fin"] - aujourdhui).days
                if 0 <= jours_restants <= 3:
                    alertes.append(
                        f"⚠️ **{row['patient']}** ({row['hopital']}) : Recommander **{row['molecule']}** avant le {row['date_fin'].strftime('%d/%m/%Y')} (Reste {jours_restants} jours)."
                    )

        if alertes:
            for alerte in alertes:
                st.error(alerte)
        else:
            st.success("Aucun réapprovisionnement urgent requis aujourd'hui.")

        st.subheader("Toutes les ordonnances enregistrées")
        st.dataframe(df, use_container_width=True)
