/**
 * WiFi Tracker - Authentication Module
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.loginModal = document.getElementById('loginModal');
        this.loginForm = document.getElementById('loginForm');
        this.loginError = document.getElementById('loginError');
        this.app = document.getElementById('app');
        this.logoutBtn = document.getElementById('logoutBtn');

        this.init();
    }

    init() {
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        this.logoutBtn.addEventListener('click', () => this.logout());

        this.checkAuth();
    }

    async checkAuth() {
        const token = localStorage.getItem('access_token');

        if (token) {
            try {
                this.user = await api.getCurrentUser();
                this.showApp();
            } catch (error) {
                console.error('Auth check failed:', error);
                this.showLogin();
            }
        } else {
            this.showLogin();
        }
    }

    async handleLogin(e) {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        this.loginError.textContent = '';

        try {
            await api.login(username, password);
            this.user = await api.getCurrentUser();
            this.showApp();
        } catch (error) {
            this.loginError.textContent = error.message || 'Login failed. Please try again.';
        }
    }

    showLogin() {
        this.loginModal.classList.remove('hidden');
        this.app.classList.add('hidden');
    }

    showApp() {
        this.loginModal.classList.add('hidden');
        this.app.classList.remove('hidden');

        this.updateUserInfo();

        if (window.app) {
            window.app.init();
        }
    }

    updateUserInfo() {
        if (this.user) {
            document.getElementById('userName').textContent = this.user.username;
            document.getElementById('userInitial').textContent = this.user.username.charAt(0).toUpperCase();
        }
    }

    logout() {
        api.clearToken();
        this.user = null;
        this.showLogin();

        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    }

    isAuthenticated() {
        return !!this.user;
    }

    getUser() {
        return this.user;
    }

    isAdmin() {
        return this.user && this.user.role === 'admin';
    }
}

const auth = new AuthManager();
