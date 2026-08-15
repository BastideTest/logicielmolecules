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

# --- CONFIGURATION PAGE ---
st.set_page_config(
    page_title="Gestionnaire d'Ordonnances - Bastide",
    page_icon="🔒",
    layout="wide",
)

# --- CHEMINS DES FICHIERS EN LOCAL / RÉSEAU ---
CHEMIN_ORDONNANCES = r"C:\Users\Public\Documents\bastide\ordonnances_db.json"
CHEMIN_HOPITAUX = r"C:\Users\Public\Documents\bastide\hopitaux_db.json"

# --- COMPTES UTILISATEURS AUTORISÉS ---
COMPTES = {
    "Bastideadmin": hashlib.sha256("moleculesbastide".encode()).hexdigest(),
}


# --- FONCTIONS DE GESTION DES DONNÉES ---
def charger_hopitaux():
    """Charge la liste des hôpitaux et leurs coordonnées."""
    if os.path.exists(CHEMIN_HOPITAUX):
        try:
            with open(CHEMIN_HOPITAUX, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur lors de la lecture des hôpitaux : {e}")
            return []
    return []


def sauvegarder_hopitaux():
    """Sauvegarde les hôpitaux dans le fichier JSON."""
    try:
        dossier_parent = os.path.dirname(CHEMIN_HOPITAUX)
        if dossier_parent and not os.path.exists(dossier_parent):
            os.makedirs(dossier_parent, exist_ok=True)
        with open(CHEMIN_HOPITAUX, "w", encoding="utf-8") as f:
            json.dump(
                st.session_state.hopitaux_db, f, ensure_ascii=False, indent=4
            )
    except Exception as e:
        st.error(f"Erreur d'écriture sur les hôpitaux : {e}")


def charger_ordonnances():
    """Charge les ordonnances depuis le fichier JSON."""
    if os.path.exists(CHEMIN_ORDONNANCES):
        try:
            with open(CHEMIN_ORDONNANCES, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    item["date_debut"] = datetime.strptime(
                        item["date_debut"], "%Y-%m-%d"
                    ).date()
                    item["date_fin"] = datetime.strptime(
                        item["date_fin"], "%Y-%m-%d"
                    ).date()
                return data
        except Exception as e:
            st.error(f"Erreur lors de la lecture des ordonnances : {e}")
            return []
    return []


def sauvegarder_ordonnances():
    """Sauvegarde les ordonnances."""
    try:
        donnees_a_sauver = []
        for item in st.session_state.ordonnances:
            item_copy = item.copy()
            if isinstance(item_copy["date_debut"], (datetime, datetime.date)):
                item_copy["date_debut"] = item_copy["date_debut"].strftime(
                    "%Y-%m-%d"
                )
            if isinstance(item_copy["date_fin"], (datetime, datetime.date)):
                item_copy["date_fin"] = item_copy["date_fin"].strftime(
                    "%Y-%m-%d"
                )
            donnees_a_sauver.append(item_copy)

        dossier_parent = os.path.dirname(CHEMIN_ORDONNANCES)
        if dossier_parent and not os.path.exists(dossier_parent):
            os.makedirs(dossier_parent, exist_ok=True)

        with open(CHEMIN_ORDONNANCES, "w", encoding="utf-8") as f:
            json.dump(donnees_a_sauver, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erreur d'écriture sur le disque : {e}")


def supprimer_ligne(index):
    """Supprime un traitement et synchronise la base de données."""
    st.session_state.ordonnances.pop(index)
    sauvegarder_ordonnances()
    st.toast("Ligne supprimée avec succès !", icon="🗑️")


def generer_lien_mailto(
    destinataire_email, nom_hopital, patient, molecule, jours_restants, date_fin
):
    """Génère une URL mailto: pour ouvrir Outlook avec un brouillon pré-rempli."""
    sujet = f"URGENT : Renouvellement d'ordonnance - Patient : {patient}"
    corps = f"""Bonjour,

Nous vous contactons concernant le traitement du patient {patient}, suivi au sein de votre établissement ({nom_hopital}).

Le traitement suivant arrive à échéance :
- Traitement : {molecule}
- Date de fin de traitement : {date_fin.strftime('%d/%m/%Y')}
- Jours restants : {jours_restants} jour(s)

Merci de bien vouloir nous faire parvenir la nouvelle ordonnance renouvelée dans les plus brefs délais afin d'éviter toute rupture de traitement.

Cordialement,
L'équipe médicale - Bastide
"""
    sujet_encode = urllib.parse.quote(sujet)
    corps_encode = urllib.parse.quote(corps)
    return f"mailto:{destinataire_email}?subject={sujet_encode}&body={corps_encode}"


# --- MODULE D'AUTHENTIFICATION ---
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
if "utilisateur" not in st.session_state:
    st.session_state.utilisateur = ""


def verifier_identifiants(utilisateur, mot_de_passe):
    """Vérifie le hash SHA-256 du mot de passe saisi."""
    hash_mp = hashlib.sha256(mot_de_passe.encode()).hexdigest()
    if utilisateur in COMPTES and COMPTES[utilisateur] == hash_mp:
        st.session_state.authentifie = True
        st.session_state.utilisateur = utilisateur
        st.session_state.ordonnances = charger_ordonnances()
        st.session_state.hopitaux_db = charger_hopitaux()
        st.rerun()
    else:
        st.error("Identifiant ou mot de passe incorrect.")


def deconnexion():
    """Réinitialise la session utilisateur."""
    st.session_state.authentifie = False
    st.session_state.utilisateur = ""
    st.session_state.ordonnances = []
    st.session_state.hopitaux_db = []
    st.rerun()


# -----------------------------------------------------------------------------
# ÉCRAN DE LOGIN
# -----------------------------------------------------------------------------
if not st.session_state.authentifie:
    st.title("🔒 Connexion au Système Médical Bastide")
    st.subheader("Accès restreint aux professionnels de santé autorisés")

    col_box, _ = st.columns([1, 1])
    with col_box:
        with st.form("form_login"):
            user_input = st.text_input("Identifiant")
            pass_input = st.text_input("Mot de passe", type="password")
            submit_btn = st.form_submit_button(
                "Se connecter", use_container_width=True
            )

            if submit_btn:
                verifier_identifiants(user_input, pass_input)

    st.stop()

# -----------------------------------------------------------------------------
# APPLICATION PRINCIPALE
# -----------------------------------------------------------------------------

if "hopitaux_db" not in st.session_state:
    st.session_state.hopitaux_db = charger_hopitaux()
if "ordonnances" not in st.session_state:
    st.session_state.ordonnances = charger_ordonnances()

st.sidebar.write(f"👤 Connecté en tant que : **{st.session_state.utilisateur}**")
if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    deconnexion()

st.sidebar.divider()


def extraire_texte(fichier_image):
    img = Image.open(fichier_image)
    texte = pytesseract.image_to_string(img, lang="fra")
    return texte, img


def analyser_traitements(texte, date_debut_defaut):
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


st.title("💊 Centre Médical - Suivi des Ordonnances")

menu = st.sidebar.radio(
    "Navigation",
    [
        "1. Nouvelle Ordonnance",
        "2. Validation Pro",
        "3. Tableau de Bord & Alertes",
        "4. Gestion Établissements & Dossiers",
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

            # --- SELECTION DU PATIENT (EXISTANT OU NOUVEAU) ---
            patients_existants = sorted(
                list(
                    set([o["patient"] for o in st.session_state.ordonnances])
                )
            )
            type_patient = st.radio(
                "Choix du Patient :",
                ["Patient Existant", "Nouveau Patient"],
                horizontal=True,
            )

            if type_patient == "Patient Existant" and patients_existants:
                patient_selectionne = st.selectbox(
                    "Sélectionnez le Patient :", patients_existants
                )
            else:
                patient_selectionne = st.text_input(
                    "Nom et Prénom du Patient", value=d["patient"]
                )

            st.markdown("---")

            # --- SELECTION DE L'ÉTABLISSEMENT (EXISTANT OU NOUVEAU) ---
            hopitaux_existants = sorted(
                [h["nom"] for h in st.session_state.hopitaux_db]
            )
            type_hopital = st.radio(
                "Choix de l'Établissement :",
                ["Établissement Annuaire", "Autre / Nouveau"],
                horizontal=True,
            )

            if type_hopital == "Établissement Annuaire" and hopitaux_existants:
                idx_defaut = 0
                if d["hopital"] in hopitaux_existants:
                    idx_defaut = hopitaux_existants.index(d["hopital"])
                hopital_selectionne = st.selectbox(
                    "Sélectionnez l'Établissement :",
                    hopitaux_existants,
                    index=idx_defaut,
                )
            else:
                hopital_selectionne = st.text_input(
                    "Nom de l'Établissement / Praticien", value=d["hopital"]
                )

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
                                "patient": patient_selectionne,
                                "hopital": hopital_selectionne,
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
                    sauvegarder_ordonnances()
                    del st.session_state["temp_ordonnance"]
                    st.success("Ordonnance enregistrée avec succès !")
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
                                    "patient": patient_selectionne,
                                    "hopital": hopital_selectionne,
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
                        sauvegarder_ordonnances()
                        del st.session_state["temp_ordonnance"]
                        st.warning("Ordonnance rejetée et enregistrée.")
                        st.rerun()

# -----------------------------------------------------------------------------
# 3. TABLEAU DE BORD & ALERTES (SELECTION RECHERCHABLE POUR ÉTABLISSEMENT)
# -----------------------------------------------------------------------------
elif menu == "3. Tableau de Bord & Alertes":
    st.header("Tableau de Bord & Échéances des Commandes")

    if not st.session_state.ordonnances:
        st.info("Aucune ordonnance enregistrée dans le système.")
    else:
        aujourdhui = datetime.today().date()

        st.subheader("Légende des couleurs")
        st.markdown(
            "🔴 **Rouge** : ≤ 3 jours restants | 🟧 **Orange** : 4 à 7 jours restants | 🟩 **Vert** : > 7 jours restants | ⚪ **Gris** : Rejetée"
        )

        map_hopitaux_email = {
            h["nom"]: h.get("email", "") for h in st.session_state.hopitaux_db
        }

        for idx, row in enumerate(list(st.session_state.ordonnances)):
            jours_restants = (row["date_fin"] - aujourdhui).days

            if row["statut"] == "REJETÉE":
                couleur_fond = "#f0f0f0"
                badge = "⚪ REJETÉE"
                alerte_urgente = False
            elif jours_restants <= 3:
                couleur_fond = "#ffcccc"
                badge = f"🔴 COMMANDE URGENTE ({jours_restants}j restants)"
                alerte_urgente = True
            elif 4 <= jours_restants <= 7:
                couleur_fond = "#ffe6cc"
                badge = f"🟧 À PRÉVOIR ({jours_restants}j restants)"
                alerte_urgente = True
            else:
                couleur_fond = "#e6ffe6"
                badge = f"🟩 EN COURS ({jours_restants}j restants)"
                alerte_urgente = False

            with st.container():
                col_info, col_actions = st.columns([4, 2])

                with col_info:
                    st.markdown(
                        f"""
                        <div style="background-color: {couleur_fond}; padding: 12px; border-radius: 8px; margin-bottom: 5px; color: #111;">
                            <strong>Patient :</strong> {row['patient']} | <strong>Établissement :</strong> {row['hopital']}<br>
                            <strong>Médicament :</strong> {row['molecule']} ({row['prise']}) — {row['frequence']}<br>
                            <strong>Période :</strong> du {row['date_debut'].strftime('%d/%m/%Y')} au {row['date_fin'].strftime('%d/%m/%Y')} ({row['duree']} jours)<br>
                            <em>{badge}</em>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_actions:
                    col_btn_del, col_btn_email = st.columns([1, 2])

                    with col_btn_del:
                        if st.button("🗑️ Supprimer", key=f"del_board_{idx}"):
                            supprimer_ligne(idx)
                            st.rerun()

                    with col_btn_email:
                        if alerte_urgente:
                            email_dest = map_hopitaux_email.get(
                                row["hopital"], ""
                            )
                            if email_dest:
                                mailto_url = generer_lien_mailto(
                                    email_dest,
                                    row["hopital"],
                                    row["patient"],
                                    row["molecule"],
                                    jours_restants,
                                    row["date_fin"],
                                )
                                st.link_button(
                                    "📧 Recommander (Outlook)",
                                    mailto_url,
                                    use_container_width=True,
                                )
                            else:
                                st.warning("⚠️ Email non renseigné")

                # --- PANNEAU DE MODIFICATION DE L'ORDONNANCE ---
                with st.expander(
                    f"✏️ Modifier l'ordonnance de {row['patient']} ({row['molecule']})"
                ):
                    with st.form(key=f"form_edit_{idx}"):
                        mod_patient = st.text_input(
                            "Nom du Patient", value=row["patient"]
                        )

                        # LISTE DYNAMIQUE DES ÉTABLISSEMENTS POUR LA RECHERCHE (SELECTBOX)
                        liste_hopitaux = sorted(
                            list(
                                set(
                                    [
                                        h["nom"]
                                        for h in st.session_state.hopitaux_db
                                    ]
                                )
                            )
                        )

                        # Si l'hôpital actuel n'est pas encore dans l'annuaire, on l'ajoute provisoirement à la liste de choix
                        if (
                            row["hopital"]
                            and row["hopital"] not in liste_hopitaux
                        ):
                            liste_hopitaux.insert(0, row["hopital"])

                        # Recherche dynamique par saisie dans la selectbox
                        index_defaut = (
                            liste_hopitaux.index(row["hopital"])
                            if row["hopital"] in liste_hopitaux
                            else 0
                        )
                        mod_hopital = st.selectbox(
                            "Établissement / Praticien (Tapez pour filtrer)",
                            options=liste_hopitaux,
                            index=index_defaut,
                        )

                        mod_molecule = st.text_input(
                            "Médicament & Dosage", value=row["molecule"]
                        )

                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            mod_freq = st.text_input(
                                "Fréquence", value=row["frequence"]
                            )
                            mod_prise = st.text_input(
                                "Moment de Prise", value=row["prise"]
                            )
                        with col_e2:
                            mod_date_debut = st.date_input(
                                "Date de Début", value=row["date_debut"]
                            )
                            mod_duree = st.number_input(
                                "Durée (Jours)",
                                value=int(row["duree"]),
                                min_value=1,
                            )

                        btn_sauver_edit = st.form_submit_button(
                            "💾 Enregistrer les modifications",
                            use_container_width=True,
                        )

                        if btn_sauver_edit:
                            st.session_state.ordonnances[idx]["patient"] = (
                                mod_patient
                            )
                            st.session_state.ordonnances[idx]["hopital"] = (
                                mod_hopital
                            )
                            st.session_state.ordonnances[idx]["molecule"] = (
                                mod_molecule
                            )
                            st.session_state.ordonnances[idx]["frequence"] = (
                                mod_freq
                            )
                            st.session_state.ordonnances[idx]["prise"] = (
                                mod_prise
                            )
                            st.session_state.ordonnances[idx]["date_debut"] = (
                                mod_date_debut
                            )
                            st.session_state.ordonnances[idx]["duree"] = (
                                mod_duree
                            )
                            st.session_state.ordonnances[idx]["date_fin"] = (
                                mod_date_debut + timedelta(days=int(mod_duree))
                            )

                            sauvegarder_ordonnances()
                            st.success("Modifications enregistrées !")
                            st.rerun()

# -----------------------------------------------------------------------------
# 4. GESTION ÉTABLISSEMENTS & DOSSIERS PATIENTS
# -----------------------------------------------------------------------------
elif menu == "4. Gestion Établissements & Dossiers":
    st.header("⚙️ Gestion des Établissements & Dossiers Médicaux")

    tab_hopitaux, tab_patients = st.tabs(
        ["🏥 Annuaire Établissements / Hôpitaux", "📁 Dossiers Patients"]
    )

    # --- ANNUAIRE DES ÉTABLISSEMENTS ---
    with tab_hopitaux:
        st.subheader("➕ Ajouter un Établissement / Praticien")

        with st.form("form_ajouter_hopital", clear_on_submit=True):
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                nom_hop = st.text_input(
                    "Nom de l'Établissement / Praticien*",
                    placeholder="Ex: CHU Purpan / Dr. Martin",
                )
                email_hop = st.text_input(
                    "Adresse Email (pour alertes)*",
                    placeholder="secretariat@hopital.fr",
                )
                tel_hop = st.text_input(
                    "Numéro de Téléphone", placeholder="05 61 00 00 00"
                )
            with col_h2:
                service_hop = st.text_input(
                    "Service / Spécialité", placeholder="Ex: Pneumologie"
                )
                adresse_hop = st.text_area(
                    "Adresse postale",
                    placeholder="Place du Dr Baylac, 31059 Toulouse",
                    height=100,
                )

            btn_add_hop = st.form_submit_button(
                "💾 Enregistrer l'établissement", use_container_width=True
            )

            if btn_add_hop:
                if not nom_hop or not email_hop:
                    st.error("Le Nom et l'Email sont obligatoires.")
                else:
                    st.session_state.hopitaux_db.append(
                        {
                            "nom": nom_hop,
                            "email": email_hop,
                            "telephone": tel_hop,
                            "service": service_hop,
                            "adresse": adresse_hop,
                        }
                    )
                    sauvegarder_hopitaux()
                    st.success(
                        f"L'établissement **{nom_hop}** a été ajouté avec succès !"
                    )
                    st.rerun()

        st.divider()
        st.subheader("📋 Liste des Établissements Enregistrés")

        if not st.session_state.hopitaux_db:
            st.info("Aucun établissement enregistré pour le moment.")
        else:
            for idx_h, h in enumerate(list(st.session_state.hopitaux_db)):
                with st.expander(
                    f"🏥 **{h['nom']}** — {h['email']} | 📞 {h['telephone']}"
                ):
                    c_det, c_del = st.columns([4, 1])
                    with c_det:
                        st.write(f"**Service :** {h.get('service', 'N/C')}")
                        st.write(f"**Adresse :** {h.get('adresse', 'N/C')}")
                        st.write(f"**Email direct :** `{h.get('email', '')}`")
                    with c_del:
                        if st.button("🗑️ Supprimer", key=f"del_hop_db_{idx_h}"):
                            st.session_state.hopitaux_db.pop(idx_h)
                            sauvegarder_hopitaux()
                            st.toast("Établissement supprimé !")
                            st.rerun()

    # --- DOSSIERS PATIENTS ---
    with tab_patients:
        if not st.session_state.ordonnances:
            st.info("Aucune donnée ordonnance enregistrée.")
        else:
            df = pd.DataFrame(st.session_state.ordonnances)
            patients_liste = sorted(list(df["patient"].unique()))

            patient_sel = st.selectbox(
                "Sélectionnez un patient :", patients_liste
            )

            if patient_sel:
                st.subheader(f"Dossier Médical de : {patient_sel}")

                if st.button(
                    f"⚠️ Supprimer TOUT le dossier de {patient_sel}",
                    type="primary",
                ):
                    st.session_state.ordonnances = [
                        o
                        for o in st.session_state.ordonnances
                        if o["patient"] != patient_sel
                    ]
                    sauvegarder_ordonnances()
                    st.success(f"Dossier de {patient_sel} supprimé.")
                    st.rerun()

                st.markdown("---")

                for idx, row in enumerate(list(st.session_state.ordonnances)):
                    if row["patient"] == patient_sel:
                        c_txt, c_btn = st.columns([5, 1])
                        with c_txt:
                            st.write(
                                f"💊 **{row['molecule']}** ({row['hopital']}) — {row['prise']} (Fin : {row['date_fin'].strftime('%d/%m/%Y')}) - *{row['statut']}*"
                            )
                        with c_btn:
                            if st.button("🗑️ Supprimer", key=f"del_pat_{idx}"):
                                supprimer_ligne(idx)
                                st.rerun()
