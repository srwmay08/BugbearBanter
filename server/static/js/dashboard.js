// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', async () => {
    const welcomeMessage = document.getElementById('welcome-message');
    const npcUploadForm = document.getElementById('npc-upload-form');
    const npcFileInput = document.getElementById('npc-file-input');
    const uploadMessage = document.getElementById('upload-message');
    const userNpcList = document.getElementById('user-npc-list');
    const logoutButton = document.getElementById('logout-button');
    const goToSceneSetupButton = document.getElementById('go-to-scene-setup');

    let currentUser = null;

    try {
        const statusResponse = await fetch('/api/auth/status');
        const statusResult = await statusResponse.json();
        if (statusResponse.ok && statusResult.logged_in) {
            currentUser = statusResult.user;
            welcomeMessage.textContent = `Welcome, ${currentUser.name || currentUser.email}!`;
            loadUserNpcs();
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
            uploadMessage.textContent = '';
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
                if (response.ok) {
                    uploadMessage.textContent = result.message || 'NPC uploaded successfully!';
                    uploadMessage.style.color = 'green';
                    npcFileInput.value = ''; 
                    loadUserNpcs(); 
                } else {
                    uploadMessage.textContent = result.error || 'Upload failed.';
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
        userNpcList.innerHTML = '<p>Loading NPCs...</p>';
        try {
            const response = await fetch('/api/npcs'); // Fetches global + user's own NPCs
            if (!response.ok) {
                if (response.status === 401) { // Unauthorized
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const allAccessibleNpcs = await response.json();

            if (allAccessibleNpcs.length === 0) {
                userNpcList.innerHTML = '<p>No NPCs found. Try uploading one or check if default NPCs are loaded.</p>';
                return;
            }

            let html = '<ul>';
            allAccessibleNpcs.forEach(npc => {
                let ownerTag = "";
                if (npc.user_id && npc.user_id === currentUser._id) {
                    ownerTag = " (Uploaded by you)";
                } else if (!npc.user_id) {
                    ownerTag = " (Default NPC)";
                }
                // Not showing NPCs uploaded by *other* users for privacy, unless that's a feature.
                // The current backend logic in get_combined_npcs only gets global or current user's NPCs.
                html += `<li>${npc.name || 'Unnamed NPC'} ${ownerTag}</li>`;
            });
            html += '</ul>';
            userNpcList.innerHTML = html;

        } catch (error) {
            console.error('Error loading accessible NPCs:', error);
            userNpcList.innerHTML = '<p style="color:red;">Could not load NPCs.</p>';
        }
    }
    
    if (goToSceneSetupButton) {
        goToSceneSetupButton.addEventListener('click', () => {
            window.location.href = '/npc-selector'; 
        });
    }


    if (loadWorldInfoButton) {
        loadWorldInfoButton.addEventListener('click', async () => {
            worldInfoDisplay.innerHTML = '<p>Loading world information...</p>';
            try {
                const response = await fetch('/api/world-info');
                if (!response.ok) {
                    if (response.status === 401) { // Unauthorized
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
        if (!worldData) {
            worldInfoDisplay.innerHTML = '<p>No world data received.</p>';
            return;
        }
        let html = '';

        // Display Events
        if (worldData.events && worldData.events.length > 0) {
            html += '<h3>Events</h3><ul class="world-info-list">';
            worldData.events.forEach(event => {
                html += `<li><strong>${event.name || 'Unnamed Event'}</strong>: ${event.description || 'N/A'} (Impact: ${event.impact || 'N/A'}, Status: ${event.status || 'N/A'})</li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No events loaded.</p>';
        }

        // Display Locations
        if (worldData.locations && worldData.locations.length > 0) {
            html += '<h3>Locations</h3><ul class="world-info-list">';
            worldData.locations.forEach(loc => {
                html += `<li><strong>${loc.name || 'Unnamed Location'}</strong> (${loc.type || 'N/A'}): ${loc.description || 'N/A'} (Mood: ${loc.current_mood || 'N/A'})</li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No locations loaded.</p>';
        }

        // Display Religions
        if (worldData.religions && worldData.religions.length > 0) {
            html += '<h3>Religions/Deities</h3><ul class="world-info-list">';
            worldData.religions.forEach(rel => {
                // Assuming structure similar to your existing world_religions.json
                // If it was the one I previously formatted for Waterdeep/Daggerford, it would be 'name', 'type', 'description'
                // If it's the one from earlier that looked like locations data, adjust fields accordingly.
                // For the example content of world_religions.json you provided (which looks like location data):
                 html += `<li><strong>${rel.name || 'Unnamed Entity'}</strong> (${rel.type || 'N/A'}): ${rel.description || 'N/A'}. Key Features: ${Array.isArray(rel.key_features) ? rel.key_features.join(', ') : (rel.key_features || 'N/A')}</li>`;

                // If world_religions.json has a more typical deity structure like:
                // html += `<li><strong>${rel.name || 'Unnamed Deity'}</strong>: Domains: ${Array.isArray(rel.domains) ? rel.domains.join(', ') : 'N/A'}. Symbol: ${rel.symbol || 'N/A'}</li>`;
            });
            html += '</ul>';
        } else {
            html += '<p>No religions/deities loaded.</p>';
        }

        worldInfoDisplay.innerHTML = html;
    }
    
    // Initial call if you want to load User NPCs on dashboard load
    if (currentUser) { // Ensure currentUser is set from auth check
        loadUserNpcs();
    }
});