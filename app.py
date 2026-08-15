<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Planning Semainier & Gestion Clients</title>
    <style>
        :root {
            --primary: #2563eb;
            --bg: #f8fafc;
            --card: #ffffff;
            --border: #e2e8f0;
            --text: #0f172a;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            background: var(--card);
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .storage-box {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.85em;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        button {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
        }

        button:hover { opacity: 0.9; }

        .grid-planning {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 10px;
        }

        .day-column {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            min-height: 450px;
            display: flex;
            flex-direction: column;
        }

        .day-header {
            background: #f1f5f9;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            border-bottom: 1px solid var(--border);
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        .day-content {
            padding: 10px;
            flex-grow: 1;
        }

        .event-card {
            background: #e0f2fe;
            border-left: 4px solid var(--primary);
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            width: 320px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        input, select {
            padding: 8px;
            border: 1px solid var(--border);
            border-radius: 4px;
        }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h2>Planning Semainier</h2>
        <div class="nav-controls">
            <button onclick="changerSemaine(-1)">&larr; Précédent</button>
            <span id="currentWeekDisplay" style="font-weight: bold;"></span>
            <button onclick="changerSemaine(1)">Suivant &rarr;</button>
        </div>
        <button onclick="ouvrirModal()">+ Nouveau rendez-vous</button>
    </header>

    <div class="storage-box">
        <span><strong>Dossier cible local :</strong> <code>C:\Users\favie\Documents</code></span>
        <div>
            <button onclick="sauvegarderLocalement()">💾 Enregistrer le fichier</button>
            <button onclick="chargerFichierLocal()">📂 Charger le fichier</button>
        </div>
    </div>

    <div class="grid-planning" id="planningGrid"></div>
</div>

<!-- Modal Ajout RDV -->
<div class="modal" id="modalRdv">
    <div class="modal-content">
        <h3>Nouveau Rendez-vous</h3>
        <label>Date :</label>
        <input type="date" id="rdvDate">
        <label>Heure :</label>
        <input type="time" id="rdvHeure">
        <label>Nom du Client :</label>
        <input type="text" id="rdvClient" placeholder="M. Dupont">
        <label>Détails / Prestation :</label>
        <input type="text" id="rdvNote" placeholder="Soin, Réunion...">
        <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:10px;">
            <button type="button" onclick="fermerModal()" style="background:#94a3b8;">Annuler</button>
            <button type="button" onclick="ajouterRDV()">Enregistrer</button>
        </div>
    </div>
</div>

<script>
    let currentDate = new Date();
    let rdvData = JSON.parse(localStorage.getItem('planning_data')) || [];

    // Obtenir le lundi de la semaine courante
    function getMonday(d) {
        d = new Date(d);
        let day = d.getDay(),
            diff = d.getDate() - day + (day == 0 ? -6 : 1);
        return new Date(d.setDate(diff));
    }

    function changerSemaine(offsetDays) {
        currentDate.setDate(currentDate.getDate() + (offsetDays * 7));
        renderPlanning();
    }

    function renderPlanning() {
        const grid = document.getElementById('planningGrid');
        grid.innerHTML = '';
        const monday = getMonday(currentDate);

        const options = { month: 'short', day: 'numeric' };
        const endOfWeek = new Date(monday);
        endOfWeek.setDate(monday.getDate() + 6);
        
        document.getElementById('currentWeekDisplay').innerText = 
            `Semaine du ${monday.toLocaleDateString('fr-FR', options)} au ${endOfWeek.toLocaleDateString('fr-FR', options)}`;

        const jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

        for (let i = 0; i < 7; i++) {
            let dayDate = new Date(monday);
            dayDate.setDate(monday.getDate() + i);
            let dateStr = dayDate.toISOString().split('T')[0];

            let col = document.createElement('div');
            col.className = 'day-column';
            col.innerHTML = `
                <div class="day-header">
                    ${jours[i]}<br>
                    <small style="font-weight:normal; color:#64748b;">${dayDate.toLocaleDateString('fr-FR')}</small>
                </div>
                <div class="day-content" id="day-${dateStr}"></div>
            `;
            grid.appendChild(col);

            // Charger les RDV du jour
            let events = rdvData.filter(r => r.date === dateStr);
            events.sort((a,b) => a.heure.localeCompare(b.heure));
            let contentDiv = col.querySelector('.day-content');
            
            events.forEach(e => {
                let card = document.createElement('div');
                card.className = 'event-card';
                card.innerHTML = `<strong>${e.heure}</strong> - ${e.client}<br><small>${e.note}</small>`;
                contentDiv.appendChild(card);
            });
        }
    }

    function ouvrirModal() { document.getElementById('modalRdv').style.display = 'flex'; }
    function fermerModal() { document.getElementById('modalRdv').style.display = 'none'; }

    function ajouterRDV() {
        const date = document.getElementById('rdvDate').value;
        const heure = document.getElementById('rdvHeure').value;
        const client = document.getElementById('rdvClient').value;
        const note = document.getElementById('rdvNote').value;

        if(!date || !heure || !client) { alert('Veuillez remplir au moins la date, l\'heure et le client'); return; }

        rdvData.push({ date, heure, client, note });
        localStorage.setItem('planning_data', JSON.stringify(rdvData));
        fermerModal();
        renderPlanning();
    }

    // Gestion de l'enregistrement dans le fichier C:\Users\favie\Documents
    async function sauvegarderLocalement() {
        const content = JSON.stringify(rdvData, null, 2);
        try {
            const handle = await window.showSaveFilePicker({
                suggestedName: 'donnees_planning.json',
                types: [{ description: 'Fichier JSON', accept: { 'application/json': ['.json'] } }]
            });
            const writable = await handle.createWritable();
            await writable.write(content);
            await writable.close();
            alert('Sauvegarde effectuée avec succès dans le dossier choisi !');
        } catch (err) {
            console.error(err);
        }
    }

    async function chargerFichierLocal() {
        try {
            const [handle] = await window.showOpenFilePicker({
                types: [{ description: 'Fichier JSON', accept: { 'application/json': ['.json'] } }]
            });
            const file = await handle.getFile();
            const text = await file.text();
            rdvData = JSON.parse(text);
            localStorage.setItem('planning_data', JSON.stringify(rdvData));
            renderPlanning();
            alert('Données chargées avec succès !');
        } catch (err) {
            console.error(err);
        }
    }

    // Initialisation
    renderPlanning();
</script>
</body>
</html>
