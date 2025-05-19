// static/js/app.js - Modified
document.addEventListener('DOMContentLoaded', async () => { // Make it async
    const npcSelectionArea = document.getElementById('npc-selection-area');
    const selectedNpcListElement = document.getElementById('selected-npc-list');
    const noNpcsSelectedElement = document.getElementById('no-npcs-selected');
    const proceedToSceneButton = document.getElementById('proceed-to-scene-button');

    // Check login status first
    try {
        const statusResponse = await fetch('/api/auth/status');
        const statusResult = await statusResponse.json();
        if (!statusResponse.ok || !statusResult.logged_in) {
            // Not logged in, or error checking status
            window.location.href = '/login'; // Redirect to login
            return; // Stop further execution of this script
        }
        // User is logged in, proceed to load their NPCs
        // statusResult.user contains user info if needed
    } catch (e) {
        console.error("Error checking auth status on NPC selection page", e);
        window.location.href = '/login'; // Redirect on error
        return;
    }

    let allUserNPCs = []; // To store fetched NPCs for the user
    let selectedNPCs = new Map();

    // ... (rest of the DOM element checks) ...

    // Fetch User-Specific NPCs
    fetch('/api/npcs') // This now fetches user's NPCs due to @login_required and backend logic
        .then(response => {
            if (response.status === 401) { // Unauthorized
                window.location.href = '/login';
                return Promise.reject('User not authenticated');
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(npcs => {
            allUserNPCs = npcs;
            if (!Array.isArray(allUserNPCs)) {
                console.error('Fetched NPC data is not an array:', allUserNPCs);
                npcSelectionArea.innerHTML = '<p>Error: NPC data format is incorrect.</p>';
                return;
            }
            if (allUserNPCs.length === 0) {
                npcSelectionArea.innerHTML = '<p>You have no NPCs. Please upload some from your dashboard.</p> <a href="/dashboard" class="jrpg-button-small">Go to Dashboard</a>';
                return;
            }
            displayNPCs(allUserNPCs);
        })
        .catch(error => {
            if (error !== 'User not authenticated') { // Avoid double logging if redirected
                console.error('Error fetching user NPCs:', error);
                npcSelectionArea.innerHTML = `<p>Error loading your NPCs: ${error.message}.</p>`;
            }
        });

    // displayNPCs function remains largely the same,
    // but ensure personality_traits is handled as a string
    function displayNPCs(npcs) {
        npcSelectionArea.innerHTML = ''; // Clear loading message

        npcs.forEach(npc => {
            const card = document.createElement('div');
            card.className = 'npc-card';
            card.dataset.npcId = npc._id; 

            const npcInitials = npc.name ? npc.name.substring(0, 2).toUpperCase().replace(/[^A-Z0-9]/g, '') : '??';
            const placeholderBgColor = stringToColor(npc.name || "defaultNPC");
            const placeholderTextColor = 'FFFFFF';
            const placeholderImageUrl = `https://placehold.co/80x80/<span class="math-inline">\{placeholderBgColor\}/</span>{placeholderTextColor}?text=${npcInitials}&font=source-sans-pro`;

            card.innerHTML = `
                <div class="npc-portrait-container">
                    <img src="${placeholderImageUrl}" alt="Portrait of <span class="math-inline">\{npc\.name \|\| 'NPC'\}" class\="npc\-portrait" onerror\="this\.src\='https\://placehold\.co/80x80/CCCCCC/FFFFFF?text\=ERR&font\=lora'; this\.onerror\=null;"\>
                    </div>
<div class="npc-details">
<h3>{npc.name || 'Unnamed NPC'}</h3>
<p><em>${npc.appearance || 'No description available.'}</em></p>
${npc.personality_traits && npc.personality_traits.trim().length > 0 ? <p>Traits: ${npc.personality_traits}</p> : '<p>Traits: Not specified.</p>'}
</div>
`;
// ... (rest of displayNPCs and other functions: toggleNPCSelection, updateSelectedNPCListUI, updateProceedButtonState, proceedToSceneButton, stringToColor) ...
// Event listener for selecting/deselecting NPC
card.addEventListener('click', () => {
toggleNPCSelection(npc, card);
});
npcSelectionArea.appendChild(card);
});
}
// ... copy the rest of the functions from your original app.js ...
function toggleNPCSelection(npc, cardElement) {
const npcId = npc._id;
if (selectedNPCs.has(npcId)) {
selectedNPCs.delete(npcId);
cardElement.classList.remove('selected');
} else {
selectedNPCs.set(npcId, npc); // Store the whole NPC object if needed later
cardElement.classList.add('selected');
}
updateSelectedNPCListUI();
updateProceedButtonState();
}
function updateSelectedNPCListUI() {
        selectedNpcListElement.innerHTML = ''; // Clear current list
        if (selectedNPCs.size === 0) {
            selectedNpcListElement.appendChild(noNpcsSelectedElement);
        } else {
            selectedNPCs.forEach(npc => {
                const listItem = document.createElement('li');
                listItem.textContent = npc.name;
                selectedNpcListElement.appendChild(listItem);
            });
        }
    }

    function updateProceedButtonState() {
        proceedToSceneButton.disabled = selectedNPCs.size === 0;
    }

    proceedToSceneButton.addEventListener('click', () => {
        if (selectedNPCs.size > 0) {
            const selectedIds = Array.from(selectedNPCs.keys());
            window.location.href = `/scene?npcs=${selectedIds.join(',')}`;
        }
    });
    
    function stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash; 
        }
        let color = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '00000'.substring(0, 6 - color.length) + color;
    }

    // Initial UI updates
    // updateSelectedNPCListUI(); // Called after NPCs are loaded now
    // updateProceedButtonState(); // Called after NPCs are loaded now
});

```