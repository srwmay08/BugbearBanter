// srwmay08/bugbearbanter/BugbearBanter-cf73d42aed67696601941e44943cc5db45c8e493/server/static/js/npc-selector.js
document.addEventListener('DOMContentLoaded', () => {
    const pcSelectionListDiv = document.getElementById('pc-selection-list');
    const npcSelectionListDiv = document.getElementById('npc-selection-list');
    const startSceneBtn = document.getElementById('start-scene-btn');
    let allCharacters = [];

    async function loadCharacters() {
        if (pcSelectionListDiv) pcSelectionListDiv.innerHTML = '<p>Loading PCs...</p>';
        if (npcSelectionListDiv) npcSelectionListDiv.innerHTML = '<p>Loading NPCs...</p>';

        try {
            const response = await fetch('/api/npcs'); // Fetches all characters
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            allCharacters = await response.json();

            renderCharacterLists();
        } catch (error) {
            console.error("Failed to load characters:", error);
            if (pcSelectionListDiv) pcSelectionListDiv.innerHTML = '<p style="color:red;">Could not load PCs.</p>';
            if (npcSelectionListDiv) npcSelectionListDiv.innerHTML = '<p style="color:red;">Could not load NPCs.</p>';
        }
    }

    function renderCharacterLists() {
        let pcHtml = '<ul>';
        let npcHtml = '<ul>';
        let pcCount = 0;
        let npcCount = 0;

        allCharacters.forEach(char => {
            const listItemHtml = `
                <li>
                    <input type="checkbox" id="char-${char._id}" name="character_select" value="${char._id}" data-type="${char.character_type || 'NPC'}">
                    <label for="char-${char._id}">${char.name || 'Unnamed Character'}</label>
                </li>`;

            if (char.character_type === 'PC') {
                pcHtml += listItemHtml;
                pcCount++;
            } else {
                npcHtml += listItemHtml;
                npcCount++;
            }
        });

        pcHtml += '</ul>';
        npcHtml += '</ul>';

        if (pcSelectionListDiv) {
            pcSelectionListDiv.innerHTML = pcCount > 0 ? pcHtml : '<p>No PCs available.</p>';
        }
        if (npcSelectionListDiv) {
            npcSelectionListDiv.innerHTML = npcCount > 0 ? npcHtml : '<p>No NPCs available.</p>';
        }
    }

    if (startSceneBtn) {
        startSceneBtn.addEventListener('click', () => {
            const selectedPcIds = [];
            const selectedNpcIds = [];

            document.querySelectorAll('input[name="character_select"]:checked').forEach(checkbox => {
                if (checkbox.dataset.type === 'PC') {
                    selectedPcIds.push(checkbox.value);
                } else {
                    selectedNpcIds.push(checkbox.value);
                }
            });

            if (selectedPcIds.length === 0 && selectedNpcIds.length === 0) {
                alert("Please select at least one character for the scene.");
                return;
            }
            //Navigate to scene.html with pc_ids and npc_ids as URL parameters
            window.location.href = `/scene.html?pc_ids=${selectedPcIds.join(',')}&npc_ids=${selectedNpcIds.join(',')}`;
        });
    }

    loadCharacters();
});