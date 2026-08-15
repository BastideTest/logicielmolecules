<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Planning - Fiche Patient</title>
    <style>
        :root {
            --bg-color: #f4f6f9;
            --card-bg: #ffffff;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --success: #16a34a;
            --success-hover: #15803d;
            --warning: #d97706;
            --warning-hover: #b45309;
            --danger: #dc2626;
            --danger-hover: #b91c1c;
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --border: #e5e7eb;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            width: 100%;
            max-width: 600px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* --- FICHE PATIENT --- */
        .patient-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            overflow: hidden;
        }

        .card-header {
            background-color: #eff6ff;
            border-bottom: 1px solid #dbeafe;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-header h2 {
            margin: 0;
            font-size: 1.25rem;
            color: #1e40af;
        }

        .badge-time {
            background-color: var(--primary);
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
        }

        .card-body {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 8px;
        }

        .info-row:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }

        .label {
            font-weight: 600;
            color: var(--text-muted);
        }

        .value {
            font-weight: 500;
            text-align: right;
        }

        /* --- BARRE DE BOUTONS DISTINCTS ET VISIBLES --- */
        .actions-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            width: 100%;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 14px 16px;
            font-size: 0.95rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }

        .btn:active {
            transform: translateY(0);
        }

        /* Couleurs et distinctions spécifiques */
        .btn-confirm {
            background-color: var(--success);
        }
        .btn-confirm:hover {
            background-color: var(--success-hover);
        }

        .btn-edit {
            background-color: var(--primary);
        }
        .btn-edit:hover {
            background-color: var(--primary-hover);
        }

        .btn-reschedule {
            background-color: var(--warning);
        }
        .btn-reschedule:hover {
            background-color: var(--warning-hover);
        }

        .btn-cancel {
            background-color: var(--danger);
        }
        .btn-cancel:hover {
            background-color: var(--danger-hover);
        }

        /* SVG des icônes */
        .btn svg {
            width: 18px;
            height: 18px;
            fill: none;
            stroke: currentColor;
            stroke-width: 2.2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
    </style>
</head>
<body>

<div class="container">

    <!-- 1. FICHE PATIENT -->
    <div class="patient-card">
        <div class="card-header">
            <h2>Jean DUPONT</h2>
            <span class="badge-time">14h30 - 15h00</span>
        </div>
        <div class="card-body">
            <div class="info-row">
                <span class="label">Motif :</span>
                <span class="value">Consultation suivi</span>
            </div>
            <div class="info-row">
                <span class="label">Téléphone :</span>
                <span class="value">06 12 34 56 78</span>
            </div>
            <div class="info-row">
                <span class="label">Statut :</span>
                <span class="value" style="color: var(--primary); font-weight: 600;">Planifié</span>
            </div>
            <div class="info-row">
                <span class="label">Notes :</span>
                <span class="value">Dossier médical mis à jour. Ramener les analyses.</span>
            </div>
        </div>
    </div>

    <!-- 2. BOUTONS D'ACTION SOUS LA FICHE PATIENT -->
    <div class="actions-bar">
        <button class="btn btn-confirm" onclick="validerRdv()">
            <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Valider
        </button>

        <button class="btn btn-edit" onclick="modifierRdv()">
            <svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            Modifier
        </button>

        <button class="btn btn-reschedule" onclick="deplacerRdv()">
            <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            Déplacer
        </button>

        <button class="btn btn-cancel" onclick="annulerRdv()">
            <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            Annuler
        </button>
    </div>

</div>

<script>
    function validerRdv() {
        alert("Rendez-vous validé !");
    }

    function modifierRdv() {
        alert("Ouverture de l'édition du rendez-vous.");
    }

    function deplacerRdv() {
        alert("Sélectionnez une nouvelle date pour ce rendez-vous.");
    }

    function annulerRdv() {
        if(confirm("Êtes-vous sûr de vouloir annuler ce rendez-vous ?")) {
            alert("Rendez-vous annulé.");
        }
    }
</script>

</body>
</html>
