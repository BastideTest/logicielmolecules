def parser_texte(texte):
    """Extraction intelligente adaptée aux formats d'ordonnance réels."""
    donnees = {
        "patient": "",
        "hopital": "",
        "molecule": "",
        "date_debut": datetime.today().date(),
        "frequence": 1,
        "duree": 30,  # 1 mois = 30 jours par défaut
    }

    lignes = [l.strip() for l in texte.split("\n") if l.strip()]

    # 1. Extraction du Patient (Cherche une ligne avec un prénom/nom + âge ou juste nom isolé)
    m_patient = re.search(
        r"([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)(?:,\s*\d+\s*ans)?", texte
    )
    if m_patient and "Docteur" not in m_patient.group(1):
        donnees["patient"] = m_patient.group(1)

    # 2. Médecin / Établissement
    m_doc = re.search(r"(Docteur\s+[A-Za-zÀ-ÿ\s]+|CH\s+[A-Za-zÀ-ÿ\s]+)", texte)
    if m_doc:
        donnees["hopital"] = m_doc.group(1).strip()

    # 3. Molécule & Dosage (Détecte la première molécule disponible)
    m_molecules = re.findall(
        r"([A-Z][a-zà-ÿ]+\s+\d+(?:[\.,]\d+)?\s*(?:mg|g|ml))", texte
    )
    if m_molecules:
        donnees["molecule"] = " / ".join(m_molecules)  # Associe les molécules

    # 4. Durée (Gestion de "1 mois" -> 30 jours)
    if "1 mois" in texte.lower() or "un mois" in texte.lower():
        donnees["duree"] = 30
    elif "2 mois" in texte.lower():
        donnees["duree"] = 60

    # 5. Fréquence
    if "soir" in texte.lower() and "matin" in texte.lower():
        donnees["frequence"] = 3
    elif "soir" in texte.lower():
        donnees["frequence"] = 1

    return donnees
