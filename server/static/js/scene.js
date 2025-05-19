// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const npcInteractionArea = document.getElementById('npc-interaction-area');
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const startSceneButton = document.getElementById('start-scene-button');
    const currentSceneDescriptionDisplay = document.getElementById('current-scene-description-display');
    let loadingNpcsMessage = npcInteractionArea ? npcInteractionArea.querySelector('.loading-npcs-message') : null;

    // --- State Variables ---
    let sceneParticipants = []; // Stores full NPC objects for the current scene
    let conversationHistory = {}; // Object to store conversation history per NPC: { npcId: [{speaker, text}, ...] }

    // --- Initial Error Checks ---
    if (!npcInteractionArea || !sceneDescriptionTextarea || !startSceneButton || !currentSceneDescriptionDisplay) {
        console.error('CRITICAL: One or more essential UI elements for the scene page are missing from scene.html!');
        if(npcInteractionArea) npcInteractionArea.innerHTML = '<p style="color:red; text-align:center;">Error: UI setup incomplete.</p>';
        return;
    }
    if (!loadingNpcsMessage && npcInteractionArea) {
        loadingNpcsMessage = npcInteractionArea.querySelector('.loading-npcs-message');
    }

    // --- Get Selected NPCs from URL ---
    const urlParams = new URLSearchParams(window.location.search);
    const npcIdsParam = urlParams.get('npcs');
    const selectedNpcIds = npcIdsParam ? npcIdsParam.split(',') : [];

    if (selectedNpcIds.length === 0) {
        if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'No NPCs selected. Please go back.';
        else if(npcInteractionArea) npcInteractionArea.innerHTML = '<p>No NPCs selected. Please go back.</p>';
        startSceneButton.disabled = true;
        return;
    }

    // --- Fetch NPC Data and Initialize UI ---
    fetch('/api/npcs')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error fetching NPC list! Status: ${response.status} ${response.statusText}`);
            return response.json();
        })
        .then(allNpcs => {
            selectedNpcIds.forEach(id => {
                const npc = allNpcs.find(n => n._id === id);
                if (npc) {
                    sceneParticipants.push(npc);
                    conversationHistory[npc._id] = []; // Initialize history for each participant
                } else {
                    console.warn(`NPC with ID ${id} not found in fetched list from /api/npcs.`);
                }
            });
            
            if (sceneParticipants.length === 0) {
                if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'Could not load details for selected NPCs.';
                startSceneButton.disabled = true;
            } else {
                if(loadingNpcsMessage) loadingNpcsMessage.remove();
                createNpcInteractionInterfaces();
            }
        })
        .catch(error => {
            console.error('Error fetching NPC details for scene:', error);
            if(loadingNpcsMessage) loadingNpcsMessage.textContent = `Error loading NPC details: ${error.message}.`;
            startSceneButton.disabled = true;
        });

    function createNpcInteractionInterfaces() {
        npcInteractionArea.innerHTML = '';
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
        addControlEventListeners();
    }
    
    function addControlEventListeners() {
        npcInteractionArea.addEventListener('click', function(event) {
            const button = event.target.closest('.jrpg-button-small');
            if (button && button.dataset.npcId) {
                const npcId = button.dataset.npcId;
                let action = "Unknown Action";
                if (button.classList.contains('btn-submit-memory')) action = "Submit to Memory";
                else if (button.classList.contains('btn-undo-memory')) action = "Undo Memory";
                else action = button.textContent.trim();
                
                const npc = sceneParticipants.find(p => p._id === npcId);
                if (npc) handleControlButtonClick(npc, action, button);
            }
        });
    }
    
    function handleControlButtonClick(npc, action, buttonElement) {
        alert(`Control '${action}' for ${npc.name} (ID: ${npc._id}) is not fully implemented.`);
        console.log("Button clicked:", { npcName: npc.name, npcId: npc._id, action: action });
    }

    startSceneButton.addEventListener('click', () => {
        const sceneDescription = sceneDescriptionTextarea.value.trim();
        if (sceneParticipants.length === 0) {
            alert('No NPCs in scene.');
            return;
        }
        if (!sceneDescription) {
            alert('Please describe the scene.');
            sceneDescriptionTextarea.focus();
            return;
        }

        currentSceneDescriptionDisplay.textContent = `Current Scene: ${sceneDescription}`;
        
        sceneParticipants.forEach(npc => {
            const logContainer = document.getElementById(`chat-log-${npc._id}`);
            if (logContainer) {
                logContainer.innerHTML = ''; 
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Scene context: "${sceneDescription.substring(0,100)}..."`, "system");
                // Initialize or update conversation history for this NPC
                conversationHistory[npc._id] = [{ speaker: "SYSTEM", text: `Scene context: "${sceneDescription}"` }]; 
            }
        });

        // --- Trigger AI Dialogue Generation for each NPC ---
        sceneParticipants.forEach((npc, index) => {
            addDialogueEntryToNpcLog(npc._id, npc.name, "<i>...pondering the situation...</i>", "npc-thinking"); // Show thinking message

            setTimeout(() => { // Stagger API calls slightly
                console.log(`Fetching dialogue for ${npc.name} (ID: ${npc._id}) with scene: "${sceneDescription}"`); // DEBUG LOG
                fetchNpcDialogue(npc, sceneDescription);
            }, index * 700 + 400); 
        });
        
        sceneDescriptionTextarea.value = ""; 
    });

    /**
     * Fetches AI-generated dialogue for a specific NPC.
     * @param {Object} npc - The NPC object.
     * @param {string} currentSceneDescription - The GM's description of the scene.
     */
    async function fetchNpcDialogue(npc, currentSceneDescription) {
        const npcId = npc._id;
        const npcLogContainer = document.getElementById(`chat-log-${npcId}`);
        
        // Remove "thinking" message if it exists
        if (npcLogContainer) {
            const thinkingMessageEntry = npcLogContainer.querySelector('.chat-entry.npc-thinking');
            if(thinkingMessageEntry) {
                thinkingMessageEntry.remove();
            }
        }

        try {
            const payload = {
                npc_id: npc._id,
                scene_context: currentSceneDescription,
                history: conversationHistory[npcId] ? conversationHistory[npcId].slice(-5) : [] 
            };
            console.log(`Payload for ${npc.name}:`, JSON.stringify(payload)); // DEBUG LOG

            const response = await fetch('/api/dialogue/generate_npc_line', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                let errorDetail = "Failed to fetch dialogue line.";
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorData.error || `Server responded with status ${response.status}`;
                } catch (e) {
                    errorDetail = `Server responded with status ${response.status} and non-JSON error.`;
                }
                throw new Error(errorDetail);
            }

            const data = await response.json(); 

            if (data.dialogue_text) {
                addDialogueEntryToNpcLog(npcId, npc.name, data.dialogue_text, "npc");
                conversationHistory[npcId].push({ speaker: npc.name, text: data.dialogue_text });
            } else {
                addDialogueEntryToNpcLog(npcId, "SYSTEM", "AI could not generate a response for " + npc.name, "system-error");
            }

        } catch (error) {
            console.error(`Error fetching dialogue for ${npc.name} (ID: ${npcId}):`, error);
            addDialogueEntryToNpcLog(npcId, "SYSTEM", `Error for ${npc.name}: ${error.message}`, "system-error");
        }
    }

    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc") {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer) {
            console.error(`Chat log for NPC ID ${npcId} not found! Cannot add: "${text}"`);
            return;
        }

        const entryDiv = document.createElement('div');
        entryDiv.classList.add('chat-entry', type); 
        
        let bubbleHtml = `<div class="chat-bubble">`;
        if (type !== "npc" || type === "npc-thinking") { 
            bubbleHtml += `<span class="speaker-name">${speakerName}</span>`;
        }
        // Basic text sanitization for display (replace with a proper library if handling complex user input)
        const sanitizedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        bubbleHtml += `<p class="dialogue-text">${sanitizedText.replace(/\n/g, '<br>')}</p>`;
        bubbleHtml += `</div>`;
        entryDiv.innerHTML = bubbleHtml;

        logContainer.appendChild(entryDiv);
        logContainer.scrollTop = logContainer.scrollHeight; 
    }
    
    function stringToColor(str) { /* ... (implementation as before) ... */ }
});
