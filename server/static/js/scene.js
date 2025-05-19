// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const npcInteractionArea = document.getElementById('npc-interaction-area');
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const startSceneButton = document.getElementById('start-scene-button'); // From scene.html
    const currentSceneDescriptionDisplay = document.getElementById('current-scene-description-display');
    let loadingNpcsMessage = npcInteractionArea ? npcInteractionArea.querySelector('.loading-npcs-message') : null;

    // --- State Variables ---
    let sceneParticipants = []; // Stores full NPC objects for the current scene
    let conversationHistory = {}; // Object to store conversation history per NPC: { npcId: [{speaker, text}, ...] }
    let currentSceneContext = ""; // Store the latest scene description globally for this page

    // --- Initial Error Checks for Essential Elements ---
    if (!npcInteractionArea || !sceneDescriptionTextarea || !startSceneButton || !currentSceneDescriptionDisplay) {
        console.error('CRITICAL: One or more essential UI elements for the scene page are missing from scene.html!');
        if(npcInteractionArea) {
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
                    conversationHistory[npc._id] = []; // Initialize history for each participant
                } else {
                    console.warn(`NPC with ID ${id} not found in fetched list from /api/npcs.`);
                }
            });
            
            if (sceneParticipants.length === 0) {
                if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'Could not load details for any of the selected NPCs.';
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
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC_bg"); // Ensure unique color
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
                    <button class="jrpg-button-small btn-submit-memory" data-action="submit_memory" data-npc-id="${npc._id}" title="Commit last exchange to ${npc.name}'s memory">To Memory</button>
                    <button class="jrpg-button-small btn-undo-memory" data-action="undo_memory" data-npc-id="${npc._id}" title="Undo last memory submission for ${npc.name}">Undo Mem</button>
                    <button class="jrpg-button-small btn-next-topic" data-action="next_topic" data-npc-id="${npc._id}" title="Advance ${npc.name} to the next generated topic">Next Topic</button>
                    <button class="jrpg-button-small btn-regen-topics" data-action="regenerate_topics" data-npc-id="${npc._id}" title="Generate new conversation topics for ${npc.name}">Regen Topics</button>
                    <button class="jrpg-button-small btn-show-top5" data-action="show_top5_options" data-npc-id="${npc._id}" title="Show top 5 dialogue options for ${npc.name}">Top 5</button>
                    <button class="jrpg-button-small btn-show-tree" data-action="show_tree" data-npc-id="${npc._id}" title="Show conversation tree for ${npc.name} (future)">Tree</button>
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
            const button = event.target.closest('.jrpg-button-small[data-action]'); // Find the button if clicked on icon/text within it
            if (button) { // Check if a button with data-action was clicked
                const npcId = button.dataset.npcId;
                const actionType = button.dataset.action; // Get action from data-action attribute
                const npc = sceneParticipants.find(p => p._id === npcId);
                
                if (npc) {
                    handleNpcSpecificAction(npc, actionType, button);
                } else {
                    console.warn(`Could not find NPC data for ID: ${npcId} on button click for action: ${actionType}.`);
                }
            }
        });
    }
    
    /**
     * Handles clicks on the per-NPC dialogue control buttons by calling a backend action.
     * @param {Object} npc - The NPC object associated with the button.
     * @param {string} actionType - The type of action to perform (e.g., "submit_memory", "next_topic").
     * @param {HTMLElement} buttonElement - The button element that was clicked.
     */
    async function handleNpcSpecificAction(npc, actionType, buttonElement) {
        console.log(`Action '${actionType}' triggered for ${npc.name} (ID: ${npc._id})`);
        addDialogueEntryToNpcLog(npc._id, "GM Action", `GM triggered: ${actionType} for ${npc.name}`, "system-info");

        let payload = {}; // Action-specific data to send to backend
        if (actionType === "submit_memory") {
            const historyForMemory = conversationHistory[npc._id] ? conversationHistory[npc._id].slice(-2) : []; 
            if (historyForMemory.length === 0) {
                alert(`No recent dialogue to submit to memory for ${npc.name}.`);
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `No recent dialogue for memory submission.`, "system-error");
                return;
            }
            // Send as a single string or structured data as your backend expects
            payload.dialogue_exchange = historyForMemory.map(entry => `${entry.speaker}: ${entry.text}`).join('\n');
        }
        // For other actions, the backend might just need npc_id, current scene, and history.

        try {
            if (buttonElement) buttonElement.disabled = true; // Disable button while processing

            const apiPayload = {
                npc_id: npc._id,
                action_type: actionType,
                payload: payload, 
                scene_description: currentSceneContext, 
                history: conversationHistory[npc._id] ? conversationHistory[npc._id].slice(-5) : [] 
            };
            console.log(`Sending payload for action '${actionType}' for ${npc.name}:`, apiPayload);


            const response = await fetch('/api/dialogue/npc_action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(apiPayload)
            });

            if (buttonElement) buttonElement.disabled = false; // Re-enable button

            const responseData = await response.json();

            if (!response.ok) {
                throw new Error(responseData.error || responseData.message || `Action '${actionType}' failed with status ${response.status}`);
            }

            // Handle response based on action
            let systemMessage = `Action '${actionType}' for ${npc.name} processed.`;
            if (responseData.message) {
                systemMessage = responseData.message;
            }
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", systemMessage, "system-success");


            if (responseData.data) {
                if (responseData.action === "next_topic" || responseData.action === "regenerate_topics") {
                    if (responseData.data.new_topics && responseData.data.new_topics.length > 0) {
                        const topicsMessage = "Suggested Topics:\n- " + responseData.data.new_topics.join("\n- ");
                        addDialogueEntryToNpcLog(npc._id, "AI Topics", topicsMessage, "system-info");
                        displayDialogueOptionsForNpc(npc._id, responseData.data.new_topics, "Suggested Topics (click to use as input):");
                    } else {
                        addDialogueEntryToNpcLog(npc._id, "SYSTEM", "No new topics were generated.", "system-info");
                    }
                } else if (responseData.action === "show_top5_options") {
                     if (responseData.data.dialogue_options && responseData.data.dialogue_options.length > 0) {
                        displayDialogueOptionsForNpc(npc._id, responseData.data.dialogue_options, "AI Suggested Next Lines (click to make NPC say):");
                     } else {
                        addDialogueEntryToNpcLog(npc._id, "SYSTEM", "No dialogue options were generated.", "system-info");
                     }
                }
            }

        } catch (error) {
            console.error(`Error during NPC action '${actionType}' for ${npc.name}:`, error);
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Error with action '${actionType}': ${error.message}`, "system-error");
            if(buttonElement) buttonElement.disabled = false;
        }
    }

    /**
     * Handles the "Initiate Scene / Narrate" button click.
     */
    startSceneButton.addEventListener('click', () => {
        const sceneDescriptionInput = sceneDescriptionTextarea.value.trim();
        if (sceneParticipants.length === 0) {
            alert('No NPCs are currently part of the scene.'); return;
        }
        if (!sceneDescriptionInput) {
            alert('Please describe the scene or provide narration before initiating.'); 
            sceneDescriptionTextarea.focus(); 
            return;
        }

        currentSceneContext = sceneDescriptionInput; // Store current scene context
        currentSceneDescriptionDisplay.textContent = `Current Scene: ${currentSceneContext}`;
        
        // Clear previous logs and add system message to each NPC's log
        sceneParticipants.forEach(npc => {
            const logContainer = document.getElementById(`chat-log-${npc._id}`);
            if (logContainer) {
                logContainer.innerHTML = ''; // Clear previous messages from this log
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Scene context: "${currentSceneContext.substring(0,100)}..."`, "system");
                // Initialize or update conversation history for this NPC
                conversationHistory[npc._id] = [{ speaker: "SYSTEM", text: `Scene context: "${currentSceneContext}"` }]; 
            }
        });

        // --- Trigger AI Dialogue Generation for each NPC ---
        sceneParticipants.forEach((npc, index) => {
            addDialogueEntryToNpcLog(npc._id, npc.name, "<i>...formulating a response...</i>", "npc-thinking"); 
            setTimeout(() => { // Stagger API calls slightly
                console.log(`Fetching initial dialogue for ${npc.name} (ID: ${npc._id}) with scene: "${currentSceneContext}"`);
                fetchNpcInitialDialogue(npc, currentSceneContext); // Pass the stored currentSceneContext
            }, index * 700 + 400); // Stagger initial responses
        });
        
        sceneDescriptionTextarea.value = ""; // Clear textarea for next narration/input
    });

    /**
     * Fetches AI-generated dialogue for a specific NPC when the scene starts or context changes.
     * @param {Object} npc - The NPC object.
     * @param {string} sceneDescForCall - The scene description to send for this specific call.
     */
    async function fetchNpcInitialDialogue(npc, sceneDescForCall) {
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
                scene_context: sceneDescForCall, 
                history: conversationHistory[npcId] ? conversationHistory[npcId].slice(-5) : [] 
            };
            console.log(`Payload for initial line for ${npc.name}:`, JSON.stringify(payload));

            const response = await fetch('/api/dialogue/generate_npc_line', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                let errorDetail = "Failed to fetch initial dialogue.";
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorData.error || `Server responded with status ${response.status}`;
                } catch (e) { errorDetail = `Server responded with status ${response.status} and non-JSON error.`; }
                throw new Error(errorDetail);
            }

            const data = await response.json(); 
            if (data.dialogue_text) {
                addDialogueEntryToNpcLog(npcId, npc.name, data.dialogue_text, "npc");
                // Add AI's response to this NPC's history
                conversationHistory[npcId].push({ speaker: npc.name, text: data.dialogue_text });
            } else {
                addDialogueEntryToNpcLog(npcId, "SYSTEM", "AI could not generate an initial response for " + npc.name, "system-error");
            }
        } catch (error) {
            console.error(`Error fetching initial dialogue for ${npc.name} (ID: ${npcId}):`, error);
            addDialogueEntryToNpcLog(npcId, "SYSTEM", `Error for ${npc.name}: ${error.message}`, "system-error");
        }
    }

    /**
     * Adds a dialogue entry to a specific NPC's chat log.
     * @param {string} npcId - The ID of the NPC whose log to update.
     * @param {string} speakerName - The name of the speaker (NPC name, "GM", "SYSTEM").
     * @param {string} text - The dialogue text.
     * @param {string} type - 'npc', 'gm', 'system', 'system-info', 'system-error', 'system-success', 'npc-thinking'.
     */
    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc") {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer) {
            console.error(`Chat log container for NPC ID ${npcId} not found! Cannot add entry: "${text}"`);
            return;
        }

        const entryDiv = document.createElement('div');
        // Add specific class for system messages for styling if needed
        const typeClass = type.startsWith('system') ? 'system-message' : type; // e.g. system-message, system-error
        entryDiv.classList.add('chat-entry', typeClass); 
        
        let bubbleHtml = `<div class="chat-bubble">`;
        // Show speaker name if it's not the primary NPC of this chat log OR if it's a special type like 'npc-thinking' or system messages
        if (type !== "npc" || type === "npc-thinking" || type.startsWith("system")) { 
            bubbleHtml += `<span class="speaker-name">${speakerName}</span>`;
        }
        // Basic text sanitization for display (replace with a proper library if handling complex user input)
        const sanitizedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        bubbleHtml += `<p class="dialogue-text">${sanitizedText.replace(/\n/g, '<br>')}</p>`;
        bubbleHtml += `</div>`;
        entryDiv.innerHTML = bubbleHtml;

        logContainer.appendChild(entryDiv);
        logContainer.scrollTop = logContainer.scrollHeight; // Auto-scroll to the latest message
    }
    
    /**
     * Placeholder: Displays multiple choice dialogue options for a specific NPC.
     * @param {string} npcId - The ID of the NPC.
     * @param {Array<string>} options - An array of dialogue option strings.
     * @param {string} title - A title for the options block.
     */
    function displayDialogueOptionsForNpc(npcId, options, title = "Suggested Options:") {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer || !options || options.length === 0) return;

        const existingOptions = logContainer.querySelector('.dialogue-options-container');
        if(existingOptions) existingOptions.remove(); // Remove old options if any

        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'dialogue-options-container'; // Style this class in scene.css
        
        const titleElement = document.createElement('p');
        titleElement.className = 'dialogue-options-title'; // Style this
        titleElement.textContent = title;
        optionsContainer.appendChild(titleElement);

        options.forEach(optionText => {
            const optionButton = document.createElement('button');
            optionButton.className = 'jrpg-button-small dialogue-option'; // Add specific class for styling
            optionButton.textContent = optionText;
            optionButton.addEventListener('click', () => {
                // Log the GM's choice
                addDialogueEntryToNpcLog(npcId, "GM Choice", `Selected: "${optionText}"`, "gm");
                
                // Option 1: Make the NPC say the selected line (if options are direct dialogue)
                // const npcToSpeak = sceneParticipants.find(p=>p._id === npcId);
                // if(npcToSpeak) {
                //     addDialogueEntryToNpcLog(npcId, npcToSpeak.name, optionText, "npc");
                //     conversationHistory[npcId].push({ speaker: npcToSpeak.name, text: optionText });
                // }

                // Option 2: Use the selected option as new input for this NPC to respond to (if options are topics/questions)
                const npcToRespond = sceneParticipants.find(p => p._id === npcId);
                if (npcToRespond) {
                    addDialogueEntryToNpcLog(npcId, npcToRespond.name, `<i>...reacting to GM's choice: "${optionText.substring(0,30)}..."</i>`, "npc-thinking");
                    // The 'optionText' becomes the new 'scene_context' for this specific NPC's next line
                    fetchNpcInitialDialogue(npcToRespond, optionText); 
                }
                
                optionsContainer.remove(); // Remove options after selection
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
        if (!str || str.length === 0) return 'CCCCCC'; // Default color for empty string
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash; // Convert to 32bit integer
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }
});
