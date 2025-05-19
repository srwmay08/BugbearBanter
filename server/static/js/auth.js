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

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        loginMessage.textContent = '';
        const formData = new FormData(loginForm);
        const data = Object.fromEntries(formData.entries());