// srwmay08/bugbearbanter/BugbearBanter-cf73d42aed67696601941e44943cc5db45c8e493/server/static/js/dashboard.js
// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', async () => {
    const welcomeMessage = document.getElementById('welcome-message');
    const npcUploadForm = document.getElementById('npc-upload-form');
    const npcFileInput = document.getElementById('npc-file-input');
    const uploadMessage = document.getElementById('upload-message');
    const userNpcListDiv = document.getElementById('user-npc-list');
    const userPcListDiv = document.getElementById('user-pc-list'); // Added for PCs
    const logoutButton = document.getElementById('logout-button');
    const goToSceneSetupButton = document.getElementById('go-to-scene-setup');
    const loadWorldInfoButton = document.getElementById('load-world-info-button');
    const worldInfoDisplay = document.getElementById('world-info-display');

    // Modal elements for editing NPCs (now Characters)
    const editNpcModal = document.getElementById('edit-npc-modal');
    const editNpcForm = document.getElementById('edit-npc-form');
    const cancelEditNpcButton = document.getElementById('cancel-edit-npc');
    const npcIdField = document.getElementById('edit-npc-id'); // Renamed from editNpcIdField for consistency

    // World Info Modal Elements (ensure these IDs are unique if shared across modals)
    const worldItemModal = document.getElementById('world-item-modal');
    const worldItemForm = document.getElementById('world-item-form');
    const cancelWorldItemButton = document.getElementById('cancel-world-item-modal-button');
    const worldItemIdField = document.getElementById('edit-world-item-id-field');
    const worldItemTypeField = document.getElementById('edit-world-item-type-field');
    const worldItemModalTitle = document.getElementById('world-item-modal-title');
    const worldItemFieldsContainer = document.getElementById('world-item-fields-container');


    let currentUser = null;

    // Check login status and initialize page
    try {
        const statusResponse = await fetch('/api/auth/status');
        if (!statusResponse.ok) {
            console.error('Auth status check failed with status:', statusResponse.status);
            window.location.href = '/login';
            return;
        }
        const statusResult = await statusResponse.json();
        if (statusResult.logged_in && statusResult.user) {
            currentUser = statusResult.user;
            if (welcomeMessage) welcomeMessage.textContent = `Welcome, ${currentUser.name || currentUser.email}!`;
            loadUserCharacters(); // Load Characters (PCs and NPCs)
        } else {
            window.location.href = '/login';
            return;
        }
    } catch (e) {
        console.error("Error checking auth status on dashboard:", e);
        window.location.href = '/login';
        return;
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/auth/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = '/login';
                } else {
                    alert('Logout failed. Please try again.');
                }
            } catch (error) {
                console.error('Logout error:', error);
                alert('An error occurred during logout.');
            }
        });
    }

    if (npcUploadForm && npcFileInput) {
        npcUploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            if(uploadMessage) uploadMessage.textContent = 'Uploading...';
            if(uploadMessage) uploadMessage.style.color = 'black';
            const file = npcFileInput.files[0];

            if (!file) {
                if(uploadMessage) uploadMessage.textContent = 'Please select a JSON file.';
                if(uploadMessage) uploadMessage.style.color = 'red';
                return;
            }

            const formData = new FormData();
            formData.append('npc_file', file);

            try {
                const response = await fetch('/api/npcs/upload', {
                    method: 'POST',
                    body: formData,
                });
                const result = await response.json();
                if (response.ok && response.status === 201) {
                    if(uploadMessage) uploadMessage.textContent = result.message || 'Character uploaded successfully!';
                    if(uploadMessage) uploadMessage.style.color = 'green';
                    npcFileInput.value = '';
                    loadUserCharacters(); // Reload all characters
                } else {
                    if(uploadMessage) uploadMessage.textContent = result.error || `Upload failed (Status: ${response.status}). ${result.details || ''}`;
                    if(uploadMessage) uploadMessage.style.color = 'red';
                }
            } catch (error) {
                if(uploadMessage) uploadMessage.textContent = 'An error occurred during upload.';
                if(uploadMessage) uploadMessage.style.color = 'red';
                console.error('Upload error:', error);
            }
        });
    }

    async function loadUserCharacters() {
        if (!currentUser || (!userNpcListDiv && !userPcListDiv)) return;

        if (userPcListDiv) userPcListDiv.innerHTML = '<p>Loading PCs...</p>';
        if (userNpcListDiv) userNpcListDiv.innerHTML = '<p>Loading NPCs...</p>';

        try {
            const response = await fetch('/api/npcs'); // This API now returns all characters with character_type
            if (!response.ok) {
                if (response.status === 401) { window.location.href = '/login'; return; }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const allAccessibleCharacters = await response.json();

            if (allAccessibleCharacters.length === 0) {
                if (userPcListDiv) userPcListDiv.innerHTML = '<p>No PCs found. Try uploading one.</p>';
                if (userNpcListDiv) userNpcListDiv.innerHTML = '<p>No NPCs found. Try uploading one.</p>';
                return;
            }

            let pcHtml = '<ul>';
            let npcHtml = '<ul>';
            let pcCount = 0;
            let npcCount = 0;

            allAccessibleCharacters.forEach(char => {
                let ownerTag = "";
                let canEditDelete = false;
                if (char.user_id && currentUser && char.user_id === currentUser._id) {
                    ownerTag = " (Uploaded by you)";
                    canEditDelete = true;
                } else if (!char.user_id) {
                    ownerTag = ` (Default ${char.character_type || 'Character'})`;
                }

                const charHtml = `<li data-char-id="${char._id}">
                                    <span class="char-name-display">${char.name || 'Unnamed Character'}</span> ${ownerTag}
                                    <span class="char-actions">
                                    ${canEditDelete ?
                                        `<button class="jrpg-button-small btn-edit-char" data-id="${char._id}">Edit</button>
                                         <button class="jrpg-button-small btn-delete-char" data-id="${char._id}" data-name="${char.name || 'this character'}">Delete</button>`
                                        : ''}
                                    </span>
                                 </li>`;

                if (char.character_type === "PC") {
                    pcHtml += charHtml;
                    pcCount++;
                } else { // Default to NPC if not PC or type is missing/invalid
                    npcHtml += charHtml;
                    npcCount++;
                }
            });
            pcHtml += '</ul>';
            npcHtml += '</ul>';

            if (userPcListDiv) {
                if (pcCount > 0) userPcListDiv.innerHTML = pcHtml;
                else userPcListDiv.innerHTML = '<p>No PCs found. Try uploading one (ensure "character_type": "PC" in JSON).</p>';
            }
            if (userNpcListDiv) {
                if (npcCount > 0) userNpcListDiv.innerHTML = npcHtml;
                else userNpcListDiv.innerHTML = '<p>No NPCs found. Try uploading one (or ensure "character_type": "NPC").</p>';
            }

            document.querySelectorAll('.btn-delete-char').forEach(button => {
                button.addEventListener('click', handleDeleteChar);
            });
            document.querySelectorAll('.btn-edit-char').forEach(button => {
                button.addEventListener('click', handleOpenEditCharModal);
            });

        } catch (error) {
            console.error('Error loading accessible characters:', error);
            if (userPcListDiv) userPcListDiv.innerHTML = '<p style="color:red;">Could not load PCs.</p>';
            if (userNpcListDiv) userNpcListDiv.innerHTML = '<p style="color:red;">Could not load NPCs.</p>';
        }
    }


    async function handleDeleteChar(event) { // Renamed from handleDeleteNpc
        const charId = event.target.dataset.id;
        const charName = event.target.dataset.name;
        if (!confirm(`Are you sure you want to delete ${charName}? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/npcs/${charId}`, { method: 'DELETE' }); // API endpoint remains /api/npcs/
            const result = await response.json();
            if (response.ok) {
                alert(result.message || 'Character deleted successfully.');
                loadUserCharacters(); // Reload all characters
            } else {
                alert(`Error deleting character: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Delete character error:', error);
            alert('An error occurred while deleting the character.');
        }
    }

    async function handleOpenEditCharModal(event) { // Renamed from handleOpenEditNpcModal
        const charId = event.target.dataset.id;
        if (!editNpcModal || !editNpcForm || !npcIdField) { // npcIdField is the hidden input for ID
            console.error("Edit Character modal or form elements not found in HTML!");
            return;
        }

        try {
            const response = await fetch(`/api/npcs/${charId}`); // API endpoint remains /api/npcs/
            if (!response.ok) throw new Error(`Failed to fetch character details (status ${response.status})`);
            const charData = await response.json();

            npcIdField.value = charData._id; // Set the hidden ID field
            // Populate the form based on charData keys matching form input names
            for (const key in charData) {
                if (editNpcForm.elements[key]) {
                    if (editNpcForm.elements[key].type === 'textarea' || editNpcForm.elements[key].type === 'text' || editNpcForm.elements[key].type === 'select-one') {
                        editNpcForm.elements[key].value = charData[key] || '';
                    }
                }
            }
            // If you add character_type to the form:
            // if(editNpcForm.elements['character_type']) editNpcForm.elements['character_type'].value = charData.character_type || 'NPC';

            editNpcModal.style.display = 'block';
        } catch (error) {
            console.error("Error fetching character for edit:", error);
            alert("Could not load character data for editing.");
        }
    }

    if(editNpcForm){ // For Character Edit Modal
        editNpcForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const charId = npcIdField.value; // Get ID from hidden field
            const formData = new FormData(editNpcForm);
            const dataToUpdate = {};
            const editableFields = [
                'name', 'race', 'class', 'alignment', 'age',
                'personality_traits', 'ideals', 'bonds', 'flaws',
                'backstory', 'motivations', 'speech_patterns',
                'mannerisms', 'past_situation', 'current_situation',
                'relationships_with_pcs', 'appearance', 'character_type' // Add character_type if it's in the form
            ];
            for (const [key, value] of formData.entries()) {
                if (editableFields.includes(key)) {
                    dataToUpdate[key] = value;
                }
            }

            try {
                const response = await fetch(`/api/npcs/${charId}`, { // API endpoint remains /api/npcs/
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dataToUpdate),
                });
                const result = await response.json();
                if (response.ok) {
                    alert(result.message || 'Character updated successfully!');
                    if(editNpcModal) editNpcModal.style.display = 'none';
                    loadUserCharacters(); // Reload all characters
                } else {
                    alert(`Error updating character: ${result.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Update character error:', error);
                alert('An error occurred while updating the character.');
            }
        });
    }

    if(cancelEditNpcButton){ // For Character Edit Modal
        cancelEditNpcButton.addEventListener('click', () => {
            if (editNpcModal) editNpcModal.style.display = 'none';
        });
    }

    // --- World Info Section Logic (remains largely the same) ---
    if (loadWorldInfoButton && worldInfoDisplay) {
        loadWorldInfoButton.addEventListener('click', fetchAndRenderWorldInfo);
    }

    async function fetchAndRenderWorldInfo() {
        if (!worldInfoDisplay) return;
        worldInfoDisplay.innerHTML = '<p>Loading world information...</p>';
        try {
            const response = await fetch('/api/world-info/all');
            if (!response.ok) {
                if (response.status === 401) { window.location.href = '/login'; return; }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const worldData = await response.json();
            renderWorldInfo(worldData);
        } catch (error) {
            console.error('Error loading world information:', error);
            worldInfoDisplay.innerHTML = '<p style="color:red;">Could not load world information.</p>';
        }
    }

    function renderWorldInfo(worldData) {
        if (!worldData || !worldInfoDisplay) {
            if(worldInfoDisplay) worldInfoDisplay.innerHTML = '<p>No world data received.</p>';
            return;
        }
        let html = '';

        // --- Events ---
        html += `<div class="world-info-category"><h3>Events <button class="jrpg-button-small btn-create-world-item" data-type="events">Add Event</button></h3>`;
        if (worldData.events && worldData.events.length > 0) {
            html += '<ul class="world-info-list" id="events-list">';
            worldData.events.forEach(event => {
                html += `<li data-id="${event._id}">
                            <div><strong>${event.name || 'Unnamed Event'}</strong></div>
                            <div><em>Description:</em> ${event.description || 'N/A'}</div>
                            <div><em>Impact:</em> ${event.impact || 'N/A'}</div>
                            <div><em>Status:</em> ${event.status || 'N/A'}</div>
                            <div class="world-item-actions">
                                <button class="jrpg-button-small btn-edit-world-item" data-id="${event._id}" data-type="events">Edit</button>
                                <button class="jrpg-button-small btn-delete-world-item" data-id="${event._id}" data-type="events" data-name="${event.name || 'this event'}">Delete</button>
                            </div>
                         </li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No events loaded.</p>';
        }
        html += '</div>';

        // --- Locations ---
        html += `<div class="world-info-category"><h3>Locations <button class="jrpg-button-small btn-create-world-item" data-type="locations">Add Location</button></h3>`;
        if (worldData.locations && worldData.locations.length > 0) {
            html += '<ul class="world-info-list" id="locations-list">';
            worldData.locations.forEach(loc => {
                html += `<li data-id="${loc._id}">
                            <div><strong>${loc.name || 'Unnamed Location'}</strong> (${loc.type || 'N/A'})</div>
                            <div><em>Description:</em> ${loc.description || 'N/A'}</div>
                            <div><em>Mood:</em> ${loc.current_mood || 'N/A'}</div>
                            <div><em>Key Features:</em> ${Array.isArray(loc.key_features) ? loc.key_features.join(', ') : (loc.key_features || 'N/A')}</div>
                            <div class="world-item-actions">
                                <button class="jrpg-button-small btn-edit-world-item" data-id="${loc._id}" data-type="locations">Edit</button>
                                <button class="jrpg-button-small btn-delete-world-item" data-id="${loc._id}" data-type="locations" data-name="${loc.name || 'this location'}">Delete</button>
                            </div>
                         </li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No locations loaded.</p>';
        }
        html += '</div>';

        // --- Religions ---
        html += `<div class="world-info-category"><h3>Religions/Deities <button class="jrpg-button-small btn-create-world-item" data-type="religions">Add Religion</button></h3>`;
        if (worldData.religions && worldData.religions.length > 0) {
            html += '<ul class="world-info-list" id="religions-list">';
            worldData.religions.forEach(rel => {
                html += `<li data-id="${rel._id}">
                            <div><strong>${rel.name || 'Unnamed Entity'}</strong> (${rel.type || 'N/A'})</div>
                            <div><em>Description:</em> ${rel.description || 'N/A'}</div>
                            <div><em>Domains:</em> ${Array.isArray(rel.domains) ? rel.domains.join(', ') : (rel.domains || 'N/A')}</div>
                            <div><em>Common Saying:</em> ${rel.common_saying || 'N/A'}</div>
                            <div class="world-item-actions">
                                <button class="jrpg-button-small btn-edit-world-item" data-id="${rel._id}" data-type="religions">Edit</button>
                                <button class="jrpg-button-small btn-delete-world-item" data-id="${rel._id}" data-type="religions" data-name="${rel.name || 'this entity'}">Delete</button>
                            </div>
                         </li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No religions/deities loaded.</p>';
        }
        html += '</div>';

        worldInfoDisplay.innerHTML = html;

        document.querySelectorAll('.btn-delete-world-item').forEach(button => {
            button.addEventListener('click', handleDeleteWorldItem);
        });
        document.querySelectorAll('.btn-edit-world-item').forEach(button => {
            button.addEventListener('click', handleOpenEditWorldItemModal);
        });
        document.querySelectorAll('.btn-create-world-item').forEach(button => {
            button.addEventListener('click', handleOpenCreateWorldItemModal);
        });
    }

    async function handleDeleteWorldItem(event) {
        const itemId = event.target.dataset.id;
        const itemType = event.target.dataset.type;
        const itemName = event.target.dataset.name;

        if (!confirm(`Are you sure you want to delete ${itemName}?`)) return;

        try {
            const response = await fetch(`/api/world-info/${itemType}/${itemId}`, { method: 'DELETE' });
            const result = await response.json();
            if (response.ok) {
                alert(result.message || `${capitalizeFirstLetter(itemType.slice(0,-1))} deleted.`);
                fetchAndRenderWorldInfo();
            } else {
                alert(`Error deleting: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error(`Delete ${itemType} error:`, error);
            alert(`An error occurred while deleting the ${itemType.slice(0,-1)}.`);
        }
    }

    function handleOpenCreateWorldItemModal(event) {
        const itemType = event.target.dataset.type;
        if (!worldItemModal || !worldItemForm || !worldItemFieldsContainer || !worldItemModalTitle || !worldItemIdField || !worldItemTypeField) {
            console.error("World item modal elements not found!");
            return;
        }

        worldItemModalTitle.textContent = `Create New ${capitalizeFirstLetter(itemType.slice(0,-1))}`;
        worldItemForm.reset();
        worldItemIdField.value = ''; // Clear ID for creation
        worldItemTypeField.value = itemType; // Set hidden type field
        populateWorldItemFormFields(itemType);
        worldItemModal.style.display = 'block';
    }

    async function handleOpenEditWorldItemModal(event) {
        const itemId = event.target.dataset.id;
        const itemType = event.target.dataset.type;
        if (!worldItemModal || !worldItemForm || !worldItemFieldsContainer || !worldItemModalTitle || !worldItemIdField || !worldItemTypeField) {
            console.error("World item modal elements not found!");
            return;
        }

        try {
            const response = await fetch(`/api/world-info/${itemType}/${itemId}`); // Fetch specific item
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({})); // try to get error detail
                 throw new Error(errorData.error || `Could not fetch item details for editing. Status: ${response.status}`);
            }
            const itemData = await response.json();


            if (!itemData) {
                alert("Could not find item details to edit.");
                return;
            }

            worldItemModalTitle.textContent = `Edit ${capitalizeFirstLetter(itemType.slice(0,-1))}`;
            worldItemForm.reset();
            worldItemIdField.value = itemData._id; // Set hidden ID field
            worldItemTypeField.value = itemType; // Set hidden type field
            populateWorldItemFormFields(itemType, itemData);
            worldItemModal.style.display = 'block';

        } catch (error) {
            console.error("Error preparing world item for edit:", error);
            alert(error.message || "Could not load item data for editing.");
        }
    }


    function populateWorldItemFormFields(itemType, data = {}) {
        if (!worldItemFieldsContainer) return;
        worldItemFieldsContainer.innerHTML = '';
        let fieldsHtml = '';
        // Common fields
        fieldsHtml += `
            <div class="form-group">
                <label for="world-item-name">Name:</label>
                <input type="text" id="world-item-name" name="name" class="jrpg-input" value="${data.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="world-item-description">Description:</label>
                <textarea id="world-item-description" name="description" class="jrpg-textarea" rows="3" required>${data.description || ''}</textarea>
            </div>
        `;
        // Type-specific fields
        if (itemType === 'events') {
            fieldsHtml += `
                <div class="form-group">
                    <label for="world-item-impact">Impact:</label>
                    <input type="text" id="world-item-impact" name="impact" class="jrpg-input" value="${data.impact || ''}">
                </div>
                <div class="form-group">
                    <label for="world-item-status">Status:</label>
                    <input type="text" id="world-item-status" name="status" class="jrpg-input" value="${data.status || 'Ongoing'}">
                </div>`;
        } else if (itemType === 'locations') {
            fieldsHtml += `
                <div class="form-group">
                    <label for="world-item-type-loc">Type:</label>
                    <input type="text" id="world-item-type-loc" name="type" class="jrpg-input" value="${data.type || ''}">
                </div>
                <div class="form-group">
                    <label for="world-item-mood">Current Mood:</label>
                    <input type="text" id="world-item-mood" name="current_mood" class="jrpg-input" value="${data.current_mood || ''}">
                </div>
                <div class="form-group">
                    <label for="world-item-keyfeatures">Key Features (comma-separated):</label>
                    <input type="text" id="world-item-keyfeatures" name="key_features" class="jrpg-input" value="${Array.isArray(data.key_features) ? data.key_features.join(', ') : (data.key_features || '')}">
                </div>`;
        } else if (itemType === 'religions') {
             fieldsHtml += `
                <div class="form-group">
                    <label for="world-item-type-rel">Type (e.g., Deity, Pantheon):</label>
                    <input type="text" id="world-item-type-rel" name="type" class="jrpg-input" value="${data.type || ''}">
                </div>
                 <div class="form-group">
                    <label for="world-item-domains">Domains (comma-separated):</label>
                    <input type="text" id="world-item-domains" name="domains" class="jrpg-input" value="${Array.isArray(data.domains) ? data.domains.join(', ') : (data.domains || '')}">
                </div>
                 <div class="form-group">
                    <label for="world-item-saying">Common Saying:</label>
                    <input type="text" id="world-item-saying" name="common_saying" class="jrpg-input" value="${data.common_saying || ''}">
                </div>`;
        }
        worldItemFieldsContainer.innerHTML = fieldsHtml;
    }

    if (worldItemForm) {
        worldItemForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const itemId = worldItemIdField.value;
            const itemType = worldItemTypeField.value;

            const formData = new FormData(worldItemForm);
            const dataToSubmit = {};

            for (const [key, value] of formData.entries()) {
                if (key === '_id' || key === 'item_type_hidden') continue;
                if ((itemType === 'locations' && key === 'key_features') || (itemType === 'religions' && key === 'domains')) {
                    dataToSubmit[key] = value.split(',').map(s => s.trim()).filter(s => s);
                } else {
                    dataToSubmit[key] = value;
                }
            }

            const url = itemId ? `/api/world-info/${itemType}/${itemId}` : `/api/world-info/${itemType}`;
            const method = itemId ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dataToSubmit),
                });
                const result = await response.json();
                if (response.ok) {
                    alert(result.message || `World ${itemType.slice(0,-1)} ${itemId ? 'updated' : 'created'}!`);
                    if(worldItemModal) worldItemModal.style.display = 'none';
                    fetchAndRenderWorldInfo();
                } else {
                    alert(`Error: ${result.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error(`World item ${itemId ? 'update' : 'create'} error:`, error);
                alert('An error occurred.');
            }
        });
    }

    if(cancelWorldItemButton){
        cancelWorldItemButton.addEventListener('click', () => {
            if (worldItemModal) worldItemModal.style.display = 'none';
        });
    }

    // Close modals if clicked outside
    window.addEventListener('click', function(event) {
        if (editNpcModal && event.target == editNpcModal) {
            editNpcModal.style.display = "none";
        }
        if (worldItemModal && event.target == worldItemModal) {
            worldItemModal.style.display = "none";
        }
    });

    function capitalizeFirstLetter(string) {
        if (!string) return '';
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    if (goToSceneSetupButton) {
        goToSceneSetupButton.addEventListener('click', () => {
            window.location.href = '/npc-selector.html'; // Corrected link
        });
    }
});