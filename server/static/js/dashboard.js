// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', async () => {
    const welcomeMessage = document.getElementById('welcome-message');
    const npcUploadForm = document.getElementById('npc-upload-form');
    const npcFileInput = document.getElementById('npc-file-input');
    const uploadMessage = document.getElementById('upload-message');
    const userNpcListDiv = document.getElementById('user-npc-list');
    const logoutButton = document.getElementById('logout-button');
    const goToSceneSetupButton = document.getElementById('go-to-scene-setup');
    const loadWorldInfoButton = document.getElementById('load-world-info-button');
    const worldInfoDisplay = document.getElementById('world-info-display');

    // Modal elements for editing NPCs
    const editNpcModal = document.getElementById('edit-npc-modal');
    const editNpcForm = document.getElementById('edit-npc-form');
    const cancelEditNpcButton = document.getElementById('cancel-edit-npc');
    const npcIdField = document.getElementById('edit-npc-id');

    // World Info Modal Elements
    const worldItemModal = document.getElementById('world-item-modal');
    const worldItemForm = document.getElementById('world-item-form');
    const cancelWorldItemButton = document.getElementById('cancel-world-item'); // Note: Same ID as NPC cancel, might need unique IDs if both modals can be open, or ensure only one is.
    const worldItemIdField = document.getElementById('edit-world-item-id'); // Note: Same ID
    const worldItemTypeField = document.getElementById('edit-world-item-type'); 
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
            loadUserNpcs(); // Load NPCs now that currentUser is set
            // Optionally load world info here too, or keep it button-triggered
            // fetchAndRenderWorldInfo(); 
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
                    if(uploadMessage) uploadMessage.textContent = result.message || 'NPC uploaded successfully!';
                    if(uploadMessage) uploadMessage.style.color = 'green';
                    npcFileInput.value = ''; 
                    loadUserNpcs(); 
                } else {
                    if(uploadMessage) uploadMessage.textContent = result.error || `Upload failed (Status: ${response.status}).`;
                    if(uploadMessage) uploadMessage.style.color = 'red';
                }
            } catch (error) {
                if(uploadMessage) uploadMessage.textContent = 'An error occurred during upload.';
                if(uploadMessage) uploadMessage.style.color = 'red';
                console.error('Upload error:', error);
            }
        });
    }

    async function loadUserNpcs() {
        if (!currentUser || !userNpcListDiv) return;
        userNpcListDiv.innerHTML = '<p>Loading NPCs...</p>';
        try {
            const response = await fetch('/api/npcs'); 
            if (!response.ok) {
                if (response.status === 401) { window.location.href = '/login'; return; }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const allAccessibleNpcs = await response.json();

            if (allAccessibleNpcs.length === 0) {
                userNpcListDiv.innerHTML = '<p>No NPCs found. Try uploading one or check if default NPCs are loaded.</p>';
                return;
            }

            let html = '<ul>';
            allAccessibleNpcs.forEach(npc => {
                let ownerTag = "";
                let canEditDelete = false;
                if (npc.user_id && currentUser && npc.user_id === currentUser._id) {
                    ownerTag = " (Uploaded by you)";
                    canEditDelete = true; 
                } else if (!npc.user_id) {
                    ownerTag = " (Default NPC)";
                }
                
                html += `<li data-npc-id="${npc._id}">
                            ${npc.name || 'Unnamed NPC'} ${ownerTag}
                            ${canEditDelete ? 
                                `<button class="jrpg-button-small btn-edit-npc" data-id="${npc._id}">Edit</button>
                                 <button class="jrpg-button-small btn-delete-npc" data-id="${npc._id}" data-name="${npc.name || 'this NPC'}">Delete</button>`
                                : ''}
                         </li>`;
            });
            html += '</ul>';
            userNpcListDiv.innerHTML = html;

            document.querySelectorAll('.btn-delete-npc').forEach(button => {
                button.addEventListener('click', handleDeleteNpc);
            });
            document.querySelectorAll('.btn-edit-npc').forEach(button => {
                button.addEventListener('click', handleOpenEditNpcModal);
            });

        } catch (error) {
            console.error('Error loading accessible NPCs:', error);
            userNpcListDiv.innerHTML = '<p style="color:red;">Could not load NPCs.</p>';
        }
    }

    async function handleDeleteNpc(event) {
        const npcId = event.target.dataset.id;
        const npcName = event.target.dataset.name;
        if (!confirm(`Are you sure you want to delete ${npcName}? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/npcs/${npcId}`, { method: 'DELETE' });
            const result = await response.json();
            if (response.ok) {
                alert(result.message || 'NPC deleted successfully.');
                loadUserNpcs(); 
            } else {
                alert(`Error deleting NPC: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Delete NPC error:', error);
            alert('An error occurred while deleting the NPC.');
        }
    }

    async function handleOpenEditNpcModal(event) {
        const npcId = event.target.dataset.id;
        if (!editNpcModal || !editNpcForm || !npcIdField) {
            console.error("Edit NPC modal or form elements not found in HTML!");
            return;
        }

        try {
            const response = await fetch(`/api/npcs/${npcId}`);
            if (!response.ok) throw new Error(`Failed to fetch NPC details (status ${response.status})`);
            const npcData = await response.json();

            npcIdField.value = npcData._id;
            for (const key in npcData) {
                if (editNpcForm.elements[key]) {
                    editNpcForm.elements[key].value = npcData[key] || ''; // Handle null/undefined from DB
                }
            }
            editNpcModal.style.display = 'block';
        } catch (error) {
            console.error("Error fetching NPC for edit:", error);
            alert("Could not load NPC data for editing.");
        }
    }
    
    if(editNpcForm){
        editNpcForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const npcId = npcIdField.value;
            const formData = new FormData(editNpcForm);
            const dataToUpdate = {};
            const editableFields = [
                'name', 'race', 'class', 'alignment', 'age', 
                'personality_traits', 'ideals', 'bonds', 'flaws', 
                'backstory', 'motivations', 'speech_patterns', 
                'mannerisms', 'past_situation', 'current_situation', 
                'relationships_with_pcs', 'appearance'
            ];
            for (const [key, value] of formData.entries()) {
                if (editableFields.includes(key)) {
                    dataToUpdate[key] = value;
                }
            }

            try {
                const response = await fetch(`/api/npcs/${npcId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dataToUpdate),
                });
                const result = await response.json();
                if (response.ok) {
                    alert(result.message || 'NPC updated successfully!');
                    if(editNpcModal) editNpcModal.style.display = 'none';
                    loadUserNpcs(); 
                } else {
                    alert(`Error updating NPC: ${result.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Update NPC error:', error);
                alert('An error occurred while updating the NPC.');
            }
        });
    }

    if(cancelEditNpcButton){
        cancelEditNpcButton.addEventListener('click', () => {
            if (editNpcModal) editNpcModal.style.display = 'none';
        });
    }
    
    // --- World Info Section Logic ---
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
        // ... (renderWorldInfo function from previous response, ensure it's robust)
        if (!worldData || !worldInfoDisplay) {
            if(worldInfoDisplay) worldInfoDisplay.innerHTML = '<p>No world data received.</p>';
            return;
        }
        let html = '';

        html += '<div><h3>Events <button class="jrpg-button-small btn-create-world-item" data-type="events">Add Event</button></h3>';
        if (worldData.events && worldData.events.length > 0) {
            html += '<ul class="world-info-list" id="events-list">';
            worldData.events.forEach(event => {
                html += `<li data-id="${event._id}">
                            <strong>${event.name || 'Unnamed Event'}</strong>: ${event.description || 'N/A'} 
                            (Impact: ${event.impact || 'N/A'}, Status: ${event.status || 'N/A'})
                            <button class="jrpg-button-small btn-edit-world-item" data-id="${event._id}" data-type="events">Edit</button>
                            <button class="jrpg-button-small btn-delete-world-item" data-id="${event._id}" data-type="events" data-name="${event.name || 'this event'}">Delete</button>
                         </li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No events loaded.</p>';
        }
        html += '</div>';

        html += '<div><h3>Locations <button class="jrpg-button-small btn-create-world-item" data-type="locations">Add Location</button></h3>';
        if (worldData.locations && worldData.locations.length > 0) {
            html += '<ul class="world-info-list" id="locations-list">';
            worldData.locations.forEach(loc => {
                html += `<li data-id="${loc._id}">
                            <strong>${loc.name || 'Unnamed Location'}</strong> (${loc.type || 'N/A'}): ${loc.description || 'N/A'} 
                            (Mood: ${loc.current_mood || 'N/A'})
                            <button class="jrpg-button-small btn-edit-world-item" data-id="${loc._id}" data-type="locations">Edit</button>
                            <button class="jrpg-button-small btn-delete-world-item" data-id="${loc._id}" data-type="locations" data-name="${loc.name || 'this location'}">Delete</button>
                         </li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No locations loaded.</p>';
        }
        html += '</div>';
        
        html += '<div><h3>Religions/Deities <button class="jrpg-button-small btn-create-world-item" data-type="religions">Add Religion</button></h3>';
        if (worldData.religions && worldData.religions.length > 0) {
            html += '<ul class="world-info-list" id="religions-list">';
            worldData.religions.forEach(rel => {
                html += `<li data-id="${rel._id}">
                            <strong>${rel.name || 'Unnamed Entity'}</strong> (${rel.type || 'N/A'}): ${rel.description || 'N/A'}. 
                            Key Features: ${Array.isArray(rel.key_features) ? rel.key_features.join(', ') : (rel.key_features || 'N/A')}
                            <button class="jrpg-button-small btn-edit-world-item" data-id="${rel._id}" data-type="religions">Edit</button>
                            <button class="jrpg-button-small btn-delete-world-item" data-id="${rel._id}" data-type="religions" data-name="${rel.name || 'this entity'}">Delete</button>
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
        // ... (implementation from previous response)
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
        // ... (implementation from previous response)
        const itemType = event.target.dataset.type;
        if (!worldItemModal || !worldItemForm || !worldItemFieldsContainer || !worldItemModalTitle || !worldItemIdField || !worldItemTypeField) return;
        
        worldItemModalTitle.textContent = `Create New ${capitalizeFirstLetter(itemType.slice(0,-1))}`;
        worldItemForm.reset();
        worldItemIdField.value = ''; 
        worldItemTypeField.value = itemType;
        populateWorldItemFormFields(itemType); 
        worldItemModal.style.display = 'block';
    }
    
    async function handleOpenEditWorldItemModal(event) {
        // ... (implementation from previous response)
        const itemId = event.target.dataset.id;
        const itemType = event.target.dataset.type;
         if (!worldItemModal || !worldItemForm || !worldItemFieldsContainer || !worldItemModalTitle || !worldItemIdField || !worldItemTypeField) return;

        try {
            const response = await fetch(`/api/world-info/${itemType}`); 
            if (!response.ok) throw new Error('Could not fetch item details for editing.');
            const items = await response.json();
            const itemData = items.find(item => item._id === itemId);

            if (!itemData) {
                alert("Could not find item details to edit.");
                return;
            }
            
            worldItemModalTitle.textContent = `Edit ${capitalizeFirstLetter(itemType.slice(0,-1))}`;
            worldItemForm.reset();
            worldItemIdField.value = itemData._id;
            worldItemTypeField.value = itemType;
            populateWorldItemFormFields(itemType, itemData);
            worldItemModal.style.display = 'block';

        } catch (error) {
            console.error("Error preparing world item for edit:", error);
            alert("Could not load item data for editing.");
        }
    }

    function populateWorldItemFormFields(itemType, data = {}) {
        // ... (implementation from previous response, ensure it's complete for all types)
        if (!worldItemFieldsContainer) return;
        worldItemFieldsContainer.innerHTML = ''; // Clear previous fields
        let fieldsHtml = '';
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
            // ... (implementation from previous response)
            event.preventDefault();
            const itemId = worldItemIdField.value;
            const itemType = worldItemTypeField.value;
            const formData = new FormData(worldItemForm);
            const dataToSubmit = {};
            
            for (const [key, value] of formData.entries()) {
                if (key === '_id' || key === 'item_type_hidden') continue; 
                if (key === 'key_features' || key === 'domains') { 
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

    if(cancelWorldItemButton){ // This ID might be duplicated if NPC modal also uses it
        const npcCancel = document.getElementById('cancel-edit-npc'); // Assuming unique ID for NPC modal cancel
        if(npcCancel) npcCancel.addEventListener('click', () => { if(editNpcModal) editNpcModal.style.display = 'none';});

        // For world item modal
        const worldCancel = document.getElementById('cancel-world-item');
        if(worldCancel) worldCancel.addEventListener('click', () => {
            if (worldItemModal) worldItemModal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', function(event) {
        if (event.target == editNpcModal) { // For NPC modal
            editNpcModal.style.display = "none";
        }
        if (event.target == worldItemModal) { // For World Item modal
            worldItemModal.style.display = "none";
        }
    });

    function capitalizeFirstLetter(string) {
        if (!string) return '';
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    if (goToSceneSetupButton) {
        goToSceneSetupButton.addEventListener('click', () => {
            window.location.href = '/npc-selector'; 
        });
    }
});