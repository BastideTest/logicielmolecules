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
def supprimer_ligne(index):
    """Supprime une ligne spécifique de la liste des ordonnances."""
    st.session_state.ordonnances.pop(index)
    st.toast("Ligne supprimée avec succès !", icon="🗑️")


def extraire_texte(fichier_image):
    """Ouvre l'image avec PIL et extrait le texte via Tesseract."""
    img = Image.open(fichier_image)
    texte = pytesseract.image_to_string(img, lang="fra")
    return texte, img


def analyser_traitements(texte, date_debut_defaut):
    """Détecte chaque médicament et lui attribue SA PROPRE durée, fréquence, prise et date de fin."""
    traitements = []
    lignes = [l.strip() for l in texte.split("\n") if l.strip()]

    for i, ligne in enumerate(lignes):
        m = re.search(
            r"([A-Z][a-zà-ÿA-Z]+(?:\s+[A-Z][a-zà-ÿ]+)?)\s+(\d+(?:[\.,]\d+)?\s*(?:mg|g|ml|ui))",
            ligne,
            re.IGNORECASE,
        )
        if m:
            nom_mol = f"{m.group(1)} {m.group(2)}"
            frequence = "1x / jour"
            prise = "Pendant le repas"
            duree_jours = 30

            contexte = (
                (ligne + " " + " ".join(lignes[i + 1 : i + 3]))
                if i + 1 < len(lignes)
                else ligne
            ).lower()

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

            if "1 mois" in contexte or "un mois" in contexte:
                duree_jours = 30
            elif "2 mois" in contexte:
                duree_jours = 60
            elif "3 mois" in contexte:
                duree_jours = 90
            else:
                m_duree = re.search(r"(\d+)\s*(?:jours|j)", contexte)
                if m_duree:
                    duree_jours = int(m_duree.group(1))

            traitements.append(
                {
                    "molecule": nom_mol,
                    "frequence": frequence,
                    "prise": prise,
                    "duree": duree_jours,
                }
            )

    if not traitements:
        traitements.append(
            {
                "molecule": "",
                "frequence": "1x / jour",
                "prise": "Soir",
                "duree": 30,
            }
        )

    return traitements


def parser_texte(texte):
    """Extraction globale du document."""
    donnees = {
        "patient": "",
        "hopital": "",
        "date_debut": datetime.today().date(),
        "traitements": [],
    }

    m_doc = re.search(
        r"((?:Docteur|Dr|Hôpital|Hopital|Clinique|CH)\s+[A-Za-zÀ-ÿ\s]+)",
        texte,
        re.IGNORECASE,
    )
    if m_doc:
        donnees["hopital"] = m_doc.group(1).split("\n")[0].strip()

    m_patient = re.search(
        r"([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)(?:,\s*\d+\s*ans)?", texte
    )
    if m_patient:
        nom = m_patient.group(1).strip()
        if "Docteur" not in nom and "Dr" not in nom:
            donnees["patient"] = nom

    donnees["traitements"] = analyser_traitements(texte, donnees["date_debut"])
    return donnees


# --- FRONTEND STREAMLIT ---
st.title("💊 Centre Médical - Suivi & Récapitulatif des Ordonnances")

menu = st.sidebar.radio(
    "Navigation",
    [
        "1. Nouvelle Ordonnance",
        "2. Validation Pro",
        "3. Tableau de Bord & Alertes",
        "4. Dossier Patient & Hôpital",
    ],
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
            st.subheader("Informations Générales")
            d = st.session_state["temp_ordonnance"]["data"]

            patient = st.text_input("Nom du Patient", value=d["patient"])
            hopital = st.text_input("Hôpital / Praticien", value=d["hopital"])
            date_debut = st.date_input(
                "Date de début de traitement", value=d["date_debut"]
            )

            st.divider()
            st.subheader("Détail par Médicament")

            traitements_saisis = []

            for idx, trait in enumerate(d["traitements"]):
                st.markdown(f"### 💊 Médicament n°{idx+1}")

                c1, c2 = st.columns([2, 1])
                with c1:
                    mol = st.text_input(
                        "Molécule & Dosage",
                        value=trait["molecule"],
                        key=f"mol_{idx}",
                    )
                with c2:
                    duree = st.number_input(
                        "Durée (jours)",
                        value=int(trait["duree"]),
                        min_value=1,
                        key=f"duree_{idx}",
                    )

                c3, c4 = st.columns([1, 1])
                with c3:
                    freq = st.text_input(
                        "Fréquence",
                        value=trait["frequence"],
                        key=f"freq_{idx}",
                    )
                with c4:
                    prise = st.text_input(
                        "Moment de Prise",
                        value=trait["prise"],
                        key=f"prise_{idx}",
                    )

                date_fin_mol = date_debut + timedelta(days=int(duree))
                st.info(
                    f"📅 **Fin de ce traitement : {date_fin_mol.strftime('%d/%m/%Y')}**"
                )

                traitements_saisis.append(
                    {
                        "molecule": mol,
                        "frequence": freq,
                        "prise": prise,
                        "duree": duree,
                        "date_fin": date_fin_mol,
                    }
                )
                st.markdown("---")

            col_val, col_rej = st.columns(2)

            with col_val:
                if st.button("✅ Valider l'ordonnance", use_container_width=True):
                    for t in traitements_saisis:
                        st.session_state.ordonnances.append(
                            {
                                "patient": patient,
                                "hopital": hopital,
                                "molecule": t["molecule"],
                                "frequence": t["frequence"],
                                "prise": t["prise"],
                                "date_debut": date_debut,
                                "duree": t["duree"],
                                "date_fin": t["date_fin"],
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
                        for t in traitements_saisis:
                            st.session_state.ordonnances.append(
                                {
                                    "patient": patient,
                                    "hopital": hopital,
                                    "molecule": t["molecule"],
                                    "frequence": t["frequence"],
                                    "prise": t["prise"],
                                    "date_debut": date_debut,
                                    "duree": t["duree"],
                                    "date_fin": t["date_fin"],
                                    "statut": "REJETÉE",
                                    "motif_rejet": motif,
                                }
                            )
                        del st.session_state["temp_ordonnance"]
                        st.warning("Ordonnance rejetée.")
                        st.rerun()

# -----------------------------------------------------------------------------
# 3. TABLEAU DE BORD AVEC SUPPRESSION
# -----------------------------------------------------------------------------
elif menu == "3. Tableau de Bord & Alertes":
    st.header("Tableau de Bord & Échéances des Commandes")

    if not st.session_state.ordonnances:
        st.info("Aucune ordonnance enregistrée.")
    else:
        aujourdhui = datetime.today().date()

        st.subheader("Légende des couleurs")
        st.markdown(
            "🔴 **Rouge** : ≤ 3 jours restants | 🟧 **Orange** : 4 à 7 jours restants | 🟩 **Vert** : > 7 jours restants | ⚪ **Gris** : Rejetée"
        )

        # Affichage sous forme de lignes interactives avec bouton de suppression
        for idx, row in enumerate(list(st.session_state.ordonnances)):
            jours_restants = (row["date_fin"] - aujourdhui).days

            # Choix du style de bordure/couleur
            if row["statut"] == "REJETÉE":
                couleur_fond = "#f0f0f0"
                badge = "⚪ REJETÉE"
            elif jours_restants <= 3:
                couleur_fond = "#ffcccc"
                badge = f"🔴 COMMANDE URGENTE ({jours_restants}j restants)"
            elif 4 <= jours_restants <= 7:
                couleur_fond = "#ffe6cc"
                badge = f"🟧 À PRÉVOIR ({jours_restants}j restants)"
            else:
                couleur_fond = "#e6ffe6"
                badge = f"🟩 EN COURS ({jours_restants}j restants)"

            # Card Container
            with st.container():
                col_info, col_del = st.columns([6, 1])

                with col_info:
                    st.markdown(
                        f"""
                        <div style="background-color: {couleur_fond}; padding: 12px; border-radius: 8px; margin-bottom: 5px; color: #111;">
                            <strong>Patient :</strong> {row['patient']} | <strong>Praticien :</strong> {row['hopital']}<br>
                            <strong>Médicament :</strong> {row['molecule']} ({row['prise']}) — {row['frequence']}<br>
                            <strong>Période :</strong> du {row['date_debut'].strftime('%d/%m/%Y')} au {row['date_fin'].strftime('%d/%m/%Y')} ({row['duree']} jours)<br>
                            <em>{badge}</em>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_del:
                    if st.button("🗑️ Supprimer", key=f"del_board_{idx}"):
                        supprimer_ligne(idx)
                        st.rerun()

# -----------------------------------------------------------------------------
# 4. DOSSIER PATIENT & HÔPITAL (AVEC SUPPRESSION)
# -----------------------------------------------------------------------------
elif menu == "4. Dossier Patient & Hôpital":
    st.header("🔍 Recherche & Dossiers Médicaux")

    if not st.session_state.ordonnances:
        st.info("Aucune donnée enregistrée pour le moment.")
    else:
        df = pd.DataFrame(st.session_state.ordonnances)
        tab1, tab2 = st.tabs(["📁 Dossier par Patient", "🏥 Recherche par Hôpital"])

        # TAB 1 : RECHERCHE PAR PATIENT
        with tab1:
            patients_liste = sorted(list(df["patient"].unique()))
            patient_sel = st.selectbox("Sélectionnez un patient :", patients_liste)

            if patient_sel:
                st.subheader(f"Dossier Médical de : {patient_sel}")

                # Bouton de suppression globale du patient
                if st.button(
                    f"⚠️ Supprimer TOUT le dossier de {patient_sel}",
                    type="primary",
                ):
                    st.session_state.ordonnances = [
                        o
                        for o in st.session_state.ordonnances
                        if o["patient"] != patient_sel
                    ]
                    st.success(f"Dossier de {patient_sel} supprimé.")
                    st.rerun()

                st.markdown("---")

                # Affichage des lignes individuelles du patient avec suppression
                for idx, row in enumerate(list(st.session_state.ordonnances)):
                    if row["patient"] == patient_sel:
                        c_txt, c_btn = st.columns([5, 1])
                        with c_txt:
                            st.write(
                                f"💊 **{row['molecule']}** — {row['prise']} (Fin : {row['date_fin'].strftime('%d/%m/%Y')}) - *{row['statut']}*"
                            )
                        with c_btn:
                            if st.button("🗑️ Supprimer", key=f"del_pat_{idx}"):
                                supprimer_ligne(idx)
                                st.rerun()

        # TAB 2 : RECHERCHE PAR HÔPITAL
        with tab2:
            hopitaux_liste = sorted(list(df["hopital"].unique()))
            hopital_sel = st.selectbox(
                "Sélectionnez un Établissement / Praticien :", hopitaux_liste
            )

            if hopital_sel:
                st.subheader(f"Prescriptions issues de : {hopital_sel}")

                for idx, row in enumerate(list(st.session_state.ordonnances)):
                    if row["hopital"] == hopital_sel:
                        c_txt, c_btn = st.columns([5, 1])
                        with c_txt:
                            st.write(
                                f"👤 **{row['patient']}** ➔ {row['molecule']} ({row['prise']}) - Fin : {row['date_fin'].strftime('%d/%m/%Y')}"
                            )
                        with c_btn:
                            if st.button("🗑️ Supprimer", key=f"del_hop_{idx}"):
                                supprimer_ligne(idx)
                                st.rerun()
