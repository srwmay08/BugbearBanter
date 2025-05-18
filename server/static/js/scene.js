// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const npcInteractionArea = document.getElementById('npc-interaction-area');
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const startSceneButton = document.getElementById('start-scene-button'); // Corrected ID from HTML
    const currentSceneDescriptionDisplay = document.getElementById('current-scene-description-display');
    // Get the loading message element safely, it might be removed if NPCs load fast
    let loadingNpcsMessage = npcInteractionArea ? npcInteractionArea.querySelector('.loading-npcs-message') : null;

    // --- State Variables ---
    let sceneParticipants = []; // Stores full NPC objects for the current scene

    // --- Initial Error Checks for Essential Elements ---
    if (!npcInteractionArea || !sceneDescriptionTextarea || !startSceneButton || !currentSceneDescriptionDisplay) {
        console.error('CRITICAL: One or more essential UI elements for the scene page are missing from scene.html!');
        if(npcInteractionArea) { // Only try to update if it exists
            npcInteractionArea.innerHTML = '<p style="color:red; text-align:center;">Error: UI setup incomplete. Please check console and HTML structure.</p>';
        }
        return;
    }
    // If loadingNpcsMessage was initially null (because npcInteractionArea was null), try to get it now if npcInteractionArea exists
    if (!loadingNpcsMessage && npcInteractionArea) {
        loadingNpcsMessage = npcInteractionArea.querySelector('.loading-npcs-message');
    }


    // --- Get Selected NPCs from URL ---
    const urlParams = new URLSearchParams(window.location.search);
    const npcIdsParam = urlParams.get('npcs');
    const selectedNpcIds = npcIdsParam ? npcIdsParam.split(',') : [];

    if (selectedNpcIds.length === 0) {
        if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'No NPCs were selected for this scene. Please go back to NPC selection.';
        else if(npcInteractionArea) npcInteractionArea.innerHTML = '<p>No NPCs were selected for this scene. Please go back to NPC selection.</p>';
        startSceneButton.disabled = true;
        return;
    }

    // --- Fetch NPC Data and Initialize UI ---
    fetch('/api/npcs') // Assumes this endpoint returns ALL NPCs
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error fetching NPC list! Status: ${response.status} ${response.statusText}`);
            return response.json();
        })
        .then(allNpcs => {
            selectedNpcIds.forEach(id => {
                const npc = allNpcs.find(n => n._id === id);
                if (npc) {
                    sceneParticipants.push(npc);
                } else {
                    console.warn(`NPC with ID ${id} not found in fetched list from /api/npcs.`);
                }
            });
            
            if (sceneParticipants.length === 0) {
                if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'Could not load details for any of the selected NPCs.';
                else if(npcInteractionArea) npcInteractionArea.innerHTML = '<p>Could not load details for any of the selected NPCs.</p>';
                startSceneButton.disabled = true;
            } else {
                if(loadingNpcsMessage) loadingNpcsMessage.remove(); // Remove "Loading..." message
                createNpcInteractionInterfaces();
            }
        })
        .catch(error => {
            console.error('Error fetching NPC details for scene:', error);
            if(loadingNpcsMessage) loadingNpcsMessage.textContent = `Error loading NPC details: ${error.message}. Check console.`;
            else if(npcInteractionArea) npcInteractionArea.innerHTML = `<p>Error loading NPC details: ${error.message}. Check console.</p>`;
            startSceneButton.disabled = true;
        });

    /**
     * Creates the individual UI (chat box, controls) for each selected NPC.
     */
    function createNpcInteractionInterfaces() {
        npcInteractionArea.innerHTML = ''; // Clear previous content or loading messages

        sceneParticipants.forEach(npc => {
            const npcContainer = document.createElement('div');
            npcContainer.className = 'npc-dialogue-container';
            npcContainer.dataset.npcId = npc._id; 

            const npcInitials = npc.name ? npc.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC_bg");
            const portraitUrl = `https://placehold.co/50x50/${placeholderBgColor}/FFFFFF?text=${npcInitials}&font=source-sans-pro`;

            npcContainer.innerHTML = `
                <div class="npc-header">
                    <img src="${portraitUrl}" alt="Portrait of ${npc.name}" class="npc-header-portrait" onerror="this.style.display='none';">
                    <h3 class="npc-header-name">${npc.name || 'Unknown NPC'}</h3>
                </div>
                <div class="npc-chat-log" id="chat-log-${npc._id}">
                    <p class="log-placeholder">Awaiting interaction...</p>
                </div>
                <div class="npc-dialogue-controls">
                    <button class="jrpg-button-small btn-submit-memory" data-npc-id="${npc._id}" title="Commit last exchange to ${npc.name}'s memory (simulated)">To Memory</button>
                    <button class="jrpg-button-small btn-undo-memory" data-npc-id="${npc._id}" title="Undo last memory submission for ${npc.name} (simulated)">Undo Mem</button>
                    <button class="jrpg-button-small btn-next-topic" data-npc-id="${npc._id}" title="Advance ${npc.name} to the next generated topic">Next Topic</button>
                    <button class="jrpg-button-small btn-regen-topics" data-npc-id="${npc._id}" title="Generate new conversation topics for ${npc.name}">Regen Topics</button>
                    <button class="jrpg-button-small btn-show-top5" data-npc-id="${npc._id}" title="Show top 5 dialogue options for ${npc.name}">Top 5</button>
                    <button class="jrpg-button-small btn-show-tree" data-npc-id="${npc._id}" title="Show conversation tree for ${npc.name} (future)">Tree</button>
                </div>
            `;
            npcInteractionArea.appendChild(npcContainer);
        });
        addControlEventListeners(); // Add listeners after controls are in the DOM
    }
    
    /**
     * Adds event listeners to all dialogue control buttons using event delegation.
     */
    function addControlEventListeners() {
        // Add listener to the common ancestor of all NPC interaction areas
        npcInteractionArea.addEventListener('click', function(event) {
            const button = event.target.closest('.jrpg-button-small'); // Find the button if clicked on icon/text within it
            if (button && button.dataset.npcId) { // Check if it's a button with an npcId
                const npcId = button.dataset.npcId;
                // Try to get a more reliable action identifier, e.g., from a class or data-action attribute
                let action = "Unknown Action";
                if (button.classList.contains('btn-submit-memory')) action = "Submit to Memory";
                else if (button.classList.contains('btn-undo-memory')) action = "Undo Memory";
                else if (button.classList.contains('btn-next-topic')) action = "Next Topic";
                else if (button.classList.contains('btn-regen-topics')) action = "Regenerate Topics";
                else if (button.classList.contains('btn-show-top5')) action = "Show Top 5";
                else if (button.classList.contains('btn-show-tree')) action = "Show Tree";
                else action = button.textContent.trim(); // Fallback to text content
                
                const npc = sceneParticipants.find(p => p._id === npcId);
                
                if (npc) {
                    handleControlButtonClick(npc, action, button);
                } else {
                    console.warn(`Could not find NPC data for ID: ${npcId} on button click.`);
                }
            }
        });
    }
    
    /**
     * Handles clicks on the per-NPC dialogue control buttons.
     * @param {Object} npc - The NPC object associated with the button.
     * @param {string} action - The action identified for the button.
     * @param {HTMLElement} buttonElement - The button element that was clicked.
     */
    function handleControlButtonClick(npc, action, buttonElement) {
        alert(`Control '${action}' clicked for ${npc.name}. (NPC ID: ${npc._id}). This feature is not yet implemented.`);
        console.log("Button clicked:", { npcName: npc.name, npcId: npc._id, action: action, button: buttonElement });
        // TODO: Implement logic for each button.
    }

    /**
     * Handles the "Initiate Scene / Narrate" button click.
     */
    startSceneButton.addEventListener('click', () => {
        const sceneDescription = sceneDescriptionTextarea.value.trim();
        if (sceneParticipants.length === 0) {
            alert('No NPCs are currently part of the scene.');
            return;
        }
        if (!sceneDescription) {
            alert('Please describe the scene or provide narration before initiating.');
            sceneDescriptionTextarea.focus();
            return;
        }

        currentSceneDescriptionDisplay.textContent = `Current Scene: ${sceneDescription}`;
        
        sceneParticipants.forEach(npc => {
            const logContainer = document.getElementById(`chat-log-${npc._id}`);
            if (logContainer) {
                const placeholder = logContainer.querySelector('.log-placeholder');
                if (placeholder) placeholder.remove();
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Scene context updated by GM: "${sceneDescription.substring(0,70)}..."`, "system");
            }
        });

        sceneParticipants.forEach((npc, index) => {
            setTimeout(() => { 
                const aiGeneratedLine = `I am ${npc.name}. I acknowledge the scene: "${sceneDescription.substring(0, 25)}...". What happens next?`;
                addDialogueEntryToNpcLog(npc._id, npc.name, aiGeneratedLine, "npc");
                // displayDialogueOptionsForNpc(npc._id, [`${npc.name} says: Option 1`, `${npc.name} ponders: Option 2`]);
            }, index * 600 + 300); 
        });
        
        sceneDescriptionTextarea.value = ""; 
    });

    /**
     * Adds a dialogue entry to a specific NPC's chat log.
     * @param {string} npcId - The ID of the NPC whose log to update.
     * @param {string} speakerName - The name of the speaker (NPC name, "GM", "SYSTEM").
     * @param {string} text - The dialogue text.
     * @param {string} type - 'npc', 'gm', 'system'.
     */
    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc") {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer) {
            console.error(`Chat log container for NPC ID ${npcId} not found! Cannot add entry: "${text}"`);
            return;
        }

        const entryDiv = document.createElement('div');
        entryDiv.classList.add('chat-entry', type); 
        
        let bubbleHtml = `<div class="chat-bubble">`;
        if (type !== "npc") { 
            bubbleHtml += `<span class="speaker-name">${speakerName}</span>`;
        }
        bubbleHtml += `<p class="dialogue-text">${text.replace(/\n/g, '<br>')}</p>`;
        bubbleHtml += `</div>`;
        entryDiv.innerHTML = bubbleHtml;

        logContainer.appendChild(entryDiv);
        logContainer.scrollTop = logContainer.scrollHeight; 
    }
    
    /**
     * Placeholder: Displays multiple choice dialogue options for a specific NPC.
     * @param {string} npcId - The ID of the NPC.
     * @param {Array<string>} options - An array of dialogue option strings.
     */
    function displayDialogueOptionsForNpc(npcId, options) {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer || !options || options.length === 0) return;

        const existingOptions = logContainer.querySelector('.dialogue-options');
        if(existingOptions) existingOptions.remove();

        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'dialogue-options'; 
        options.forEach(optionText => {
            const optionButton = document.createElement('button');
            optionButton.className = 'jrpg-button-small dialogue-option'; 
            optionButton.textContent = optionText;
            optionButton.addEventListener('click', () => {
                addDialogueEntryToNpcLog(npcId, "GM Choice", `Selected: "${optionText}"`, "gm");
                optionsContainer.remove();
                alert(`GM selected: "${optionText}" for NPC ID ${npcId}. (Dialogue continuation not implemented)`);
            });
            optionsContainer.appendChild(optionButton);
        });
        logContainer.appendChild(optionsContainer);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    /**
     * Generates a hex color code from a string for placeholder images.
     * @param {string} str - The input string.
     * @returns {string} A hex color code without the '#'.
     */
    function stringToColor(str) {
        let hash = 0;
        if (!str || str.length === 0) return 'CCCCCC'; 
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash; 
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }
});
