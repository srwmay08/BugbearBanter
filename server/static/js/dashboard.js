// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', async () => {
    // ... (all existing variables and functions from your latest dashboard.js) ...
    const loadWorldInfoButton = document.getElementById('load-world-info-button');
    const worldInfoDisplay = document.getElementById('world-info-display');

    // --- World Info Modal Elements (Add to dashboard.html) ---
    const worldItemModal = document.getElementById('world-item-modal');
    const worldItemForm = document.getElementById('world-item-form');
    const cancelWorldItemButton = document.getElementById('cancel-world-item');
    const worldItemIdField = document.getElementById('edit-world-item-id');
    const worldItemTypeField = document.getElementById('edit-world-item-type'); // To know if editing event, location, etc.
    const worldItemModalTitle = document.getElementById('world-item-modal-title');
    const worldItemFieldsContainer = document.getElementById('world-item-fields-container');


    if (loadWorldInfoButton) {
        loadWorldInfoButton.addEventListener('click', fetchAndRenderWorldInfo);
    }

    async function fetchAndRenderWorldInfo() {
        worldInfoDisplay.innerHTML = '<p>Loading world information...</p>';
        try {
            const response = await fetch('/api/world-info/all'); // Fetch all world info
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
        if (!worldData) {
            worldInfoDisplay.innerHTML = '<p>No world data received.</p>';
            return;
        }
        let html = '';

        // --- Events ---
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

        // --- Locations ---
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
        
        // --- Religions ---
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

        // Add event listeners for new world item CRUD buttons
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
        const itemType = event.target.dataset.type; // "events", "locations", or "religions"
        const itemName = event.target.dataset.name;

        if (!confirm(`Are you sure you want to delete ${itemName}?`)) return;

        try {
            const response = await fetch(`/api/world-info/${itemType}/${itemId}`, { method: 'DELETE' });
            const result = await response.json();
            if (response.ok) {
                alert(result.message || `${itemType.slice(0,-1)} deleted.`);
                fetchAndRenderWorldInfo(); // Refresh list
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
        if (!worldItemModal || !worldItemForm || !worldItemFieldsContainer || !worldItemModalTitle || !worldItemIdField || !worldItemTypeField) return;
        
        worldItemModalTitle.textContent = `Create New ${capitalizeFirstLetter(itemType.slice(0,-1))}`;
        worldItemForm.reset();
        worldItemIdField.value = ''; // Clear ID for creation
        worldItemTypeField.value = itemType;
        populateWorldItemFormFields(itemType); // Dynamically add fields based on type
        worldItemModal.style.display = 'block';
    }
    
    async function handleOpenEditWorldItemModal(event) {
        const itemId = event.target.dataset.id;
        const itemType = event.target.dataset.type;
         if (!worldItemModal || !worldItemForm || !worldItemFieldsContainer || !worldItemModalTitle || !worldItemIdField || !worldItemTypeField) return;

        try {
            // Need a route to get a single world item, e.g., /api/world-info/events/<id>
            // For now, we'll find it from the already loaded data if possible, or fetch.
            // This is a simplification; ideally, you'd fetch the specific item.
            const response = await fetch(`/api/world-info/${itemType}`); // Fetch all of that type
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
        worldItemFieldsContainer.innerHTML = ''; // Clear previous fields
        let fieldsHtml = '';
        // Define fields based on itemType - this is a simplified example
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
            event.preventDefault();
            const itemId = worldItemIdField.value;
            const itemType = worldItemTypeField.value;
            const formData = new FormData(worldItemForm);
            const dataToSubmit = {};
            
            for (const [key, value] of formData.entries()) {
                if (key === '_id' || key === 'item_type_hidden') continue; // Don't send these helper fields
                if (key === 'key_features' || key === 'domains') { // Handle comma-separated lists
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
                    fetchAndRenderWorldInfo(); // Refresh list
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
    
    // Close world item modal if clicked outside
    window.addEventListener('click', function(event) {
        if (event.target == worldItemModal) {
            worldItemModal.style.display = "none";
        }
    });


    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    // Initial call
    if (currentUser) { 
        loadUserNpcs();
        // Optionally, load world info on dashboard load too, or keep it button-triggered
        // fetchAndRenderWorldInfo(); 
    }
});