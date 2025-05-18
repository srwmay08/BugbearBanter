document.addEventListener('DOMContentLoaded', () => {
    const npcSelectionArea = document.getElementById('npc-selection-area');

    if (!npcSelectionArea) {
        console.error('NPC selection area not found!');
        return;
    }

    fetch('/api/npcs') // Your new API endpoint
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(npcs => {
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
            card.innerHTML = `
                <h3><span class="math-inline">\{npc\.name\}</h3\>