// static/js/app.js
document.addEventListener('DOMContentLoaded', () => {
    const npcSelectionArea = document.getElementById('npc-selection-area');

    if (!npcSelectionArea) {
        console.error('NPC selection area not found!');
        return;
    }

    // Fetch NPCs from your backend API
    fetch('/api/npcs')
        .then(response => {
            if (!response.ok) {
                // If the response is not OK, throw an error with status text
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }
            return response.json(); // Parse the JSON data from the response
        })
        .then(npcs => {
            // Check if the fetched data is actually an array
            if (!Array.isArray(npcs)) {
                console.error('Fetched NPC data is not an array:', npcs);
                npcSelectionArea.innerHTML = '<p>Error: NPC data format is incorrect. Please check the /api/npcs endpoint.</p>';
                return;
            }
            // If no NPCs are found, display a message
            if (npcs.length === 0) {
                npcSelectionArea.innerHTML = '<p>No NPCs found in the database. Go create some!</p>';
                return;
            }
            // If NPCs are found, display them
            displayNPCs(npcs);
        })
        .catch(error => {
            // Handle any errors that occurred during the fetch operation
            console.error('Error fetching NPCs:', error);
            npcSelectionArea.innerHTML = `<p>Error loading NPCs: ${error.message}. Check the browser console and Flask server logs for more details, particularly for the /api/npcs endpoint.</p>`;
        });

    /**
     * Displays the list of NPCs on the page.
     * @param {Array<Object>} npcs - An array of NPC objects.
     */
    function displayNPCs(npcs) {
        npcSelectionArea.innerHTML = ''; // Clear any previous content (like loading/error messages)

        npcs.forEach(npc => {
            const card = document.createElement('div');
            card.className = 'npc-card'; // Apply styling for the NPC card

            // Set the HTML content for the NPC card using a template literal
            // This assumes your NPC objects have 'name', 'appearance', and 'personality_traits' fields.
            // It includes fallbacks for missing data.
            card.innerHTML = `
                <h3>${npc.name || 'Unnamed NPC'}</h3>
                <p><em>${npc.appearance || 'No description available.'}</em></p>
                ${npc.personality_traits && npc.personality_traits.length > 0 ? `<p>Traits: ${npc.personality_traits.join(', ')}</p>` : '<p>Traits: Not specified.</p>'}
            `;

            // Add an event listener to handle clicks on the NPC card
            card.addEventListener('click', () => {
                handleNPCSelection(npc);
            });

            npcSelectionArea.appendChild(card); // Add the newly created card to the selection area
        });
    }

    /**
     * Handles the selection of an NPC.
     * @param {Object} npc - The selected NPC object.
     */
    function handleNPCSelection(npc) {
        console.log('Selected NPC:', npc);
        // Placeholder for what happens when an NPC is selected.
        // You might want to:
        // 1. Store npc._id (if your NPC objects have an _id field from MongoDB).
        // 2. Navigate to a dialogue page: window.location.href = `/dialogue_interface?npc_id=${npc._id}`;
        // 3. Fetch dialogue options for this NPC and display them.
        // 4. Show more details about the NPC in a modal or another section.
        alert(`You selected ${npc.name}! (ID: ${npc._id || 'N/A'})`);
    }
});
