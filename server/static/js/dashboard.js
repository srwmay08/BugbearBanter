// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', async () => {
    const welcomeMessage = document.getElementById('welcome-message');
    const npcUploadForm = document.getElementById('npc-upload-form');
    const npcFileInput = document.getElementById('npc-file-input');
    const uploadMessage = document.getElementById('upload-message');
    const userNpcListDiv = document.getElementById('user-npc-list'); // Changed variable name for clarity
    const logoutButton = document.getElementById('logout-button');
    const goToSceneSetupButton = document.getElementById('go-to-scene-setup');
    const loadWorldInfoButton = document.getElementById('load-world-info-button');
    const worldInfoDisplay = document.getElementById('world-info-display');

    // Modal elements for editing NPCs (add to dashboard.html)
    const editNpcModal = document.getElementById('edit-npc-modal');
    const editNpcForm = document.getElementById('edit-npc-form');
    const cancelEditNpcButton = document.getElementById('cancel-edit-npc');
    const npcIdField = document.getElementById('edit-npc-id'); // Hidden field for ID

    let currentUser = null;

    try {
        const statusResponse = await fetch('/api/auth/status');
        const statusResult = await statusResponse.json();
        if (statusResponse.ok && statusResult.logged_in) {
            currentUser = statusResult.user;
            welcomeMessage.textContent = `Welcome, ${currentUser.name || currentUser.email}!`;
            loadUserNpcs(); // Load NPCs on dashboard load
        } else {
            window.location.href = '/login';
            return; 
        }
    } catch (e) {
        console.error("Error checking auth status", e);
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

    if (npcUploadForm) {
        npcUploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            uploadMessage.textContent = 'Uploading...';
            uploadMessage.style.color = 'black';
            const file = npcFileInput.files[0];

            if (!file) {
                uploadMessage.textContent = 'Please select a JSON file.';
                uploadMessage.style.color = 'red';
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
                    uploadMessage.textContent = result.message || 'NPC uploaded successfully!';
                    uploadMessage.style.color = 'green';
                    npcFileInput.value = ''; 
                    loadUserNpcs(); 
                } else {
                    uploadMessage.textContent = result.error || `Upload failed (Status: ${response.status}).`;
                    uploadMessage.style.color = 'red';
                }
            } catch (error) {
                uploadMessage.textContent = 'An error occurred during upload.';
                uploadMessage.style.color = 'red';
                console.error('Upload error:', error);
            }
        });
    }

    async function loadUserNpcs() {
        if (!currentUser) return;
        userNpcListDiv.innerHTML = '<p>Loading NPCs...</p>';
        try {
            const response = await fetch('/api/npcs'); 
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
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
                if (npc.user_id && npc.user_id === currentUser._id) {
                    ownerTag = " (Uploaded by you)";
                    canEditDelete = true; // User owns this NPC
                } else if (!npc.user_id) {
                    ownerTag = " (Default NPC)";
                    // Default NPCs are not editable/deletable by regular users via this interface
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

            // Add event listeners for new buttons
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
            const response = await fetch(`/api/npcs/${npcId}`, {
                method: 'DELETE',
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message || 'NPC deleted successfully.');
                loadUserNpcs(); // Refresh the list
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
        if (!editNpcModal || !editNpcForm) {
            console.error("Edit modal or form not found in HTML!");
            return;
        }

        try {
            const response = await fetch(`/api/npcs/${npcId}`);
            if (!response.ok) throw new Error(`Failed to fetch NPC details (status ${response.status})`);
            const npcData = await response.json();

            // Populate the form
            npcIdField.value = npcData._id;
            // Assuming your form has inputs with names matching NPC fields
            for (const key in npcData) {
                if (editNpcForm.elements[key]) {
                    if (key === 'personality_traits' && Array.isArray(npcData[key])) {
                         // If personality_traits was an array, join it. But your model is a string.
                        // editNpcForm.elements[key].value = npcData[key].join(', ');
                        editNpcForm.elements[key].value = npcData[key]; // It's already a string
                    } else {
                        editNpcForm.elements[key].value = npcData[key];
                    }
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
            // Only include fields that are part of your NPC model and editable
            // Exclude _id and user_id as they are not directly editable by user here
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
                    editNpcModal.style.display = 'none';
                    loadUserNpcs(); // Refresh list
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
    
    // Close modal if clicked outside of it
    window.onclick = function(event) {
        if (event.target == editNpcModal) {
            editNpcModal.style.display = "none";
        }
    }


    // --- World Info Section ---
    if (loadWorldInfoButton) {
        loadWorldInfoButton.addEventListener('click', async () => {
            worldInfoDisplay.innerHTML = '<p>Loading world information...</p>';
            try {
                const response = await fetch('/api/world-info');
                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.href = '/login';
                        return;
                    }
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const worldData = await response.json();
                renderWorldInfo(worldData);

            } catch (error) {
                console.error('Error loading world information:', error);
                worldInfoDisplay.innerHTML = '<p style="color:red;">Could not load world information.</p>';
            }
        });
    }

    function renderWorldInfo(worldData) {
        // ... (renderWorldInfo function from previous response) ...
        if (!worldData) {
            worldInfoDisplay.innerHTML = '<p>No world data received.</p>';
            return;
        }
        let html = '';

        if (worldData.events && worldData.events.length > 0) {
            html += '<h3>Events</h3><ul class="world-info-list">';
            worldData.events.forEach(event => {
                html += `<li><strong>${event.name || 'Unnamed Event'}</strong>: ${event.description || 'N/A'} (Impact: ${event.impact || 'N/A'}, Status: ${event.status || 'N/A'})</li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No events loaded.</p>';
        }

        if (worldData.locations && worldData.locations.length > 0) {
            html += '<h3>Locations</h3><ul class="world-info-list">';
            worldData.locations.forEach(loc => {
                html += `<li><strong>${loc.name || 'Unnamed Location'}</strong> (${loc.type || 'N/A'}): ${loc.description || 'N/A'} (Mood: ${loc.current_mood || 'N/A'})</li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No locations loaded.</p>';
        }
        
        if (worldData.religions && worldData.religions.length > 0) {
            html += '<h3>Religions/Deities</h3><ul class="world-info-list">';
            worldData.religions.forEach(rel => {
                 html += `<li><strong>${rel.name || 'Unnamed Entity'}</strong> (${rel.type || 'N/A'}): ${rel.description || 'N/A'}. Key Features: ${Array.isArray(rel.key_features) ? rel.key_features.join(', ') : (rel.key_features || 'N/A')}</li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No religions/deities loaded.</p>';
        }

        worldInfoDisplay.innerHTML = html;
    }
    
    // Initial call if you want to load User NPCs on dashboard load
    if (currentUser) { 
        loadUserNpcs();
    }
});