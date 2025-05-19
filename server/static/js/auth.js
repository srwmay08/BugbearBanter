// static/js/auth.js
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginMessage = document.getElementById('login-message');
    const registerMessage = document.getElementById('register-message');
    const googleMessage = document.getElementById('google-message');

    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const loginFormContainer = document.querySelector('.login-form-container');
    const registerFormContainer = document.querySelector('.register-form-container');

    if (showRegisterLink && showLoginLink && loginFormContainer && registerFormContainer) { // Check if elements exist
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginFormContainer.style.display = 'none';
            registerFormContainer.style.display = 'block';
        });

        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerFormContainer.style.display = 'none';
            loginFormContainer.style.display = 'block';
        });
    }


    if (loginForm) { // Check if loginForm exists
        loginForm.addEventListener('submit', async (event) => { // This is line 26 if checks above are minimal
            event.preventDefault();
            loginMessage.textContent = '';
            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries()); // This should be line 30

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                const result = await response.json();
                if (response.ok) {
                    loginMessage.textContent = result.message || 'Login successful!';
                    loginMessage.style.color = 'green';
                    window.location.href = '/dashboard'; 
                } else {
                    loginMessage.textContent = result.error || 'Login failed.';
                    loginMessage.style.color = 'red';
                }
            } catch (error) {
                loginMessage.textContent = 'An error occurred. Please try again.';
                loginMessage.style.color = 'red';
                console.error('Login error:', error);
            }
        }); // Make sure this closing '});' is present
    }


    if (registerForm) { // Check if registerForm exists
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            registerMessage.textContent = '';
            const password = document.getElementById('reg-password').value;
            const confirmPassword = document.getElementById('reg-confirm-password').value;

            if (password !== confirmPassword) {
                registerMessage.textContent = 'Passwords do not match.';
                registerMessage.style.color = 'red';
                return;
            }
            if (password.length < 8) {
                registerMessage.textContent = 'Password must be at least 8 characters.';
                 registerMessage.style.color = 'red';
                return;
            }

            const formData = new FormData(registerForm);
            const data = Object.fromEntries(formData.entries());
            delete data.confirm_password; 

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                const result = await response.json();
                if (response.ok) {
                    registerMessage.textContent = result.message || 'Registration successful! You are now logged in.';
                    registerMessage.style.color = 'green';
                    window.location.href = '/dashboard';
                } else {
                    registerMessage.textContent = result.error || 'Registration failed.';
                    registerMessage.style.color = 'red';
                }
            } catch (error) {
                registerMessage.textContent = 'An error occurred. Please try again.';
                registerMessage.style.color = 'red';
                console.error('Registration error:', error);
            }
        }); // Make sure this closing '});' is present
    }
}); // Closing for DOMContentLoaded

// Google Sign-In callback function
// THIS MUST BE IN THE GLOBAL SCOPE for the Google library to find it
async function handleGoogleCredentialResponse(response) {
    const googleMessage = document.getElementById('google-message');
    if (!googleMessage) { // Defensive check
        console.error("google-message element not found");
        return;
    }
    googleMessage.textContent = 'Processing Google Sign-In...';
    googleMessage.style.color = 'black';

    try {
        const serverResponse = await fetch('/api/auth/google-signin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ credential: response.credential }),
        });
        const result = await serverResponse.json();
        if (serverResponse.ok) {
            googleMessage.textContent = result.message || 'Google Sign-In successful!';
            googleMessage.style.color = 'green';
            window.location.href = '/dashboard'; 
        } else {
            googleMessage.textContent = result.error || 'Google Sign-In failed.';
            googleMessage.style.color = 'red';
        }
    } catch (error) {
        googleMessage.textContent = 'Google Sign-In error. Please try again.';
        googleMessage.style.color = 'red';
        console.error('Google Sign-In Error:', error);
    }
}