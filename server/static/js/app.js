// static/js/app.js - For NPC Selector Page (index.html)
document.addEventListener('DOMContentLoaded', async () => {
    const npcSelectionArea = document.getElementById('npc-selection-area');
    const selectedNpcListElement = document.getElementById('selected-npc-list');
    const noNpcsSelectedElement = document.getElementById('no-npcs-selected');
    const proceedToSceneButton = document.getElementById('proceed-to-scene-button');
    // Attempt to find the loading message element within the npcSelectionArea
    const loadingMessageElement = npcSelectionArea ? npcSelectionArea.querySelector('.loading-message') : null;

    // Ensure essential elements exist
    if (!npcSelectionArea || !selectedNpcListElement || !proceedToSceneButton || !noNpcsSelectedElement) {
        console.error('CRITICAL UI ERROR: One or more essential UI elements for NPC selection are missing from index.html! Ensure npc-selection-area, selected-npc-list, no-npcs-selected, and proceed-to-scene-button exist.');
        if (npcSelectionArea) {
            npcSelectionArea.innerHTML = '<p style="color:red; text-align:center;">Error: UI setup incomplete. Please check console and HTML structure of index.html.</p>';
        }
        // Disable button if elements are missing to prevent further errors
        if(proceedToSceneButton) proceedToSceneButton.disabled = true;
        return;
    }
    
    let allAvailableNPCs = []; 
    let selectedNPCs = new Map();

    // Initial UI state
    updateSelectedNPCListUI(); // Show "None yet"
    updateProceedButtonState(); // Disable button

    // Check login status first
    try {
        const statusResponse = await fetch('/api/auth/status');
        if (!statusResponse.ok) {
            console.error('Auth status check failed with status:', statusResponse.status);
            if(loadingMessageElement) loadingMessageElement.textContent = 'Authentication error.';
            window.location.href = '/login'; // Redirect if status check itself fails
            return;
        }
        const statusResult = await statusResponse.json();
        if (!statusResult.logged_in) {
            window.location.href = '/login'; // Redirect to login if not authenticated
            return; 
        }
        // User is logged in, can proceed.
    } catch (e) {
        console.error("Error checking auth status on NPC selection page:", e);
        if(loadingMessageElement) loadingMessageElement.textContent = 'Error checking authentication.';
        // Potentially redirect to login, or show an error that user needs to be logged in.
        // For now, we'll let it proceed to fetch NPCs, which should then fail with 401 if session is truly gone.
        // window.location.href = '/login'; 
        // return;
    }

    // Fetch Combined NPCs (Global + User's Own)
    try {
        if(loadingMessageElement) loadingMessageElement.style.display = 'block'; 

        const response = await fetch('/api/npcs'); 
        if (!response.ok) {
            if (response.status === 401) { 
                if(loadingMessageElement) loadingMessageElement.textContent = 'Authentication required.';
                window.location.href = '/login';
                return Promise.reject('User not authenticated, redirecting.');
            }
            throw new Error(`HTTP error fetching NPCs! Status: ${response.status}`);
        }
        allAvailableNPCs = await response.json();

        if(loadingMessageElement) loadingMessageElement.style.display = 'none';

        if (!Array.isArray(allAvailableNPCs)) {
            console.error('Fetched NPC data is not an array:', allAvailableNPCs);
            npcSelectionArea.innerHTML = '<p style="color:red;">Error: NPC data format is incorrect.</p>';
            return;
        }
        if (allAvailableNPCs.length === 0) {
            npcSelectionArea.innerHTML = '<p>No NPCs available. You can upload your own NPCs from the dashboard, or check if default NPCs are loaded in the database.</p> <a href="/dashboard" class="jrpg-button-small">Go to Dashboard</a>';
            return;
        }
        displayNPCs(allAvailableNPCs);
    } catch (error) {
        console.error('Error fetching or processing NPCs on selection page:', error);
        if (error.message !== 'User not authenticated, redirecting.') {
            if(loadingMessageElement) loadingMessageElement.style.display = 'none';
            npcSelectionArea.innerHTML = `<p style="color:red;">Error loading NPCs: ${error.message}.</p>`;
        }
    }

    function displayNPCs(npcs) {
        if (!npcSelectionArea) return; // Guard against missing element
        npcSelectionArea.innerHTML = ''; 

        npcs.forEach(npc => {
            const card = document.createElement('div');
            card.className = 'npc-card';
            card.dataset.npcId = npc._id; 

            const npcInitials = npc.name ? npc.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC"); 
            const placeholderTextColor = 'FFFFFF';
            const placeholderImageUrl = `https://placehold.co/80x80/${placeholderBgColor}/${placeholderTextColor}?text=${npcInitials}&font=source-sans-pro`;

            const traitsDisplay = npc.personality_traits && typeof npc.personality_traits === 'string' && npc.personality_traits.trim().length > 0 
                ? `<p>Traits: ${npc.personality_traits}</p>` 
                : '<p>Traits: Not specified.</p>';

            card.innerHTML = `
                <div class="npc-portrait-container">
                    <img src="${placeholderImageUrl}" alt="Portrait of ${npc.name || 'NPC'}" class="npc-portrait" onerror="this.src='https://placehold.co/80x80/CCCCCC/FFFFFF?text=ERR&font=lora'; this.onerror=null;">
                </div>
                <div class="npc-details">
                    <h3>${npc.name || 'Unnamed NPC'}</h3>
                    <p><em>${npc.appearance || 'No description available.'}</em></p>
                    ${traitsDisplay}
                </div>
            `;
            card.addEventListener('click', () => {
                toggleNPCSelection(npc, card);
            });
            npcSelectionArea.appendChild(card);
        });
        updateSelectedNPCListUI(); 
        updateProceedButtonState();
    }

    function toggleNPCSelection(npc, cardElement) {
        const npcId = npc._id;
        if (selectedNPCs.has(npcId)) {
            selectedNPCs.delete(npcId);
            cardElement.classList.remove('selected');
        } else {
            selectedNPCs.set(npcId, npc);
            cardElement.classList.add('selected');
        }
        updateSelectedNPCListUI();
        updateProceedButtonState();
    }

    function updateSelectedNPCListUI() {
        if (!selectedNpcListElement || !noNpcsSelectedElement) return;
        selectedNpcListElement.innerHTML = ''; 
        if (selectedNPCs.size === 0) {
            noNpcsSelectedElement.style.display = 'list-item'; 
            selectedNpcListElement.appendChild(noNpcsSelectedElement);
        } else {
            noNpcsSelectedElement.style.display = 'none'; 
            selectedNPCs.forEach(npc => {
                const listItem = document.createElement('li');
                listItem.textContent = npc.name;
                selectedNpcListElement.appendChild(listItem);
            });
        }
    }

    function updateProceedButtonState() {
        if (!proceedToSceneButton) return;
        proceedToSceneButton.disabled = selectedNPCs.size === 0;
    }

    if (proceedToSceneButton) {
        proceedToSceneButton.addEventListener('click', () => {
            if (selectedNPCs.size > 0) {
                const selectedIds = Array.from(selectedNPCs.keys());
                window.location.href = `/scene?npcs=${selectedIds.join(',')}`;
            }
        });
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