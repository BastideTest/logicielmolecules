from datetime import datetime, timedelta
import re
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gestionnaire d'Ordonnances", page_icon="💊", layout="wide"
)


def extraire_texte(image_file):
    """Ouvre l'image avec PIL et extrait le texte via Tesseract."""
    img = Image.open(image_file)
    texte = pytesseract.image_to_string(img, lang="fra")
    return texte, img

# --- INITIALISATION DE LA BASE DE DONNÉES EN MÉMOIRE ---
if "ordonnances" not in st.session_state:
    st.session_state.ordonnances = []


# --- FONCTIONS TECHNIQUES (BACKEND) ---
def extraire_texte(image_bytes):
    """Convertit l'image envoyée via l'interface web en texte."""
    file_bytes = np.asarray(bytearray(image_bytes.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    return pytesseract.image_to_string(thresh, lang="fra"), img


def parser_texte(texte):
    """Extrait automatiquement les champs grâce aux règles Regex."""
    donnees = {
        "patient": "",
        "hopital": "",
        "molecule": "",
        "date_debut": datetime.today().date(),
        "frequence": 1,
        "duree": 7,
    }

    # Extraction du Nom du Patient
    m_patient = re.search(
        r"(?:Patient|Nom)\s*:\s*([A-Za-ZÀ-ÿ\s]+)", texte, re.IGNORECASE
    )
    if m_patient:
        donnees["patient"] = m_patient.group(1).strip()

    # Extraction de l'Hôpital
    m_hopital = re.search(
        r"((?:Hôpital|Hopital|Clinique|CH)\s+[A-Za-ZÀ-ÿ\s]+)",
        texte,
        re.IGNORECASE,
    )
    if m_hopital:
        donnees["hopital"] = m_hopital.group(1).strip()

    # Extraction de la Molécule
    m_molecule = re.search(r"([A-Z][a-zà-ÿ]+)\s+(\d+\s*(?:mg|g|ml))", texte)
    if m_molecule:
        donnees["molecule"] = f"{m_molecule.group(1)} {m_molecule.group(2)}"

    # Extraction de la Fréquence
    m_freq = re.search(
        r"(\d+)\s*(?:fois par jour|/jour|par jour)", texte, re.IGNORECASE
    )
    if m_freq:
        donnees["frequence"] = int(m_freq.group(1))

    # Extraction de la Durée
    m_duree = re.search(r"pendant\s+(\d+)\s*jours", texte, re.IGNORECASE)
    if m_duree:
        donnees["duree"] = int(m_duree.group(1))

    return donnees


# --- INTERFACE GRAPHIQUE (FRONTEND) ---
st.title("💊 Centre Médical - Suivi & Récapitulatif des Ordonnances")

# Menu Navigation
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
        import numpy as np

        texte_extrait, img_cv = extraire_texte(fichier)
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
        st.info("Acuune ordonnance en attente de relecture. Veuillez d'abord en téléverser une.")
    else:
        col_img, col_form = st.columns([1, 1])

        # Colonne de Gauche : Affichage de l'ordonnance
        with col_img:
            st.image(
                st.session_state["temp_ordonnance"]["image"],
                caption="Ordonnance originale",
                use_column_width=True,
            )

        # Colonne de Droite : Formulaire pré-rempli
        with col_form:
            st.subheader("Champs extraits")
            d = st.session_state["temp_ordonnance"]["data"]

            patient = st.text_input("Nom du Patient", value=d["patient"])
            hopital = st.text_input("Hôpital / Centre", value=d["hopital"])
            molecule = st.text_input("Molécule & Dosage", value=d["molecule"])
            date_debut = st.date_input("Date de début", value=d["date_debut"])
            frequence = st.number_input(
                "Fréquence (par jour)", value=d["frequence"], min_value=1
            )
            duree = st.number_input(
                "Durée du traitement (jours)", value=d["duree"], min_value=1
            )

            date_fin = date_debut + timedelta(days=duree)
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
        st.write("Acuune donnée enregistrée pour le moment.")
    else:
        df = pd.DataFrame(st.session_state.ordonnances)
        aujourdhui = datetime.today().date()

        # Filtrer les alertes
        st.subheader("🚨 Alertes de renouvellement (Échéance < 3 jours)")
        alertes = []

        for idx, row in df.iterrows():
            if row["statut"] == "VALIDÉE":
                jours_restants = (row["date_fin"] - aujourdhui).days
                if 0 <= jours_restants <= 3:
                    alertes.append(
                        f"⚠️ **{row['patient']}** ({row['hopital']}) : Récommander la molécule **{row['molecule']}** avant le {row['date_fin'].strftime('%d/%m/%Y')} (Reste {jours_restants} jours)."
                    )

        if alertes:
            for alerte in alertes:
                st.error(alerte)
        else:
            st.success("Aucun réapprovisionnement urgent requis aujourd'hui.")

        st.subheader("Toutes les ordonnances enregistrées")
        st.dataframe(df, use_container_width=True)
