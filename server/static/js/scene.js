// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const npcInteractionArea = document.getElementById('npc-interaction-area');
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const startSceneButton = document.getElementById('start-scene-button'); 
    const currentSceneDescriptionDisplay = document.getElementById('current-scene-description-display');
    let loadingNpcsMessage = npcInteractionArea ? npcInteractionArea.querySelector('.loading-npcs-message') : null;

    // --- State Variables ---
    let sceneParticipants = []; 
    let conversationHistory = {}; 
    let currentSceneContext = ""; 

    // --- Helper Function to Escape HTML ---
    function escapeForHtml(unsafe) {
        if (unsafe === null || typeof unsafe === 'undefined') {
            return '';
        }
        return unsafe
             .toString()
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;")
             .replace(/`/g, "&#96;"); 
    }

    if (!npcInteractionArea || !sceneDescriptionTextarea || !startSceneButton || !currentSceneDescriptionDisplay) {
        console.error('CRITICAL: One or more essential UI elements for the scene page are missing from scene.html!');
        if(npcInteractionArea) {
            npcInteractionArea.innerHTML = '<p style="color:red; text-align:center;">Error: UI setup incomplete. Please check console and HTML structure.</p>';
        }
        return;
    }
    if (!loadingNpcsMessage && npcInteractionArea) {
        loadingNpcsMessage = npcInteractionArea.querySelector('.loading-npcs-message');
    }

    const urlParams = new URLSearchParams(window.location.search);
    const npcIdsParam = urlParams.get('npcs');
    const selectedNpcIds = npcIdsParam ? npcIdsParam.split(',') : [];

    if (selectedNpcIds.length === 0) {
        if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'No NPCs were selected for this scene. Please go back to NPC selection.';
        else if(npcInteractionArea) npcInteractionArea.innerHTML = '<p>No NPCs were selected for this scene. Please go back to NPC selection.</p>';
        startSceneButton.disabled = true;
        return;
    }

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
                    conversationHistory[npc._id] = []; 
                } else {
                    console.warn(`NPC with ID ${id} not found in fetched list from /api/npcs.`);
                }
            });
            
            if (sceneParticipants.length === 0) {
                if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'Could not load details for any of the selected NPCs.';
                startSceneButton.disabled = true;
            } else {
                if(loadingNpcsMessage) loadingNpcsMessage.remove(); 
                createNpcInteractionInterfaces();
            }
        })
        .catch(error => {
            console.error('Error fetching NPC details for scene:', error);
            if(loadingNpcsMessage) loadingNpcsMessage.textContent = `Error loading NPC details: ${error.message}. Check console.`;
            else if(npcInteractionArea) npcInteractionArea.innerHTML = `<p>Error loading NPC details: ${error.message}. Check console.</p>`;
            startSceneButton.disabled = true;
        });

    function createNpcInteractionInterfaces() {
        npcInteractionArea.innerHTML = ''; // Clear previous content

        sceneParticipants.forEach(npc => {
            const npcContainer = document.createElement('div');
            npcContainer.className = 'npc-dialogue-container';
            npcContainer.dataset.npcId = npc._id; // Original ID for lookups

            const npcNameDisplay = npc.name || 'Unknown NPC';
            const npcIdHtml = npc._id; // Original ID for data attributes, DOM handles it.

            const npcInitials = npc.name ? npc.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC_bg");
            const portraitUrl = `https://placehold.co/50x50/${placeholderBgColor}/FFFFFF?text=${encodeURIComponent(npcInitials)}&font=source-sans-pro`;

            // NPC Header
            const npcHeaderDiv = document.createElement('div');
            npcHeaderDiv.className = 'npc-header';

            const portraitImg = document.createElement('img');
            portraitImg.src = portraitUrl;
            portraitImg.alt = `Portrait of ${npcNameDisplay}`; // Text content, browser handles rendering
            portraitImg.className = 'npc-header-portrait';
            portraitImg.onerror = function() { this.style.display='none'; };
            npcHeaderDiv.appendChild(portraitImg);

            const npcNameH3 = document.createElement('h3');
            npcNameH3.className = 'npc-header-name';
            npcNameH3.textContent = npcNameDisplay;
            npcHeaderDiv.appendChild(npcNameH3);
            npcContainer.appendChild(npcHeaderDiv);

            // Chat Log
            const chatLogDiv = document.createElement('div');
            chatLogDiv.className = 'npc-chat-log';
            chatLogDiv.id = `chat-log-${npcIdHtml}`; // Use original ID for targeting
            const logPlaceholderP = document.createElement('p');
            logPlaceholderP.className = 'log-placeholder';
            logPlaceholderP.textContent = 'Awaiting interaction...';
            chatLogDiv.appendChild(logPlaceholderP);
            npcContainer.appendChild(chatLogDiv);

            // Dialogue Controls
            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'npc-dialogue-controls';

            const controlButtonData = [
                { action: "submit_memory", title: `Commit last exchange to ${npcNameDisplay}'s memory`, text: "To Memory" },
                { action: "undo_memory", title: `Undo last memory submission for ${npcNameDisplay}`, text: "Undo Mem" },
                { action: "next_topic", title: `Advance ${npcNameDisplay} to the next generated topic`, text: "Next Topic" },
                { action: "regenerate_topics", title: `Generate new conversation topics for ${npcNameDisplay}`, text: "Regen Topics" },
                { action: "show_top5_options", title: `Show top 5 dialogue options for ${npcNameDisplay}`, text: "Top 5" },
                { action: "show_tree", title: `Show conversation tree for ${npcNameDisplay} (future)`, text: "Tree" }
            ];

            controlButtonData.forEach(btnData => {
                const button = document.createElement('button');
                button.className = 'jrpg-button-small'; // Main class
                button.classList.add(`btn-${btnData.action.replace('_', '-')}`); // Specific class if needed
                button.dataset.action = btnData.action;
                button.dataset.npcId = npcIdHtml; // Use original ID
                button.title = btnData.title; // Browsers handle attribute escaping well
                button.textContent = btnData.text;
                controlsDiv.appendChild(button);
            });
            npcContainer.appendChild(controlsDiv);
            npcInteractionArea.appendChild(npcContainer);
        });
        addControlEventListeners(); 
    }
    
    function addControlEventListeners() {
        npcInteractionArea.addEventListener('click', function(event) {
            const button = event.target.closest('.jrpg-button-small[data-action]'); 
            if (button) { 
                const npcId = button.dataset.npcId;
                const actionType = button.dataset.action; 
                const npc = sceneParticipants.find(p => p._id === npcId);
                
                if (npc) {
                    handleNpcSpecificAction(npc, actionType, button);
                } else {
                    console.warn(`Could not find NPC data for ID: ${escapeForHtml(npcId)} on button click for action: ${escapeForHtml(actionType)}.`);
                }
            }
        });
    }
    
    async function handleNpcSpecificAction(npc, actionType, buttonElement) {
        const npcNameSafe = escapeForHtml(npc.name); // For display in logs/messages
        console.log(`Action '${actionType}' triggered for ${npcNameSafe} (ID: ${npc._id})`);
        addDialogueEntryToNpcLog(npc._id, "GM Action", `GM triggered: ${escapeForHtml(actionType)} for ${npcNameSafe}`, "system-info");

        let payloadSpecifics = {}; 
        if (actionType === "submit_memory") {
            const historyForNpc = conversationHistory[npc._id] || [];
            let relevantExchange = [];
            if (historyForNpc.length > 0) {
                const lastEntry = historyForNpc[historyForNpc.length - 1];
                if (lastEntry.speaker === npc.name && historyForNpc.length > 1) {
                    const secondLastEntry = historyForNpc[historyForNpc.length - 2];
                    if (secondLastEntry.speaker !== npc.name && secondLastEntry.speaker !== "GM Action") { 
                        relevantExchange.push(secondLastEntry); 
                    }
                    relevantExchange.push(lastEntry); 
                } else if (lastEntry.speaker !== npc.name && lastEntry.speaker !== "GM Action" && historyForNpc.length > 1){
                    const secondLastEntry = historyForNpc[historyForNpc.length - 2];
                    if(secondLastEntry.speaker === npc.name){ 
                        relevantExchange.push(lastEntry); 
                        relevantExchange.push(secondLastEntry); 
                        relevantExchange.reverse(); 
                    } else {
                         relevantExchange = historyForNpc.slice(-2).filter(e => e.speaker !== "GM Action");
                    }
                } else if (lastEntry.speaker !== "GM Action") { 
                     relevantExchange.push(lastEntry);
                }
            }
            if (relevantExchange.length > 2) relevantExchange = relevantExchange.slice(-2);
            if (relevantExchange.length === 0) {
                alert(`No recent dialogue to submit to memory for ${npcNameSafe}.`);
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `No recent dialogue for memory submission.`, "system-error");
                return;
            }
            payloadSpecifics.dialogue_exchange = relevantExchange.map(entry => `${entry.speaker}: ${entry.text}`).join('\n');
            payloadSpecifics.scene_context_for_memory = currentSceneContext; 
        }
        
        try {
            if (buttonElement) buttonElement.disabled = true; 
            const apiPayload = {
                npc_id: npc._id, action_type: actionType, payload: payloadSpecifics, 
                scene_description: currentSceneContext, 
                history: conversationHistory[npc._id] ? conversationHistory[npc._id].slice(-10) : [] 
            };
            // console.log(`Sending payload for action '${actionType}' for ${npcNameSafe}:`, apiPayload);

            const response = await fetch('/api/dialogue/npc_action', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(apiPayload)
            });
            if (buttonElement) buttonElement.disabled = false; 
            const responseData = await response.json();
            if (!response.ok) throw new Error(responseData.error || responseData.message || `Action '${actionType}' failed`);
            
            let systemMessage = responseData.message || `Action '${escapeForHtml(actionType)}' for ${npcNameSafe} processed.`;
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", systemMessage, "system-success");

            if (responseData.data) {
                if (responseData.action === "next_topic" || responseData.action === "regenerate_topics") {
                    if (responseData.data.new_topics && responseData.data.new_topics.length > 0) {
                        addDialogueEntryToNpcLog(npc._id, "AI Topics", "Suggested Topics:\n- " + responseData.data.new_topics.join("\n- "), "system-info");
                        displayDialogueOptionsForNpc(npc._id, responseData.data.new_topics, "Suggested Topics (click to use as input):");
                    } else { addDialogueEntryToNpcLog(npc._id, "SYSTEM", "No new topics were generated.", "system-info"); }
                } else if (responseData.action === "show_top5_options") {
                     if (responseData.data.dialogue_options && responseData.data.dialogue_options.length > 0) {
                        displayDialogueOptionsForNpc(npc._id, responseData.data.dialogue_options, "AI Suggested Next Lines (click to make NPC say):");
                     } else { addDialogueEntryToNpcLog(npc._id, "SYSTEM", "No dialogue options were generated.", "system-info"); }
                }
            }
        } catch (error) {
            console.error(`Error during NPC action '${actionType}' for ${npcNameSafe}:`, error);
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Error with action '${escapeForHtml(actionType)}': ${error.message}`, "system-error");
            if(buttonElement) buttonElement.disabled = false;
        }
    }

    startSceneButton.addEventListener('click', () => {
        const sceneDescriptionInput = sceneDescriptionTextarea.value.trim();
        if (sceneParticipants.length === 0) { alert('No NPCs are currently part of the scene.'); return; }
        if (!sceneDescriptionInput) { alert('Please describe the scene or provide narration before initiating.'); sceneDescriptionTextarea.focus(); return; }

        currentSceneContext = sceneDescriptionInput; 
        currentSceneDescriptionDisplay.textContent = `Current Scene: ${escapeForHtml(currentSceneContext)}`;
        
        sceneParticipants.forEach(npc => {
            const logContainer = document.getElementById(`chat-log-${npc._id}`); // Use original ID
            if (logContainer) {
                logContainer.innerHTML = ''; 
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Scene context: "${escapeForHtml(currentSceneContext.substring(0,100))}..."`, "system");
                conversationHistory[npc._id] = [{ speaker: "SYSTEM", text: `Scene context: "${currentSceneContext}"` }]; 
            }
        });

        sceneParticipants.forEach((npc, index) => {
            addDialogueEntryToNpcLog(npc._id, npc.name, "<i>...formulating a response...</i>", "npc-thinking"); 
            setTimeout(() => { 
                // console.log(`Workspaceing initial dialogue for ${escapeForHtml(npc.name)} (ID: ${npc._id}) with scene: "${escapeForHtml(currentSceneContext)}"`);
                fetchNpcInitialDialogue(npc, currentSceneContext); 
            }, index * 700 + 400); 
        });
        sceneDescriptionTextarea.value = ""; 
    });

    async function fetchNpcInitialDialogue(npc, sceneDescForCall) {
        const npcId = npc._id; 
        const npcLogContainer = document.getElementById(`chat-log-${npcId}`);
        if (npcLogContainer) {
            const thinkingMessageEntry = npcLogContainer.querySelector('.chat-entry.npc-thinking');
            if(thinkingMessageEntry) thinkingMessageEntry.remove();
        }
        try {
            const payload = { npc_id: npcId, scene_context: sceneDescForCall, history: conversationHistory[npcId] ? conversationHistory[npcId].slice(-10) : [] };
            const response = await fetch('/api/dialogue/generate_npc_line', {
                method: 'POST', headers: { 'Content-Type': 'application/json', }, body: JSON.stringify(payload),
            });
            if (!response.ok) {
                let errorDetail = "Failed to fetch initial dialogue.";
                try { const errorData = await response.json(); errorDetail = errorData.detail || errorData.error || `Server status ${response.status}`; } catch (e) { errorDetail = `Server status ${response.status}, non-JSON error.`; }
                throw new Error(errorDetail);
            }
            const data = await response.json(); 
            if (data.dialogue_text) addDialogueEntryToNpcLog(npcId, npc.name, data.dialogue_text, "npc");
            else addDialogueEntryToNpcLog(npcId, "SYSTEM", "AI could not generate an initial response for " + escapeForHtml(npc.name), "system-error");
        } catch (error) {
            console.error(`Error fetching initial dialogue for ${escapeForHtml(npc.name)} (ID: ${npcId}):`, error);
            addDialogueEntryToNpcLog(npcId, "SYSTEM", `Error for ${escapeForHtml(npc.name)}: ${error.message}`, "system-error");
        }
    }

    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc") {
        const logContainer = document.getElementById(`chat-log-${npcId}`); // Use original ID
        if (!logContainer) { console.error(`Chat log container for NPC ID ${npcId} not found!`); return; }
        const entryDiv = document.createElement('div');
        const typeClass = type.startsWith('system') ? 'system-message' : type; 
        entryDiv.classList.add('chat-entry', typeClass); 
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';

        const speakerNameSafe = escapeForHtml(speakerName);
        if (type !== "npc" || type === "npc-thinking" || type.startsWith("system")) { 
            const speakerSpan = document.createElement('span');
            speakerSpan.className = 'speaker-name';
            speakerSpan.textContent = speakerNameSafe;
            bubbleDiv.appendChild(speakerSpan);
        }
        
        const dialogueP = document.createElement('p');
        dialogueP.className = 'dialogue-text';
        // Sanitize text for display using textContent or careful innerHTML
        // Using textContent is safest for directly inserting text that might contain HTML-like chars
        // If you need line breaks, you might need to split and append text nodes and br elements
        const lines = text.split('\n');
        lines.forEach((line, index) => {
            dialogueP.appendChild(document.createTextNode(line));
            if (index < lines.length - 1) {
                dialogueP.appendChild(document.createElement('br'));
            }
        });

        bubbleDiv.appendChild(dialogueP);
        entryDiv.appendChild(bubbleDiv);

        if (type === "npc" || type === "gm" || (type === "system" && speakerName === "SYSTEM" && text.startsWith("Scene context:")) ) {
             if (!conversationHistory[npcId]) conversationHistory[npcId] = [];
             if (!(type === "system-info" && speakerName === "GM Action")) {
                conversationHistory[npcId].push({ speaker: speakerName, text: text }); 
             }
        }
        logContainer.appendChild(entryDiv);
        logContainer.scrollTop = logContainer.scrollHeight; 
    }
    
    function displayDialogueOptionsForNpc(npcId, options, title = "Suggested Options:") {
        const logContainer = document.getElementById(`chat-log-${npcId}`); // Use original ID
        if (!logContainer || !options || options.length === 0) return;
        const existingOptions = logContainer.querySelector('.dialogue-options-container');
        if(existingOptions) existingOptions.remove(); 
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'dialogue-options-container'; 
        const titleElement = document.createElement('p');
        titleElement.className = 'dialogue-options-title'; 
        titleElement.textContent = escapeForHtml(title);
        optionsContainer.appendChild(titleElement);
        options.forEach(optionText => {
            const optionButton = document.createElement('button');
            optionButton.className = 'jrpg-button-small dialogue-option'; 
            optionButton.textContent = escapeForHtml(optionText); 
            optionButton.addEventListener('click', () => {
                addDialogueEntryToNpcLog(npcId, "GM Choice", `Selected: "${optionText}"`, "gm"); 
                const npcToRespond = sceneParticipants.find(p => p._id === npcId);
                if (npcToRespond) {
                    addDialogueEntryToNpcLog(npcId, npcToRespond.name, `<i>...reacting to GM's choice: "${escapeForHtml(optionText.substring(0,30))}..."</i>`, "npc-thinking");
                    fetchNpcInitialDialogue(npcToRespond, optionText); 
                }
                optionsContainer.remove(); 
            });
            optionsContainer.appendChild(optionButton);
        });
        logContainer.appendChild(optionsContainer);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

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