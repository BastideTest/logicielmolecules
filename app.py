from datetime import datetime, timedelta
import re
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st

# --- CONFIGURATION PAGE ---
st.set_page_config(
    page_title="Gestionnaire d'Ordonnances", page_icon="💊", layout="wide"
)

# --- BASE DE DONNÉES EN MÉMOIRE ---
if "ordonnances" not in st.session_state:
    st.session_state.ordonnances = []


# --- FONCTIONS BACKEND ---
def extraire_texte(fichier_image):
    """Ouvre l'image avec PIL et extrait le texte via Tesseract."""
    img = Image.open(fichier_image)
    texte = pytesseract.image_to_string(img, lang="fra")
    return texte, img


def analyser_traitements(texte):
    """Détecte et détaille chaque molécule : Nom, Posologie, Fréquence et Prise."""
    traitements = []
    lignes = [l.strip() for l in texte.split("\n") if l.strip()]

    for i, ligne in enumerate(lignes):
        # Détection d'une molécule (ex: Zolpidem 10 mg, Alprazolam 0,25 mg)
        m = re.search(
            r"([A-Z][a-zà-ÿA-Z]+(?:\s+[A-Z][a-zà-ÿ]+)?)\s+(\d+(?:[\.,]\d+)?\s*(?:mg|g|ml|ui))",
            ligne,
            re.IGNORECASE,
        )
        if m:
            nom_mol = f"{m.group(1)} {m.group(2)}"
            frequence = "1x / jour"
            prise = "Pendant le repas"

            # Analyse du contexte sur la ligne suivante pour la prise / fréquence
            contexte = (
                (ligne + " " + lignes[i + 1])
                if i + 1 < len(lignes)
                else ligne
            ).lower()

            # Détection des moments de prise
            moments = []
            if "matin" in contexte:
                moments.append("Matin")
            if "midi" in contexte:
                moments.append("Midi")
            if "soir" in contexte or "coucher" in contexte:
                moments.append("Soir / Coucher")

            if moments:
                prise = " + ".join(moments)
                frequence = f"{len(moments)}x / jour"

            traitements.append(
                {"molecule": nom_mol, "frequence": frequence, "prise": prise}
            )

    return traitements


def parser_texte(texte):
    """Extraction globale du document."""
    donnees = {
        "patient": "",
        "hopital": "",
        "traitements": [],
        "date_debut": datetime.today().date(),
        "duree": 30,  # Default 30 jours (1 mois)
    }

    # 1. Médecin / Établissement
    m_doc = re.search(
        r"((?:Docteur|Dr|Hôpital|Hopital|Clinique|CH)\s+[A-Za-zÀ-ÿ\s]+)",
        texte,
        re.IGNORECASE,
    )
    if m_doc:
        donnees["hopital"] = m_doc.group(1).split("\n")[0].strip()

    # 2. Patient
    m_patient = re.search(
        r"([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)(?:,\s*\d+\s*ans)?", texte
    )
    if m_patient:
        nom = m_patient.group(1).strip()
        if "Docteur" not in nom and "Dr" not in nom:
            donnees["patient"] = nom

    # 3. Durée du traitement
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

    # 4. Extraction détaillée des molécules
    donnees["traitements"] = analyser_traitements(texte)

    return donnees


# --- FRONTEND STREAMLIT ---
st.title("💊 Centre Médical - Suivi & Récapitulatif des Ordonnances")

menu = st.sidebar.radio(
    "Navigation",
    ["1. Nouvelle Ordonnance", "2. Validation Pro", "3. Tableau de Bord & Alertes"],
)

# -----------------------------------------------------------------------------
# 1. UPLOAD
# -----------------------------------------------------------------------------
if menu == "1. Nouvelle Ordonnance":
    st.header("Upload de l'ordonnance")
    fichier = st.file_uploader(
        "Déposez l'ordonnance scannée (PNG, JPG)", type=["png", "jpg", "jpeg"]
    )

    if fichier is not None:
        texte_extrait, img = extraire_texte(fichier)
        donnees = parser_texte(texte_extrait)

        st.session_state["temp_ordonnance"] = {
            "image": fichier,
            "data": donnees,
        }
        st.success(
            "Ordonnance lue avec succès ! Rendez-vous dans l'onglet '2. Validation Pro'."
        )

# -----------------------------------------------------------------------------
# 2. VALIDATION PRO
# -----------------------------------------------------------------------------
elif menu == "2. Validation Pro":
    st.header("Relecture & Validation Professionnelle")

    if "temp_ordonnance" not in st.session_state:
        st.info("Aucune ordonnance en attente de relecture.")
    else:
        col_img, col_form = st.columns([1, 1])

        with col_img:
            st.image(
                st.session_state["temp_ordonnance"]["image"],
                caption="Ordonnance originale",
                use_container_width=True,
            )

        with col_form:
            st.subheader("Champs extraits")
            d = st.session_state["temp_ordonnance"]["data"]

            patient = st.text_input("Nom du Patient", value=d["patient"])
            hopital = st.text_input("Hôpital / Praticien", value=d["hopital"])

            # Calcul dynamique exact de la Date de fin
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                date_debut = st.date_input(
                    "Date de début", value=d["date_debut"]
                )
            with col_d2:
                duree = st.number_input(
                    "Durée (jours)", value=int(d["duree"]), min_value=1
                )

            date_fin_calculee = date_debut + timedelta(days=int(duree))
            st.success(
                f"📅 **Date de fin calculée : {date_fin_calculee.strftime('%d/%m/%Y')}**"
            )

            st.divider()
            st.subheader("Molécules & Posologies")

            traitements_saisis = []
            traitements_source = (
                d["traitements"]
                if d["traitements"]
                else [{"molecule": "", "frequence": "1x / jour", "prise": "Soir"}]
            )

            # Affichage dynamique des molécules (1 ou plusieurs)
            for idx, trait in enumerate(traitements_source):
                st.markdown(f"**Médicament n°{idx+1}**")
                c1, c2, c3 = st.columns([2, 1, 1])

                with c1:
                    mol = st.text_input(
                        f"Molécule & Dosage",
                        value=trait["molecule"],
                        key=f"mol_{idx}",
                    )
                with c2:
                    freq = st.text_input(
                        f"Fréquence", value=trait["frequence"], key=f"freq_{idx}"
                    )
                with c3:
                    prise = st.text_input(
                        f"Moment de Prise",
                        value=trait["prise"],
                        key=f"prise_{idx}",
                    )

                traitements_saisis.append(
                    {"molecule": mol, "frequence": freq, "prise": prise}
                )

            st.divider()
            col_val, col_rej = st.columns(2)

            with col_val:
                if st.button("✅ Valider l'ordonnance", use_container_width=True):
                    st.session_state.ordonnances.append(
                        {
                            "patient": patient,
                            "hopital": hopital,
                            "traitements": traitements_saisis,
                            "date_debut": date_debut,
                            "duree": duree,
                            "date_fin": date_fin_calculee,
                            "statut": "VALIDÉE",
                            "motif_rejet": "",
                        }
                    )
                    del st.session_state["temp_ordonnance"]
                    st.success("Ordonnance enregistrée !")
                    st.rerun()

            with col_rej:
                motif = st.text_input("Motif du rejet")
                if st.button("❌ Rejeter", use_container_width=True):
                    if not motif:
                        st.error("Saisissez un motif de rejet.")
                    else:
                        st.session_state.ordonnances.append(
                            {
                                "patient": patient,
                                "hopital": hopital,
                                "traitements": traitements_saisis,
                                "date_debut": date_debut,
                                "duree": duree,
                                "date_fin": date_fin_calculee,
                                "statut": "REJETÉE",
                                "motif_rejet": motif,
                            }
                        )
                        del st.session_state["temp_ordonnance"]
                        st.warning("Ordonnance rejetée.")
                        st.rerun()

# -----------------------------------------------------------------------------
# 3. TABLEAU DE BORD
# -----------------------------------------------------------------------------
elif menu == "3. Tableau de Bord & Alertes":
    st.header("Suivi du renouvellement & Alertes")

    if not st.session_state.ordonnances:
        st.info("Aucune ordonnance enregistrée.")
    else:
        df = pd.DataFrame(st.session_state.ordonnances)
        st.dataframe(df, use_container_width=True)
