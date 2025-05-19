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

    // Check login status
    try {
        const statusResponse = await fetch('/api/auth/status');
        const statusResult = await statusResponse.json();
        if (statusResponse.ok && statusResult.logged_in) {
            currentUser = statusResult.user;
            welcomeMessage.textContent = `Welcome, ${currentUser.name || currentUser.email}!`;
            loadUserNpcs();
        } else {
            // Not logged in, redirect to login page
            window.location.href = '/login';
            return; // Stop further execution
        }
    } catch (e) {
        console.error("Error checking auth status", e);
        window.location.href = '/login'; // Redirect on error
        return;
    }

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
            const response = await fetch('/api/npcs/upload', { // Ensure this matches your new backend route
                method: 'POST',
                body: formData, // No Content-Type header needed for FormData with files
            });
            const result = await response.json();
            if (response.ok) {
                uploadMessage.textContent = result.message || 'NPC uploaded successfully!';
                uploadMessage.style.color = 'green';
                npcFileInput.value = ''; // Clear file input
                loadUserNpcs(); // Refresh the list
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

    async function loadUserNpcs() {
        if (!currentUser) return;
        userNpcList.innerHTML = '<p>Loading your NPCs...</p>';
        try {
            // This route needs to be modified to return NPCs for the current_user
            const response = await fetch('/api/npcs'); // Or a new route like /api/user/npcs
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const allNpcs = await response.json();

            // Filter NPCs that belong to the current user
            // This assumes your /api/npcs route will eventually be user-aware
            // OR you create a new endpoint /api/user/npcs that returns only user's npcs
            const userNpcs = allNpcs.filter(npc => currentUser.npc_ids && currentUser.npc_ids.includes(npc._id));


            if (userNpcs.length === 0) {
                userNpcList.innerHTML = '<p>You haven\'t uploaded any NPCs yet. Use the form above to add some!</p>';
                return;
            }

            let html = '<ul>';
            userNpcs.forEach(npc => {
                html += `<li>${npc.name || 'Unnamed NPC'} (ID: ${npc._id})</li>`;
            });
            html += '</ul>';
            userNpcList.innerHTML = html;

        } catch (error) {
            console.error('Error loading user NPCs:', error);
            userNpcList.innerHTML = '<p style="color:red;">Could not load your NPCs.</p>';
        }
    }

    goToSceneSetupButton.addEventListener('click', () => {
        // Redirect to the existing NPC selection page (index.html)
        // index.html and app.js will need to be aware of the logged-in user
        // to only show their NPCs for selection.
        // For now, it will show all NPCs if app.js is not modified.
        window.location.href = '/';
    });
});