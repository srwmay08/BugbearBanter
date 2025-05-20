// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    console.log('Scene.js: DOMContentLoaded');

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

    // --- Helper Function to Escape HTML (and JS template literal-breaking chars like backtick) ---
    function escapeForHtml(unsafe) {
        if (unsafe === null || typeof unsafe === 'undefined') {
            console.warn('escapeForHtml called with null or undefined');
            return '';
        }
        return unsafe
             .toString()
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;")
             .replace(/`/g, "&#96;"); // Escape backticks
    }

    console.log('Scene.js: Initial checks for UI elements.');
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
    console.log('Scene.js: UI elements checked.');

    const urlParams = new URLSearchParams(window.location.search);
    const npcIdsParam = urlParams.get('npcs');
    const selectedNpcIds = npcIdsParam ? npcIdsParam.split(',') : [];
    console.log('Scene.js: Selected NPC IDs from URL:', selectedNpcIds);

    if (selectedNpcIds.length === 0) {
        console.warn('Scene.js: No NPCs selected.');
        if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'No NPCs were selected for this scene. Please go back to NPC selection.';
        else if(npcInteractionArea) npcInteractionArea.innerHTML = '<p>No NPCs were selected for this scene. Please go back to NPC selection.</p>';
        startSceneButton.disabled = true;
        return;
    }

    console.log('Scene.js: Fetching /api/npcs...');
    fetch('/api/npcs') 
        .then(response => {
            console.log('Scene.js: /api/npcs response received.');
            if (!response.ok) {
                console.error('Scene.js: HTTP error fetching NPC list!', response.status, response.statusText);
                throw new Error(`HTTP error fetching NPC list! Status: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(allNpcs => {
            console.log('Scene.js: All NPCs data:', allNpcs);
            if (!Array.isArray(allNpcs)) {
                console.error('Scene.js: Fetched NPC data is not an array!', allNpcs);
                throw new Error('Fetched NPC data is not an array.');
            }

            selectedNpcIds.forEach(id => {
                const npc = allNpcs.find(n => n._id === id);
                if (npc) {
                    console.log('Scene.js: Found NPC for ID:', id, npc);
                    sceneParticipants.push(npc);
                    conversationHistory[npc._id] = []; 
                } else {
                    console.warn(`Scene.js: NPC with ID ${id} not found in fetched list.`);
                }
            });
            
            console.log('Scene.js: Scene participants:', sceneParticipants);
            if (sceneParticipants.length === 0) {
                console.warn('Scene.js: Could not load details for any selected NPCs.');
                if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'Could not load details for any of the selected NPCs.';
                startSceneButton.disabled = true;
            } else {
                if(loadingNpcsMessage) loadingNpcsMessage.remove(); 
                console.log('Scene.js: Calling createNpcInteractionInterfaces...');
                createNpcInteractionInterfaces();
            }
        })
        .catch(error => {
            console.error('Scene.js: Error fetching or processing NPC details for scene:', error);
            if(loadingNpcsMessage) loadingNpcsMessage.textContent = `Error loading NPC details: ${error.message}. Check console.`;
            else if(npcInteractionArea) npcInteractionArea.innerHTML = `<p>Error loading NPC details: ${error.message}. Check console.</p>`;
            startSceneButton.disabled = true;
        });

    function createNpcInteractionInterfaces() {
        console.log('Scene.js: createNpcInteractionInterfaces called.');
        npcInteractionArea.innerHTML = ''; 

        sceneParticipants.forEach((npc, index) => {
            console.log(`Scene.js: Processing NPC ${index}:`, npc);
            if (!npc || typeof npc._id === 'undefined' || typeof npc.name === 'undefined') {
                console.error('Scene.js: NPC object is invalid or missing critical properties (_id, name):', npc);
                // Optionally, append an error message to the UI for this NPC
                const errorNpcContainer = document.createElement('div');
                errorNpcContainer.className = 'npc-dialogue-container';
                errorNpcContainer.innerHTML = `<p style="color:red;">Error: Invalid NPC data for one participant.</p>`;
                npcInteractionArea.appendChild(errorNpcContainer);
                return; // Skip this NPC
            }

            try {
                const npcContainer = document.createElement('div');
                npcContainer.className = 'npc-dialogue-container';
                npcContainer.dataset.npcId = npc._id; 

                const npcNameForDisplay = escapeForHtml(npc.name || 'Unknown NPC');
                const npcIdForHtml = escapeForHtml(npc._id);

                const npcNameStr = npc.name || "defaultNPC_bg"; // Ensure string for stringToColor
                const npcInitials = npc.name ? String(npc.name).substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
                console.log(`Scene.js: NPC Name: ${npc.name}, Initials: ${npcInitials}`);

                const placeholderBgColor = stringToColor(npcNameStr);
                console.log(`Scene.js: Placeholder BG Color for ${npcNameStr}: ${placeholderBgColor}`);

                const portraitUrl = `https://placehold.co/50x50/${placeholderBgColor}/FFFFFF?text=${encodeURIComponent(npcInitials)}&font=source-sans-pro`;
                console.log(`Scene.js: Portrait URL for ${npcNameForDisplay}: ${portraitUrl}`);
                
                // This is the version using innerHTML from two turns ago, with added escaping
                npcContainer.innerHTML = `
                    <div class="npc-header">
                        <img src="${portraitUrl}" alt="Portrait of ${npcNameForDisplay}" class="npc-header-portrait" onerror="this.style.display='none'; console.error('Image load error for: ${portraitUrl}');">
                        <h3 class="npc-header-name">${npcNameForDisplay}</h3>
                    </div>
                    <div class="npc-chat-log" id="chat-log-${npcIdForHtml}">
                        <p class="log-placeholder">Awaiting interaction...</p>
                    </div>
                    <div class="npc-dialogue-controls">
                        <button class="jrpg-button-small btn-submit-memory" data-action="submit_memory" data-npc-id="${npcIdForHtml}" title="Commit last exchange to ${npcNameForDisplay}'s memory">To Memory</button>
                        <button class="jrpg-button-small btn-undo-memory" data-action="undo_memory" data-npc-id="${npcIdForHtml}" title="Undo last memory submission for ${npcNameForDisplay}">Undo Mem</button>
                        <button class="jrpg-button-small btn-next-topic" data-action="next_topic" data-npc-id="${npcIdForHtml}" title="Advance ${npcNameForDisplay} to the next generated topic">Next Topic</button>
                        <button class="jrpg-button-small btn-regen-topics" data-action="regenerate_topics" data-npc-id="${npcIdForHtml}" title="Generate new conversation topics for ${npcNameForDisplay}">Regen Topics</button>
                        <button class="jrpg-button-small btn-show-top5" data-action="show_top5_options" data-npc-id="${npcIdForHtml}" title="Show top 5 dialogue options for ${npcNameForDisplay}">Top 5</button>
                        <button class="jrpg-button-small btn-show-tree" data-action="show_tree" data-npc-id="${npcIdForHtml}" title="Show conversation tree for ${npcNameForDisplay} (future)">Tree</button>
                    </div>
                `;
                npcInteractionArea.appendChild(npcContainer);
                console.log(`Scene.js: Appended container for ${npcNameForDisplay}`);

            } catch (e) {
                console.error(`Scene.js: Error creating HTML for NPC:`, npc, e);
                const errorDiv = document.createElement('div');
                errorDiv.style.color = 'red';
                errorDiv.textContent = `Error rendering NPC: ${escapeForHtml(npc.name || 'Unknown')}. Check console.`;
                npcInteractionArea.appendChild(errorDiv);
            }
        });
        addControlEventListeners(); 
        console.log('Scene.js: createNpcInteractionInterfaces finished.');
    }
    
    // ... (rest of the functions: addControlEventListeners, handleNpcSpecificAction, startSceneButton listener, fetchNpcInitialDialogue, addDialogueEntryToNpcLog, displayDialogueOptionsForNpc, stringToColor)
    // Ensure escapeForHtml is used in those functions where appropriate for displaying NPC names or other data.
    // For brevity, I'll assume the rest of the functions from the previous correct version are here and only show changes if directly related to the problem.
    // Make sure to use 'escapeForHtml' in console logs or UI messages if they include dynamic NPC data.

    function addControlEventListeners() {
        console.log('Scene.js: addControlEventListeners called.');
        npcInteractionArea.addEventListener('click', function(event) {
            const button = event.target.closest('.jrpg-button-small[data-action]'); 
            if (button) { 
                const npcId = button.dataset.npcId;
                const actionType = button.dataset.action; 
                const npc = sceneParticipants.find(p => p._id === npcId);
                
                if (npc) {
                    handleNpcSpecificAction(npc, actionType, button);
                } else {
                    console.warn(`Scene.js: Could not find NPC data for ID: ${escapeForHtml(npcId)} on button click for action: ${escapeForHtml(actionType)}.`);
                }
            }
        });
    }
    
    async function handleNpcSpecificAction(npc, actionType, buttonElement) {
        const npcNameSafe = escapeForHtml(npc.name);
        console.log(`Scene.js: Action '${actionType}' triggered for ${npcNameSafe} (ID: ${npc._id})`);
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
            console.log(`Scene.js: Sending payload for action '${actionType}' for ${npcNameSafe}:`, apiPayload);

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
            console.error(`Scene.js: Error during NPC action '${actionType}' for ${npcNameSafe}:`, error);
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Error with action '${escapeForHtml(actionType)}': ${error.message}`, "system-error");
            if(buttonElement) buttonElement.disabled = false;
        }
    }

    startSceneButton.addEventListener('click', () => {
        console.log('Scene.js: Start Scene button clicked.');
        const sceneDescriptionInput = sceneDescriptionTextarea.value.trim();
        if (sceneParticipants.length === 0) { alert('No NPCs are currently part of the scene.'); return; }
        if (!sceneDescriptionInput) { alert('Please describe the scene or provide narration before initiating.'); sceneDescriptionTextarea.focus(); return; }

        currentSceneContext = sceneDescriptionInput; 
        currentSceneDescriptionDisplay.textContent = `Current Scene: ${escapeForHtml(currentSceneContext)}`;
        
        sceneParticipants.forEach(npc => {
            const logContainer = document.getElementById(`chat-log-${npc._id}`);
            if (logContainer) {
                logContainer.innerHTML = ''; 
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Scene context: "${escapeForHtml(currentSceneContext.substring(0,100))}..."`, "system");
                conversationHistory[npc._id] = [{ speaker: "SYSTEM", text: `Scene context: "${currentSceneContext}"` }]; 
            }
        });

        sceneParticipants.forEach((npc, index) => {
            addDialogueEntryToNpcLog(npc._id, npc.name, "<i>...formulating a response...</i>", "npc-thinking"); 
            setTimeout(() => { 
                console.log(`Scene.js: Fetching initial dialogue for ${escapeForHtml(npc.name)} (ID: ${npc._id}) with scene: "${escapeForHtml(currentSceneContext)}"`);
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
            // console.log(`Payload for initial line for ${escapeForHtml(npc.name)}:`, JSON.stringify(payload));
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
            console.error(`Scene.js: Error fetching initial dialogue for ${escapeForHtml(npc.name)} (ID: ${npcId}):`, error);
            addDialogueEntryToNpcLog(npcId, "SYSTEM", `Error for ${escapeForHtml(npc.name)}: ${error.message}`, "system-error");
        }
    }

    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc") {
        const logContainer = document.getElementById(`chat-log-${npcId}`); 
        if (!logContainer) { console.error(`Chat log container for NPC ID ${npcId} not found!`); return; }
        const entryDiv = document.createElement('div');
        const typeClass = type.startsWith('system') ? 'system-message' : type; 
        entryDiv.classList.add('chat-entry', typeClass); 
        
        let bubbleHtml = `<div class="chat-bubble">`;
        const speakerNameSafe = escapeForHtml(speakerName);
        if (type !== "npc" || type === "npc-thinking" || type.startsWith("system")) { 
            bubbleHtml += `<span class="speaker-name">${speakerNameSafe}</span>`;
        }
        // For text content that might contain <i> for italics, we need to set innerHTML carefully
        // For AI generated dialogue, it's generally plain text. For our hardcoded "<i>...</i>", this is an issue.
        // Let's assume 'text' from AI is plain, and hardcoded italics are only for "thinking"
        if (type === "npc-thinking" && text.includes("<i>")) {
             bubbleHtml += `<p class="dialogue-text">${text.replace(/\n/g, '<br>')}</p>`; // Allow italics for thinking
        } else {
            const displayText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); // Basic sanitization for display
            bubbleHtml += `<p class="dialogue-text">${displayText.replace(/\n/g, '<br>')}</p>`;
        }
        bubbleHtml += `</div>`;
        entryDiv.innerHTML = bubbleHtml; // Reverted this part back to innerHTML for simplicity with italics

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
        const logContainer = document.getElementById(`chat-log-${npcId}`); 
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
        if (!str || typeof str !== 'string' || str.length === 0) return 'CCCCCC'; // Added type check
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash; 
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }
    console.log('Scene.js: Script loaded and event listeners should be active.');
});