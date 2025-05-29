// srwmay08/bugbearbanter/BugbearBanter-cf73d42aed67696601941e44943cc5db45c8e493/server/static/js/scene.js
// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    console.log('Scene.js: DOMContentLoaded');

    const pcDisplayArea = document.getElementById('pc-display-area'); // For PCs
    const npcInteractionArea = document.getElementById('npc-interaction-area'); // For NPCs
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const startSceneButton = document.getElementById('start-scene-button');
    const currentSceneDescriptionDisplay = document.getElementById('current-scene-description-display');
    let loadingNpcsMessage = npcInteractionArea ? npcInteractionArea.querySelector('.loading-npcs-message') : null;
    if (pcDisplayArea && pcDisplayArea.querySelector('p')) { // Initial placeholder for PCs
        pcDisplayArea.querySelector('p').textContent = 'Loading PCs...';
    }


    let playerCharacters = []; // Array for PC objects
    let sceneNpcs = []; // Array for NPC objects (was sceneParticipants)
    let conversationHistory = {};
    let currentSceneContext = "";

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

    console.log('Scene.js: Initial checks for UI elements.');
    if (!npcInteractionArea || !sceneDescriptionTextarea || !startSceneButton || !currentSceneDescriptionDisplay || !pcDisplayArea) {
        console.error('CRITICAL: One or more essential UI elements for the scene page are missing from scene.html!');
        if(npcInteractionArea) {
            npcInteractionArea.innerHTML = '<p style="color:red; text-align:center;">Error: UI setup incomplete. Please check console and HTML structure.</p>';
        }
        if(pcDisplayArea){
            pcDisplayArea.innerHTML = '<p style="color:red; text-align:center;">Error: PC Display Area missing.</p>';
        }
        return;
    }


    const urlParams = new URLSearchParams(window.location.search);
    const pcIdsParam = urlParams.get('pc_ids');
    const npcIdsParam = urlParams.get('npc_ids');
    const selectedPcIds = pcIdsParam ? pcIdsParam.split(',').filter(id => id) : []; // Filter out empty strings if param is just ","
    const selectedNpcIds = npcIdsParam ? npcIdsParam.split(',').filter(id => id) : [];
    console.log('Scene.js: Selected PC IDs from URL:', selectedPcIds);
    console.log('Scene.js: Selected NPC IDs from URL:', selectedNpcIds);


    if (selectedPcIds.length === 0 && selectedNpcIds.length === 0) {
        console.warn('Scene.js: No characters (PCs or NPCs) selected.');
        if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'No NPCs were selected for this scene.';
        else if(npcInteractionArea) npcInteractionArea.innerHTML = '<p>No NPCs were selected for this scene.</p>';
        if(pcDisplayArea && pcDisplayArea.querySelector('p')) pcDisplayArea.querySelector('p').textContent = 'No PCs were selected for this scene.';
        if(startSceneButton) startSceneButton.disabled = true;
        return;
    }

    console.log('Scene.js: Fetching /api/npcs (for all characters)...');
    fetch('/api/npcs')
        .then(response => {
            console.log('Scene.js: /api/npcs response received.');
            if (!response.ok) {
                console.error('Scene.js: HTTP error fetching character list!', response.status, response.statusText);
                throw new Error(`HTTP error fetching character list! Status: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(allCharacters => { // Renamed from allNpcs
            console.log('Scene.js: All characters data received:', allCharacters);
            if (!Array.isArray(allCharacters)) {
                console.error('Scene.js: Fetched character data is not an array!', allCharacters);
                if(npcInteractionArea) npcInteractionArea.innerHTML = '<p style="color:red;">Error: Incorrect character data format from server.</p>';
                return;
            }

            allCharacters.forEach(char => {
                if (selectedPcIds.includes(char._id) && char.character_type === "PC") {
                    playerCharacters.push(char);
                } else if (selectedNpcIds.includes(char._id)) { // NPCs (or anything not PC)
                    sceneNpcs.push(char);
                    conversationHistory[char._id] = [];
                }
            });

            console.log('Scene.js: Player Characters list:', playerCharacters);
            console.log('Scene.js: Scene NPCs list:', sceneNpcs);

            if (playerCharacters.length === 0 && sceneNpcs.length === 0) {
                 console.warn('Scene.js: Could not load details for any selected characters.');
                 if(loadingNpcsMessage) loadingNpcsMessage.textContent = 'Could not load details for any selected NPCs.';
                 if(pcDisplayArea.querySelector('p')) pcDisplayArea.querySelector('p').textContent = 'Could not load details for any selected PCs.';
                 if(startSceneButton) startSceneButton.disabled = true;
            } else {
                if(loadingNpcsMessage && npcInteractionArea.contains(loadingNpcsMessage)) loadingNpcsMessage.remove();
                const pcPlaceholder = pcDisplayArea.querySelector('p');
                if (pcPlaceholder && pcDisplayArea.contains(pcPlaceholder)) pcPlaceholder.remove();
                console.log('Scene.js: Calling createCharacterInterfaces...');
                createCharacterInterfaces();
            }
        })
        .catch(error => {
            console.error('Scene.js: Error fetching or processing character details for scene:', error);
            if(loadingNpcsMessage && npcInteractionArea.contains(loadingNpcsMessage)) loadingNpcsMessage.textContent = `Error loading NPC details: ${error.message}. Check console.`;
            else if(npcInteractionArea) npcInteractionArea.innerHTML = `<p style="color:red;">Error loading NPC details: ${error.message}. Check console.</p>`;

            const pcPlaceholder = pcDisplayArea.querySelector('p');
            if(pcPlaceholder && pcDisplayArea.contains(pcPlaceholder)) pcPlaceholder.textContent = `Error loading PC details: ${error.message}. Check console.`;
            else if(pcDisplayArea) pcDisplayArea.innerHTML = `<p style="color:red;">Error loading PC details: ${error.message}. Check console.</p>`;

            if(startSceneButton) startSceneButton.disabled = true;
        });

    function createCharacterInterfaces() { // Renamed
        console.log('Scene.js: createCharacterInterfaces function called.');
        if (!npcInteractionArea || !pcDisplayArea) {
            console.error("Scene.js: npcInteractionArea or pcDisplayArea is null in createCharacterInterfaces!");
            return;
        }
        npcInteractionArea.innerHTML = '';
        pcDisplayArea.innerHTML = ''; // Clear PC area too

        // Render PCs
        if (playerCharacters.length > 0) {
            playerCharacters.forEach((pc, index) => {
                console.log(`Scene.js: Creating interface for PC ${index + 1}:`, pc);
                if (!pc || typeof pc._id === 'undefined' || pc.name === null || typeof pc.name === 'undefined') {
                    console.error('Scene.js: Invalid PC data encountered (missing _id or name):', pc);
                    const errorElement = document.createElement('div');
                    errorElement.className = 'pc-token-error';
                    errorElement.style.color = 'red';
                    errorElement.textContent = 'Error loading one PC token due to invalid data.';
                    pcDisplayArea.appendChild(errorElement);
                    return;
                }
                try {
                    const pcElement = document.createElement('div');
                    pcElement.className = 'pc-token jrpg-box-small'; // Add some styling
                    pcElement.dataset.pcId = pc._id;
                    pcElement.innerHTML = `<h4>${escapeForHtml(pc.name)} (PC)</h4>`;
                    pcDisplayArea.appendChild(pcElement);
                } catch (e) {
                    console.error(`Scene.js: Error creating token for PC ${pc.name || 'Unknown'}:`, e);
                    const errorToken = document.createElement('div');
                    errorToken.className = 'pc-token-error';
                    errorToken.textContent = `Error for ${escapeForHtml(pc.name || 'Unknown PC')}.`;
                    pcDisplayArea.appendChild(errorToken);
                }
            });
        } else {
            pcDisplayArea.innerHTML = '<p>No PCs selected for this scene.</p>';
        }


        // Render NPCs
        if (sceneNpcs.length > 0) {
            sceneNpcs.forEach((npc, index) => {
                console.log(`Scene.js: Creating interface for NPC ${index + 1}:`, npc);
                 if (!npc || typeof npc._id === 'undefined' || npc.name === null || typeof npc.name === 'undefined') {
                    console.error('Scene.js: Invalid NPC data encountered (missing _id or name):', npc);
                    const errorContainer = document.createElement('div');
                    errorContainer.className = 'npc-dialogue-container';
                    errorContainer.style.color = 'red';
                    errorContainer.textContent = 'Error loading one NPC card due to invalid data.';
                    npcInteractionArea.appendChild(errorContainer);
                    return;
                }

                try {
                    const npcContainer = document.createElement('div');
                    npcContainer.className = 'npc-dialogue-container';
                    npcContainer.dataset.npcId = npc._id;

                    const npcNameSafe = escapeForHtml(npc.name);
                    const npcIdSafe = escapeForHtml(npc._id);

                    const npcInitials = String(npc.name).substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') || '??';
                    const bgColor = stringToColor(npc.name || 'default');

                    console.log(`Scene.js: NPC Name: ${npc.name}, Initials: ${npcInitials}, Color: ${bgColor}`);

                    npcContainer.innerHTML = `
                        <div class="npc-header">
                            <div class="npc-initials-placeholder" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #${bgColor}; color: white; font-family: 'Press Start 2P', cursive; border-radius: 4px; margin-right: 10px;">
                                ${npcInitials}
                            </div>
                            <h3 class="npc-header-name" style="display: inline;">${npcNameSafe} (NPC)</h3>
                        </div>
                        <div class="npc-chat-log" id="chat-log-${npcIdSafe}">
                            <p class="log-placeholder">Awaiting interaction...</p>
                        </div>
                        <div class="npc-dialogue-controls">
                            <button class="jrpg-button-small btn-submit-memory" data-action="submit_memory" data-npc-id="${npcIdSafe}" title="Commit last exchange to ${npcNameSafe}'s memory">To Memory</button>
                            <button class="jrpg-button-small btn-undo-memory" data-action="undo_memory" data-npc-id="${npcIdSafe}" title="Undo last memory submission for ${npcNameSafe}">Undo Mem</button>
                            <button class="jrpg-button-small btn-next-topic" data-action="next_topic" data-npc-id="${npcIdSafe}" title="Advance ${npcNameSafe} to the next generated topic">Next Topic</button>
                            <button class="jrpg-button-small btn-regen-topics" data-action="regenerate_topics" data-npc-id="${npcIdSafe}" title="Generate new conversation topics for ${npcNameSafe}">Regen Topics</button>
                            <button class="jrpg-button-small btn-show-top5" data-action="show_top5_options" data-npc-id="${npcIdSafe}" title="Show top 5 dialogue options for ${npcNameSafe}">Top 5</button>
                            <button class="jrpg-button-small btn-show-tree" data-action="show_tree" data-npc-id="${npcIdSafe}" title="Show conversation tree for ${npcNameSafe} (future)">Tree</button>
                        </div>
                    `;
                    npcInteractionArea.appendChild(npcContainer);
                    console.log(`Scene.js: Successfully created card for NPC ${npcNameSafe}`);

                } catch (e) {
                    console.error(`Scene.js: Error during innerHTML assignment for NPC ${npc.name || 'Unknown'}:`, e);
                    const errorCard = document.createElement('div');
                    errorCard.className = 'npc-dialogue-container';
                    errorCard.style.color = 'red';
                    errorCard.textContent = `Error creating card for ${escapeForHtml(npc.name || 'Unknown NPC')}. Check console.`;
                    npcInteractionArea.appendChild(errorCard);
                }
            });
        } else {
             npcInteractionArea.innerHTML = '<p>No NPCs selected for this scene.</p>';
        }

        addControlEventListeners();
        console.log('Scene.js: createCharacterInterfaces finished.');
    }

    function stringToColor(str) {
        let hash = 0;
        if (!str || typeof str !== 'string' || str.length === 0) return 'CCCCCC';
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash;
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }

    function addControlEventListeners() {
        console.log('Scene.js: addControlEventListeners called.');
        if (!npcInteractionArea) { // Event listeners are for NPC controls
            console.warn("Scene.js: npcInteractionArea is null, cannot add NPC control event listeners!");
            return;
        }
        npcInteractionArea.addEventListener('click', function(event) {
            const button = event.target.closest('.jrpg-button-small[data-action]');
            if (button) {
                const npcId = button.dataset.npcId;
                const actionType = button.dataset.action;
                const npc = sceneNpcs.find(p => p._id === npcId); // Search in sceneNpcs

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
        if (sceneNpcs.length === 0) { // Actions primarily target NPCs
             alert('No NPCs are currently part of the scene to interact with.');
             // You might still want to set scene context if PCs are present
             if (playerCharacters.length > 0 && sceneDescriptionInput) {
                currentSceneContext = sceneDescriptionInput;
                currentSceneDescriptionDisplay.textContent = `Current Scene: ${escapeForHtml(currentSceneContext)}`;
                addDialogueEntryToNpcLog(null, "SYSTEM", `Scene context (PCs only): "${escapeForHtml(currentSceneContext.substring(0,100))}..."`, "system", true); // Log globally if no NPCs
                sceneDescriptionTextarea.value = "";
             }
             return;
        }
        if (!sceneDescriptionInput) { alert('Please describe the scene or provide narration before initiating.'); sceneDescriptionTextarea.focus(); return; }

        currentSceneContext = sceneDescriptionInput;
        currentSceneDescriptionDisplay.textContent = `Current Scene: ${escapeForHtml(currentSceneContext)}`;

        sceneNpcs.forEach(npc => {
            const logContainer = document.getElementById(`chat-log-${npc._id}`);
            if (logContainer) {
                logContainer.innerHTML = '';
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Scene context: "${escapeForHtml(currentSceneContext.substring(0,100))}..."`, "system");
                conversationHistory[npc._id] = [{ speaker: "SYSTEM", text: `Scene context: "${currentSceneContext}"` }];
            }
        });

        sceneNpcs.forEach((npc, index) => {
            addDialogueEntryToNpcLog(npc._id, npc.name, "<i>...formulating a response...</i>", "npc-thinking");
            setTimeout(() => {
                console.log(`Scene.js: Fetching initial dialogue for ${escapeForHtml(npc.name)} (ID: ${npc._id})`);
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
            console.error(`Scene.js: Error fetching initial dialogue for ${escapeForHtml(npc.name)} (ID: ${npcId}):`, error);
            addDialogueEntryToNpcLog(npcId, "SYSTEM", `Error for ${escapeForHtml(npc.name)}: ${error.message}`, "system-error");
        }
    }

    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc", globalForPCsOnly = false) {
        let logContainer;
        if (globalForPCsOnly && !npcId) { // Log to a general area if no specific NPC and it's a global PC context
            logContainer = document.getElementById('pc-display-area'); // Or a dedicated global log if you add one
             if(logContainer && logContainer.innerHTML.includes("PCs will appear here")) logContainer.innerHTML = ""; // Clear placeholder
        } else {
             logContainer = document.getElementById(`chat-log-${npcId}`);
        }

        if (!logContainer) {
            if (!globalForPCsOnly) console.error(`Chat log container for NPC ID ${npcId} not found!`);
            else console.error(`PC Display area not found for global log!`);
            return;
        }
        const entryDiv = document.createElement('div');
        const typeClass = type.startsWith('system') ? 'system-message' : type;
        entryDiv.classList.add('chat-entry', typeClass);

        let bubbleHtml = `<div class="chat-bubble">`;
        const speakerNameSafe = escapeForHtml(speakerName);
        if (type !== "npc" || type === "npc-thinking" || type.startsWith("system")) {
            bubbleHtml += `<span class="speaker-name">${speakerNameSafe}</span>`;
        }

        if (type === "npc-thinking" && text.includes("<i>")) {
             bubbleHtml += `<p class="dialogue-text">${text.replace(/\n/g, '<br>')}</p>`; // Don't escape <i>
        } else {
            const displayText = escapeForHtml(text);
            bubbleHtml += `<p class="dialogue-text">${displayText.replace(/\n/g, '<br>')}</p>`;
        }
        bubbleHtml += `</div>`;
        entryDiv.innerHTML = bubbleHtml;

        if (!globalForPCsOnly && npcId && (type === "npc" || type === "gm" || (type === "system" && speakerName === "SYSTEM" && text.startsWith("Scene context:")) )) {
             if (!conversationHistory[npcId]) conversationHistory[npcId] = [];
             if (!(type === "system-info" && speakerName === "GM Action")) { // Don't add functional GM actions to AI history
                conversationHistory[npcId].push({ speaker: speakerName, text: text }); // Store original text for history
             }
        }
        // Clear placeholder from NPC log if it exists
        const placeholder = logContainer.querySelector('.log-placeholder');
        if(placeholder) placeholder.remove();

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
                const npcToRespond = sceneNpcs.find(p => p._id === npcId);
                if (npcToRespond) {
                    addDialogueEntryToNpcLog(npcId, npcToRespond.name, `<i>...reacting to GM's choice: "${escapeForHtml(optionText.substring(0,30))}..."</i>`, "npc-thinking");
                    fetchNpcInitialDialogue(npcToRespond, optionText); // NPC reacts to the chosen option
                }
                optionsContainer.remove();
            });
            optionsContainer.appendChild(optionButton);
        });
        logContainer.appendChild(optionsContainer);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    console.log('Scene.js: Script loaded and event listeners should be active.');
});