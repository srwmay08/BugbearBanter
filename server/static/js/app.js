// ---- server/static/js/app.js ----
document.addEventListener('DOMContentLoaded', () => {
    const npcSelectionArea = document.getElementById('npc-selection-area');

    if (!npcSelectionArea) {
        console.error('NPC selection area not found!');
        return;
    }

    fetch('/api/npcs')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(npcs => {
            if (!Array.isArray(npcs)) { // Add a check if npcs is an array
                console.error('Fetched NPC data is not an array:', npcs);
                npcSelectionArea.innerHTML = '<p>Error: NPC data format is incorrect.</p>';
                return;
            }
            if (npcs.length === 0) {
                npcSelectionArea.innerHTML = '<p>No NPCs found. Go create some!</p>';
                return;
            }
            displayNPCs(npcs);
        })
        .catch(error => {
            console.error('Error fetching NPCs:', error);
            npcSelectionArea.innerHTML = `<p>Error loading NPCs: ${error.message}. Check the console for details.</p>`;
        });

    function displayNPCs(npcs) {
        npcSelectionArea.innerHTML = ''; // Clear loading/error message
        npcs.forEach(npc => {
            const card = document.createElement('div');
            card.className = 'npc-card'; // For styling
            // --- CORRECTED innerHTML ---
            card.innerHTML = `
                <h3><span class="math-inline">\{npc\.name \|\| 'Unnamed NPC'\}</h3\>