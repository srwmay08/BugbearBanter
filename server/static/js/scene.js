// static/js/scene.js
document.addEventListener('DOMContentLoaded', () => {
    console.log('Scene.js: DOMContentLoaded');

    const npcInteractionArea = document.getElementById('npc-interaction-area');
    const sceneDescriptionTextarea = document.getElementById('scene-description-textarea');
    const startSceneButton = document.getElementById('start-scene-button');
    const currentSceneDescriptionDisplay = document.getElementById('current-scene-description-display');
    const ongoingNarrationTextarea = document.getElementById('ongoing-narration-textarea');
    const submitOngoingNarrationButton = document.getElementById('submit-ongoing-narration-button');
    const playerCharacterListUl = document.getElementById('player-character-list');
    const loadingPcsMessage = document.getElementById('loading-pcs-message');
    let loadingNpcsMessageEl = npcInteractionArea ? npcInteractionArea.querySelector('.loading-npcs-message') : null;

    let sceneParticipantNpcs = [];
    let conversationHistory = {};
    let currentSceneContext = "";
    let presentPlayerCharacters = []; // Array of PC names that are checked as present

    function escapeForHtml(unsafe) {
        if (unsafe === null || typeof unsafe === 'undefined') return '';
        return unsafe.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;").replace(/`/g, "&#96;");
    }

    if (!npcInteractionArea || !sceneDescriptionTextarea || !startSceneButton || !currentSceneDescriptionDisplay || !ongoingNarrationTextarea || !submitOngoingNarrationButton || !playerCharacterListUl) {
        console.error('CRITICAL: Essential UI elements missing from scene.html!');
        if(npcInteractionArea) npcInteractionArea.innerHTML = '<p style="color:red; text-align:center;">Error: UI setup incomplete.</p>';
        return;
    }
    if (!loadingNpcsMessageEl && npcInteractionArea) {
        loadingNpcsMessageEl = npcInteractionArea.querySelector('.loading-npcs-message');
    }

    const urlParams = new URLSearchParams(window.location.search);
    const npcIdsParam = urlParams.get('npcs');
    const selectedNpcIdsForScene = npcIdsParam ? npcIdsParam.split(',') : [];

    if (selectedNpcIdsForScene.length === 0 && loadingNpcsMessageEl) {
        console.warn('Scene.js: No NPCs selected for the scene (via URL params).');
        loadingNpcsMessageEl.textContent = 'No NPCs were selected for this scene. Please go back to NPC selection.';
        // Don't disable start button yet, PCs might still be interacted with, or scene set without NPCs initially
    }

    // Fetch ALL characters (PCs and NPCs)
    fetch('/api/npcs') 
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error fetching characters! Status: ${response.status} ${response.statusText}`);
            return response.json();
        })
        .then(allCharacters => {
            // *** DEBUGGING: Log raw data from API ***
            console.log('scene.js: Data received from /api/npcs:', JSON.stringify(allCharacters, null, 2)); 

            if (!Array.isArray(allCharacters)) {
                console.error('Scene.js: Fetched character data is not an array!', allCharacters);
                if(loadingPcsMessage) loadingPcsMessage.textContent = 'Error: Incorrect character data format from server.';
                if(loadingNpcsMessageEl) loadingNpcsMessageEl.textContent = 'Error: Incorrect character data format.';
                return;
            }

            const pcs = allCharacters.filter(char => char.type === 'pc');
            // *** DEBUGGING: Log filtered PCs ***
            console.log('scene.js: Filtered PCs for list:', JSON.stringify(pcs, null, 2)); 
            populatePlayerCharacterList(pcs); // Populate PC list first

            // Then, filter for and process NPCs selected for the scene
            selectedNpcIdsForScene.forEach(id => {
                // Ensure we only pick NPCs for scene participation, undefined type defaults to NPC for backward compatibility
                const npc = allCharacters.find(char => (char.type === 'npc' || typeof char.type === 'undefined') && char._id === id); 
                if (npc) {
                    sceneParticipantNpcs.push(npc);
                    conversationHistory[npc._id] = [];
                } else {
                    console.warn(`Scene.js: Scene NPC with ID ${id} not found in fetched characters or is not explicitly type 'npc'.`);
                }
            });
            
            if (selectedNpcIdsForScene.length > 0 && sceneParticipantNpcs.length === 0) {
                if(loadingNpcsMessageEl) loadingNpcsMessageEl.textContent = 'Could not load details for any of the selected NPCs for the scene.';
            } else if (sceneParticipantNpcs.length > 0) {
                if(loadingNpcsMessageEl) loadingNpcsMessageEl.remove(); // Remove "Loading NPCs..."
                createNpcInteractionInterfaces();
            } else { 
                 if(loadingNpcsMessageEl && selectedNpcIdsForScene.length > 0) loadingNpcsMessageEl.textContent = 'Selected NPCs not found or invalid.';
                 else if (loadingNpcsMessageEl) loadingNpcsMessageEl.textContent = 'No scene NPCs loaded (or none selected).';
            }
        })
        .catch(error => {
            console.error('Scene.js: Error fetching or processing characters:', error);
            if(loadingPcsMessage) loadingPcsMessage.textContent = `Error loading PCs: ${error.message}.`;
            if(loadingNpcsMessageEl) loadingNpcsMessageEl.textContent = `Error loading NPCs: ${error.message}.`;
        });

    function populatePlayerCharacterList(pcs) {
        if (!playerCharacterListUl) return;
        playerCharacterListUl.innerHTML = ''; // Clear previous items (like loading message)

        if (!pcs || pcs.length === 0) {
            playerCharacterListUl.innerHTML = '<li class="no-pcs-found"><p>No player characters found or loaded from the database.</p></li>';
            if(loadingPcsMessage && loadingPcsMessage.parentNode === playerCharacterListUl) { 
                loadingPcsMessage.style.display = 'none'; 
            }
            return;
        }

        pcs.forEach(pc => {
            if (!pc || !pc.name || !pc._id) { 
                console.warn("Skipping PC in list due to missing name or ID:", pc);
                return;
            }
            const listItem = document.createElement('li');
            listItem.classList.add('player-character-item');

            const pcHeader = document.createElement('div');
            pcHeader.classList.add('pc-header');
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'player_character_present';
            checkbox.value = escapeForHtml(pc.name);
            checkbox.dataset.pcId = escapeForHtml(pc._id); 
            checkbox.checked = true; 
            checkbox.addEventListener('change', updatePresentPlayerCharacters);
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(` ${escapeForHtml(pc.name)}`));
            pcHeader.appendChild(label);
            listItem.appendChild(pcHeader);

            const pcActionArea = document.createElement('div');
            pcActionArea.classList.add('pc-action-area');
            const pcActionTextarea = document.createElement('textarea');
            pcActionTextarea.classList.add('jrpg-textarea', 'pc-action-input');
            pcActionTextarea.rows = 2;
            pcActionTextarea.placeholder = `Action for ${escapeForHtml(pc.name)}...`;
            
            const pcActionButton = document.createElement('button');
            pcActionButton.classList.add('jrpg-button', 'jrpg-button-small', 'pc-action-submit-button');
            pcActionButton.textContent = `Submit Action`; 
            pcActionButton.dataset.pcName = escapeForHtml(pc.name); 

            pcActionButton.addEventListener('click', () => {
                const actionText = pcActionTextarea.value.trim();
                const charName = pcActionButton.dataset.pcName; 
                if (actionText) {
                    const narrationForNpcs = `Player Action - ${charName}: ${actionText}`;
                    
                    currentSceneContext += `\n\n${narrationForNpcs}`; 
                    currentSceneDescriptionDisplay.textContent = `Current Scene: ${escapeForHtml(currentSceneContext.substring(0, 150))}...`;

                    sceneParticipantNpcs.forEach(activeNpc => {
                        addDialogueEntryToNpcLog(activeNpc._id, "SYSTEM", `(GM notes ${charName}'s action: ${escapeForHtml(actionText.substring(0,50))}...)`, "system-info gm-action-log");
                    });
                    
                    sceneParticipantNpcs.forEach((activeNpc, index) => {
                        addDialogueEntryToNpcLog(activeNpc._id, activeNpc.name, `<i>...reacting to ${charName}'s action...</i>`, "npc-thinking");
                        setTimeout(() => {
                            fetchNpcReaction(activeNpc, narrationForNpcs); 
                        }, index * 700 + 200); 
                    });
                    pcActionTextarea.value = ''; 
                } else {
                    alert(`Please enter an action for ${charName}.`);
                }
            });

            pcActionArea.appendChild(pcActionTextarea);
            pcActionArea.appendChild(pcActionButton);
            listItem.appendChild(pcActionArea);
            playerCharacterListUl.appendChild(listItem);
        });
        if(loadingPcsMessage && loadingPcsMessage.parentNode === playerCharacterListUl) {
            loadingPcsMessage.style.display = 'none'; 
        }
        updatePresentPlayerCharacters(); 
    }

    function createNpcInteractionInterfaces() {
        if (!npcInteractionArea) { console.error("npcInteractionArea is null in createNpcInteractionInterfaces"); return; }
        npcInteractionArea.innerHTML = '';
        sceneParticipantNpcs.forEach(npc => {
            if (!npc || typeof npc._id === 'undefined' || npc.name === null || typeof npc.name === 'undefined') {
                console.error('Scene.js: Invalid NPC data for card creation:', npc);
                const errorContainer = document.createElement('div');
                errorContainer.className = 'npc-dialogue-container error-card';
                errorContainer.textContent = 'Error loading one NPC card due to invalid data.';
                npcInteractionArea.appendChild(errorContainer);
                return;
            }
            const npcContainer = document.createElement('div');
            npcContainer.className = 'npc-dialogue-container';
            npcContainer.dataset.npcId = npc._id;
            const npcNameSafe = escapeForHtml(npc.name);
            const npcIdSafe = escapeForHtml(npc._id);
            const npcInitials = String(npc.name).substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') || '??';
            const bgColor = stringToColor(npc.name || 'default');
            npcContainer.innerHTML = `
                <div class="npc-header">
                    <div class="npc-initials-placeholder" style="background-color: #${bgColor};">${npcInitials}</div>
                    <h3 class="npc-header-name">${npcNameSafe}</h3>
                </div>
                <div class="npc-chat-log" id="chat-log-${npcIdSafe}"><p class="log-placeholder">Awaiting interaction...</p></div>
                <div class="npc-dialogue-controls">
                    <button class="jrpg-button-small btn-submit-memory" data-action="submit_memory" data-npc-id="${npcIdSafe}" title="Commit last exchange to ${npcNameSafe}'s memory">To Memory</button>
                    <button class="jrpg-button-small btn-undo-memory" data-action="undo_memory" data-npc-id="${npcIdSafe}" title="Undo last memory submission for ${npcNameSafe}">Undo Mem</button>
                    <button class="jrpg-button-small btn-next-topic" data-action="next_topic" data-npc-id="${npcIdSafe}" title="Advance ${npcNameSafe} to the next generated topic">Next Topic</button>
                    <button class="jrpg-button-small btn-regen-topics" data-action="regenerate_topics" data-npc-id="${npcIdSafe}" title="Generate new conversation topics for ${npcNameSafe}">Regen Topics</button>
                    <button class="jrpg-button-small btn-show-top5" data-action="show_top5_options" data-npc-id="${npcIdSafe}" title="Show top 5 dialogue options for ${npcNameSafe}">Top 5</button>
                    <button class="jrpg-button-small btn-show-tree" data-action="show_tree" data-npc-id="${npcIdSafe}" title="Show conversation tree for ${npcNameSafe} (future)">Tree</button>
                </div>
                <div class="gm-notes-panel">
                    <label for="gm-notes-${npcIdSafe}">GM Notes for ${npcNameSafe}:</label>
                    <textarea id="gm-notes-${npcIdSafe}" class="gm-npc-notes-textarea jrpg-textarea" rows="3" placeholder="Notes on this NPC..."></textarea>
                </div>`;
            npcInteractionArea.appendChild(npcContainer);
        });
        addControlEventListeners();
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
        if (!npcInteractionArea) {console.error("npcInteractionArea is null in addControlEventListeners"); return;}
        npcInteractionArea.addEventListener('click', function(event) {
            const button = event.target.closest('.jrpg-button-small[data-action]');
            if (button) {
                const npcId = button.dataset.npcId;
                const actionType = button.dataset.action;
                const npc = sceneParticipantNpcs.find(p => p._id === npcId);
                if (npc) handleNpcSpecificAction(npc, actionType, button);
                else console.warn(`NPC data for ID: ${escapeForHtml(npcId)} not found for action: ${escapeForHtml(actionType)}.`);
            }
        });
    }

    async function handleNpcSpecificAction(npc, actionType, buttonElement) {
        const npcNameSafe = escapeForHtml(npc.name);
        if (actionType !== "show_top5_options" && actionType !== "next_topic" && actionType !== "regenerate_topics") {
            addDialogueEntryToNpcLog(npc._id, "GM Action", `GM triggered: ${escapeForHtml(actionType)} for ${npcNameSafe}`, "system-info gm-action-log");
        }
        let payloadSpecifics = {};
        if (actionType === "submit_memory") {
            const historyForNpc = (conversationHistory[npc._id] || []).filter(
                e => e.speaker !== "GM Action" && !(e.type && (e.type.includes("system-info") || e.type.includes("gm-action-log")))
            );
            let relevantExchange = historyForNpc.length > 0 ? historyForNpc.slice(-2) : [];
            if (relevantExchange.length === 0) {
                alert(`No recent significant dialogue to submit to memory for ${npcNameSafe}.`);
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `No recent dialogue for memory submission.`, "system-error");
                if (buttonElement) buttonElement.disabled = false;
                return;
            }
            payloadSpecifics.dialogue_exchange = relevantExchange.map(entry => `${entry.speaker}: ${entry.text}`).join('\n');
            payloadSpecifics.scene_context_for_memory = currentSceneContext;
        }
        try {
            if (buttonElement) buttonElement.disabled = true;
            updatePresentPlayerCharacters();
            const apiPayload = {
                npc_id: npc._id, action_type: actionType, payload: payloadSpecifics,
                scene_description: currentSceneContext,
                history: (conversationHistory[npc._id] || []).slice(-10), 
                present_player_characters: presentPlayerCharacters
            };
            const response = await fetch('/api/dialogue/npc_action', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(apiPayload) });
            if (buttonElement) buttonElement.disabled = false;
            const responseData = await response.json();
            if (!response.ok) throw new Error(responseData.error || responseData.message || `Action '${actionType}' failed with status ${response.status}`);
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", responseData.message || `Action '${escapeForHtml(actionType)}' for ${npcNameSafe} processed.`, "system-success");
            if (responseData.data) {
                if (responseData.action === "next_topic" || responseData.action === "regenerate_topics") {
                    if (responseData.data.new_topics && responseData.data.new_topics.length > 0) displayDialogueOptionsForNpc(npc._id, responseData.data.new_topics, "Suggested Topics (click for NPC to elaborate):", "topic");
                    else addDialogueEntryToNpcLog(npc._id, "SYSTEM", "No new topics were generated.", "system-info");
                } else if (responseData.action === "show_top5_options") {
                    if (responseData.data.dialogue_options && responseData.data.dialogue_options.length > 0) displayDialogueOptionsForNpc(npc._id, responseData.data.dialogue_options, "AI Suggested Next Lines (click to make NPC say):", "dialogue_line");
                    else addDialogueEntryToNpcLog(npc._id, "SYSTEM", "No dialogue options were generated.", "system-info");
                }
            }
        } catch (error) {
            console.error(`Error during NPC action '${actionType}' for ${npcNameSafe}:`, error);
            addDialogueEntryToNpcLog(npc._id, "SYSTEM", `Error with action '${escapeForHtml(actionType)}': ${error.message}`, "system-error");
            if (buttonElement) buttonElement.disabled = false;
        }
    }

    function updatePresentPlayerCharacters() {
        presentPlayerCharacters = [];
        if (playerCharacterListUl) {
            const checkboxes = playerCharacterListUl.querySelectorAll('input[name="player_character_present"]:checked');
            checkboxes.forEach(checkbox => presentPlayerCharacters.push(checkbox.value));
        }
        console.log("Scene.js: Updated Present PCs:", presentPlayerCharacters);
    }

    function handleSceneStartOrNarration(isInitialNarration = false) {
        const narrationInput = (isInitialNarration ? sceneDescriptionTextarea.value : ongoingNarrationTextarea.value).trim();
        if (sceneParticipantNpcs.length === 0 && selectedNpcIdsForScene.length > 0) { 
            alert('Scene NPCs are selected but not loaded. Check console for errors.'); return; 
        }
        // Allow scene start if no NPCs are selected, for GM-only narration or PC-to-PC.
        // if (sceneParticipantNpcs.length === 0 && selectedNpcIdsForScene.length === 0) { 
        //     alert('No NPCs are part of the scene. Please select NPCs from the dashboard and ensure they load.'); return; 
        // }
        
        if (!narrationInput) {
            alert(isInitialNarration ? 'Please describe the initial scene before starting.' : 'Please enter some narration or player action.');
            (isInitialNarration ? sceneDescriptionTextarea : ongoingNarrationTextarea).focus(); return;
        }

        if (isInitialNarration) {
            currentSceneContext = narrationInput; 
        } else {
            currentSceneContext += `\n\nGM Narration/Player Action: ${narrationInput}`; 
        }
        currentSceneDescriptionDisplay.textContent = `Current Scene: ${escapeForHtml(currentSceneContext.substring(0, 150))}...`;
        updatePresentPlayerCharacters(); 

        if(sceneParticipantNpcs.length > 0) {
            sceneParticipantNpcs.forEach(npc => {
                if (isInitialNarration) { 
                    const logContainer = document.getElementById(`chat-log-${npc._id}`);
                    if(logContainer) logContainer.innerHTML = ''; 
                    conversationHistory[npc._id] = [{ speaker: "SYSTEM", text: `Initial scene context: "${currentSceneContext}"`, type: "system" }];
                }
                addDialogueEntryToNpcLog(npc._id, "SYSTEM", `${isInitialNarration ? 'Initial S' : 'S'}cene Update: "${escapeForHtml(narrationInput.substring(0,100))}..."`, "system");
            });

            sceneParticipantNpcs.forEach((npc, index) => {
                addDialogueEntryToNpcLog(npc._id, npc.name, `<i>...formulating a response to the latest update...</i>`, "npc-thinking");
                setTimeout(() => fetchNpcReaction(npc, narrationInput), index * 700 + 400); 
            });
        } else {
            console.log("Scene started/updated without any active NPCs to react.");
        }

        if (isInitialNarration) sceneDescriptionTextarea.value = ""; 
        ongoingNarrationTextarea.value = ""; 
    }

    startSceneButton.addEventListener('click', () => handleSceneStartOrNarration(true));
    submitOngoingNarrationButton.addEventListener('click', () => handleSceneStartOrNarration(false));

    async function fetchNpcReaction(npc, latestNarrationOrAction) {
        const npcId = npc._id;
        const npcLogContainer = document.getElementById(`chat-log-${npcId}`);
        if (npcLogContainer) { 
            const thinkingMsg = npcLogContainer.querySelector('.chat-entry.npc-thinking');
            if (thinkingMsg) thinkingMsg.remove();
        }
        try {
            updatePresentPlayerCharacters(); 
            const payload = {
                npc_id: npcId, scene_context: currentSceneContext, 
                latest_narration: latestNarrationOrAction, 
                history: (conversationHistory[npcId] || []).slice(-10),
                present_player_characters: presentPlayerCharacters
            };
            const response = await fetch('/api/dialogue/generate_npc_line', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (!response.ok) {
                let errDetail = "NPC reaction failed.";
                try { const errData = await response.json(); errDetail = errData.detail || errData.error || `Server responded with ${response.status}`; } catch (e) { errDetail = `Server responded with ${response.status} and non-JSON error.`; }
                throw new Error(errDetail);
            }
            const data = await response.json();
            if (data.dialogue_text) addDialogueEntryToNpcLog(npcId, npc.name, data.dialogue_text, "npc");
            else addDialogueEntryToNpcLog(npcId, "SYSTEM", "AI could not generate a response for " + escapeForHtml(npc.name), "system-error");
        } catch (error) {
            console.error(`Error fetching reaction for ${escapeForHtml(npc.name)} (ID: ${npcId}):`, error);
            addDialogueEntryToNpcLog(npcId, "SYSTEM", `Error for ${escapeForHtml(npc.name)}: ${error.message}`, "system-error");
        }
    }

    function addDialogueEntryToNpcLog(npcId, speakerName, text, type = "npc") {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer) { console.error(`Chat log container for NPC ID ${npcId} not found! Cannot add entry.`); return; }
        const placeholder = logContainer.querySelector('.log-placeholder');
        if (placeholder) placeholder.remove(); 
        const entryDiv = document.createElement('div');
        const typeClass = type.startsWith('system') ? 'system-message' : type;
        entryDiv.classList.add('chat-entry', typeClass);
        if (type === "gm-action-log" || (type === "system-info" && speakerName === "GM Action") || speakerName === "GM Choice") {
             entryDiv.classList.add('gm-action-entry');
        }

        let bubbleHtml = `<div class="chat-bubble">`;
        const speakerNameSafe = escapeForHtml(speakerName);
        if (type !== "npc" || type === "npc-thinking" || type.startsWith("system") || entryDiv.classList.contains('gm-action-entry')) {
            bubbleHtml += `<span class="speaker-name">${speakerNameSafe}:</span>`;
        }
        const displayText = (type === "npc-thinking" && text.includes("<i>")) ? text : escapeForHtml(text);
        bubbleHtml += `<p class="dialogue-text">${displayText.replace(/\n/g, '<br>')}</p></div>`; 
        entryDiv.innerHTML = bubbleHtml;

        const isSignificantForHistory = (type === "npc" || type === "gm" || speakerName === "GM Choice" ||
            (type === "system" && (text.toLowerCase().includes("scene context:") || text.toLowerCase().includes("scene update:") ) ) );
        
        if (isSignificantForHistory && !(type === "system-info" && speakerName === "GM Action")) { 
             if (!conversationHistory[npcId]) conversationHistory[npcId] = [];
             conversationHistory[npcId].push({ speaker: speakerName, text: text, type: type }); 
        }
        logContainer.appendChild(entryDiv);
        logContainer.scrollTop = logContainer.scrollHeight; 
    }

    function displayDialogueOptionsForNpc(npcId, options, title = "Suggested Options:", optionType = "generic") {
        const logContainer = document.getElementById(`chat-log-${npcId}`);
        if (!logContainer || !options || options.length === 0) return;
        const existingOptions = logContainer.querySelector('.dialogue-options-container');
        if (existingOptions) existingOptions.remove(); 
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'dialogue-options-container';
        const titleEl = document.createElement('p');
        titleEl.className = 'dialogue-options-title';
        titleEl.textContent = escapeForHtml(title);
        optionsContainer.appendChild(titleEl);
        options.forEach(optionText => {
            const optButton = document.createElement('button');
            optButton.className = 'jrpg-button-small dialogue-option';
            optButton.textContent = escapeForHtml(optionText.length > 70 ? optionText.substring(0, 67) + "..." : optionText); 
            optButton.title = escapeForHtml(optionText); 
            optButton.addEventListener('click', () => {
                const npcToRespond = sceneParticipantNpcs.find(p => p._id === npcId);
                if (npcToRespond) {
                    if (optionType === "dialogue_line") { 
                        addDialogueEntryToNpcLog(npcId, "GM Choice", `GM selected line for ${escapeForHtml(npcToRespond.name)}: "${escapeForHtml(optionText)}"`, "gm-action-log");
                        addDialogueEntryToNpcLog(npcId, npcToRespond.name, optionText, "npc"); 
                    } else if (optionType === "topic") { 
                        addDialogueEntryToNpcLog(npcId, "GM Choice", `GM prompts ${escapeForHtml(npcToRespond.name)} to discuss: "${escapeForHtml(optionText)}"`, "gm-action-log");
                        addDialogueEntryToNpcLog(npcId, npcToRespond.name, `<i>...preparing to discuss "${escapeForHtml(optionText.substring(0,30))}..."</i>`, "npc-thinking");
                        fetchNpcReaction(npcToRespond, `Please elaborate on the topic: "${optionText}"`); 
                    }
                }
                optionsContainer.remove(); 
            });
            optionsContainer.appendChild(optButton);
        });
        logContainer.appendChild(optionsContainer);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    console.log('Scene.js: Script loaded and all event listeners should be active.');
}); // End of DOMContentLoaded