// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    const participantsListElement = document.getElementById('scene-participants-list');
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const generateDialogueButton = document.getElementById('generate-dialogue-button');
    const conversationLogContainer = document.getElementById('conversation-log-container');
    const logPlaceholder = document.querySelector('.log-placeholder');

    let sceneParticipants = []; // Array to store full NPC objects for the scene
    let allFetchedNPCs = null; // Store all NPCs fetched once for quick lookup

    if (!participantsListElement || !sceneDescriptionTextarea || !generateDialogueButton || !conversationLogContainer) {
        console.error('One or more essential UI elements for the scene page are missing!');
        return;
    }

    // Get selected NPC IDs from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const npcIdsParam = urlParams.get('npcs');
    const selectedNpcIds = npcIdsParam ? npcIdsParam.split(',') : [];

    if (selectedNpcIds.length === 0) {
        participantsListElement.innerHTML = '<p>No NPCs were selected for this scene. Please go back and select participants.</p>';
        generateDialogueButton.disabled = true;
        return;
    }

    // Fetch all NPCs to get details for the selected ones
    // In a more optimized app, you might have an endpoint to fetch specific NPCs by ID
    // or pass more data via localStorage/sessionStorage from the selection page.
    fetch('/api/npcs')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(allNpcs => {
            allFetchedNPCs = allNpcs;
            selectedNpcIds.forEach(id => {
                const npc = allNpcs.find(n => n._id === id);
                if (npc) {
                    sceneParticipants.push(npc);
                }
            });
            displaySceneParticipants();
            if (sceneParticipants.length === 0) {
                 participantsListElement.innerHTML = '<p>Could not load details for selected NPCs.</p>';
                 generateDialogueButton.disabled = true;
            }
        })
        .catch(error => {
            console.error('Error fetching NPC details for scene:', error);
            participantsListElement.innerHTML = '<p>Error loading NPC details. See console.</p>';
            generateDialogueButton.disabled = true;
        });

    function displaySceneParticipants() {
        participantsListElement.innerHTML = ''; // Clear loading message
        if (sceneParticipants.length === 0) {
            participantsListElement.innerHTML = '<p>No valid participants found for the scene.</p>';
            return;
        }
        sceneParticipants.forEach(npc => {
            const chip = document.createElement('div');
            chip.className = 'participant-chip';

            const npcInitials = npc.name ? npc.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC");
            const placeholderImageUrl = `https://placehold.co/30x30/${placeholderBgColor}/FFFFFF?text=${npcInitials}&font=source-sans-pro`;
            
            chip.innerHTML = `
                <img src="${placeholderImageUrl}" alt="${npc.name}" title="${npc.name}">
                <span>${npc.name}</span>
            `;
            participantsListElement.appendChild(chip);
        });
    }

    generateDialogueButton.addEventListener('click', () => {
        const sceneDescription = sceneDescriptionTextarea.value.trim();
        if (sceneParticipants.length === 0) {
            alert('Please select NPCs for the scene first (go back to NPC selection).');
            return;
        }
        if (!sceneDescription) {
            alert('Please describe the scene before starting the conversation.');
            sceneDescriptionTextarea.focus();
            return;
        }

        if (logPlaceholder) logPlaceholder.remove(); // Remove initial placeholder

        // Placeholder: Simulate initiating dialogue generation
        addDialogueEntry("SYSTEM", `Scene started. GM described: "${sceneDescription}"`, "system");
        
        // Here you would make an API call to your backend to generate dialogue
        // For example: /api/dialogue/generate (which you have from previous steps)
        // The request would include sceneParticipants (IDs or full profiles) and sceneDescription.

        // For now, let's simulate a first line from the first NPC
        if (sceneParticipants.length > 0) {
            const firstNpc = sceneParticipants[0];
            // This is where you'd call your AI service
            // For now, a placeholder response:
            const placeholderDialogue = `Hello, I am ${firstNpc.name}. What is this about, "${sceneDescription.substring(0,30)}..."?`;
            addDialogueEntry(firstNpc.name, placeholderDialogue, "npc", firstNpc);
        }
        
        // Disable button after starting to prevent multiple requests without new context
        // generateDialogueButton.disabled = true; 
        // You'll need more sophisticated state management later
    });

    /**
     * Adds a dialogue entry to the conversation log.
     * @param {string} speakerName - The name of the speaker (NPC name, "GM", "SYSTEM").
     * @param {string} text - The dialogue text.
     * @param {string} type - 'npc', 'player', 'system', 'gm'.
     * @param {Object} [npcData=null] - The NPC object, if the speaker is an NPC (for portrait).
     */
    function addDialogueEntry(speakerName, text, type = "npc", npcData = null) {
        const entryDiv = document.createElement('div');
        entryDiv.classList.add('chat-entry', type);

        let portraitHtml = '';
        if (type === 'npc' && npcData) {
            const npcInitials = npcData.name ? npcData.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npcData.name || "defaultNPC");
            const portraitUrl = `https://placehold.co/40x40/${placeholderBgColor}/FFFFFF?text=${npcInitials}&font=source-sans-pro`;
            portraitHtml = `<img src="${portraitUrl}" alt="${speakerName}" class="chat-portrait">`;
        } else if (type === 'system') {
             portraitHtml = `<div class="chat-portrait system-icon">⚙️</div>`; // Simple system icon
        }


        entryDiv.innerHTML = `
            ${portraitHtml}
            <div class="chat-bubble">
                <span class="speaker-name">${speakerName}</span>
                <p class="dialogue-text">${text.replace(/\n/g, '<br>')}</p> 
            </div>
        `;
        conversationLogContainer.appendChild(entryDiv);
        conversationLogContainer.scrollTop = conversationLogContainer.scrollHeight; // Auto-scroll to bottom
    }


    // Helper function (can be moved to a shared utility file later)
    function stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash;
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }

    // Placeholder event listeners for dialogue controls
    document.getElementById('btn-submit-memory').addEventListener('click', () => alert('Submit to Memory clicked (not implemented)'));
    document.getElementById('btn-undo-memory').addEventListener('click', () => alert('Undo Last from Memory clicked (not implemented)'));
    document.getElementById('btn-next-topic').addEventListener('click', () => alert('Next Topic clicked (not implemented)'));
    document.getElementById('btn-regen-topics').addEventListener('click', () => alert('Regenerate Topics clicked (not implemented)'));
    document.getElementById('btn-show-top5').addEventListener('click', () => alert('Show Top 5 clicked (not implemented)'));
    document.getElementById('btn-show-tree').addEventListener('click', () => alert('Show Conversation Tree clicked (not implemented)'));

});
