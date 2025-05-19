// static/js/app.js
document.addEventListener('DOMContentLoaded', () => {
    const npcSelectionArea = document.getElementById('npc-selection-area');
    const selectedNpcListElement = document.getElementById('selected-npc-list');
    const noNpcsSelectedElement = document.getElementById('no-npcs-selected');
    const proceedToSceneButton = document.getElementById('proceed-to-scene-button');

    let allNPCs = []; // To store fetched NPCs
    let selectedNPCs = new Map(); // Use a Map to store selected NPCs by ID for easy add/remove

    if (!npcSelectionArea || !selectedNpcListElement || !proceedToSceneButton || !noNpcsSelectedElement) {
        console.error('One or more essential UI elements are missing!');
        if(npcSelectionArea) npcSelectionArea.innerHTML = '<p>Error: UI setup incomplete. Please check console.</p>';
        return;
    }

    // Fetch NPCs from your backend API
    fetch('/api/npcs')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(npcs => {
            allNPCs = npcs; // Store all fetched NPCs
            if (!Array.isArray(allNPCs)) {
                console.error('Fetched NPC data is not an array:', allNPCs);
                npcSelectionArea.innerHTML = '<p>Error: NPC data format is incorrect. Please check the /api/npcs endpoint.</p>';
                return;
            }
            if (allNPCs.length === 0) {
                npcSelectionArea.innerHTML = '<p>No NPCs found in the database. Please run the data loader script or check your database.</p>';
                return;
            }
            displayNPCs(allNPCs);
        })
        .catch(error => {
            console.error('Error fetching NPCs:', error);
            npcSelectionArea.innerHTML = `<p>Error loading NPCs: ${error.message}. Check the browser console and Flask server logs for more details.</p>`;
        });

    /**
     * Displays the list of NPCs on the page.
     * @param {Array<Object>} npcs - An array of NPC objects.
     */
    function displayNPCs(npcs) {
        npcSelectionArea.innerHTML = ''; // Clear loading message

        npcs.forEach(npc => {
            const card = document.createElement('div');
            card.className = 'npc-card';
            card.dataset.npcId = npc._id; // Store NPC ID on the card element

            const npcInitials = npc.name ? npc.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC");
            const placeholderTextColor = 'FFFFFF';
            const placeholderImageUrl = `https://placehold.co/80x80/${placeholderBgColor}/${placeholderTextColor}?text=${npcInitials}&font=source-sans-pro`;

            card.innerHTML = `
                <div class="npc-portrait-container">
                    <img src="${placeholderImageUrl}" alt="Portrait of ${npc.name || 'NPC'}" class="npc-portrait" onerror="this.src='https://placehold.co/80x80/CCCCCC/FFFFFF?text=ERR&font=lora'; this.onerror=null;">
                </div>
                <div class="npc-details">
                    <h3>${npc.name || 'Unnamed NPC'}</h3>
                    <p><em>${npc.appearance || 'No description available.'}</em></p>
                    ${npc.personality_traits && npc.personality_traits.trim().length > 0 ? `<p>Traits: ${npc.personality_traits}</p>` : '<p>Traits: Not specified.</p>'}
                </div>
            `;

            // Event listener for selecting/deselecting NPC
            card.addEventListener('click', () => {
                toggleNPCSelection(npc, card);
            });
            npcSelectionArea.appendChild(card);
        });
    }

    /**
     * Toggles the selection state of an NPC.
     * @param {Object} npc - The NPC object.
     * @param {HTMLElement} cardElement - The HTML element of the NPC card.
     */
    function toggleNPCSelection(npc, cardElement) {
        const npcId = npc._id;
        if (selectedNPCs.has(npcId)) {
            selectedNPCs.delete(npcId);
            cardElement.classList.remove('selected');
        } else {
            selectedNPCs.set(npcId, npc); // Store the whole NPC object if needed later
            cardElement.classList.add('selected');
        }
        updateSelectedNPCListUI();
        updateProceedButtonState();
    }

    /**
     * Updates the UI list of selected NPCs.
     */
    function updateSelectedNPCListUI() {
        selectedNpcListElement.innerHTML = ''; // Clear current list
        if (selectedNPCs.size === 0) {
            selectedNpcListElement.appendChild(noNpcsSelectedElement);
        } else {
            selectedNPCs.forEach(npc => {
                const listItem = document.createElement('li');
                listItem.textContent = npc.name;
                selectedNpcListElement.appendChild(listItem);
            });
        }
    }

    /**
     * Enables or disables the "Proceed to Scene" button based on selection.
     */
    function updateProceedButtonState() {
        proceedToSceneButton.disabled = selectedNPCs.size === 0;
    }

    /**
     * Handles navigation to the scene setup page.
     */
    proceedToSceneButton.addEventListener('click', () => {
        if (selectedNPCs.size > 0) {
            const selectedIds = Array.from(selectedNPCs.keys());
            // Pass selected NPC IDs as a comma-separated query parameter
            window.location.href = `/scene?npcs=${selectedIds.join(',')}`;
        }
    });
    
    /**
     * Generates a hex color code from a string for placeholder images.
     * @param {string} str - The input string.
     * @returns {string} A hex color code without the '#'.
     */
    function stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash; 
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }

    // Initial UI updates
    updateSelectedNPCListUI(); // Ensure "None yet" is shown initially
    updateProceedButtonState();
});