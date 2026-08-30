// Main Application State & Utilities

const state = {
    token: localStorage.getItem('token') || null,
    user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null,
    currentView: 'student',
    currentSessionId: null,
    sessions: []
};

// Centralized API Base URL Configuration
const API_BASE_URL = (typeof window !== 'undefined' && window.API_BASE_URL) ? window.API_BASE_URL : '';

// API Helper
async function apiRequest(url, method = 'GET', body = null, isFormData = false) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    const headers = {};
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }
    
    if (body && !isFormData) {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(body);
    }

    try {
        const response = await fetch(fullUrl, { method, headers, body });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }
        return data;
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    
    // style toast inline if needed
    toast.style.padding = '0.75rem 1.25rem';
    toast.style.marginBottom = '0.5rem';
    toast.style.borderRadius = '8px';
    toast.style.fontSize = '0.85rem';
    toast.style.color = '#fff';
    toast.style.background = type === 'error' ? '#f87171' : type === 'success' ? '#4ade80' : '#38bdf8';
    
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// UI Setup & Init
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initAuthModal();
    checkAuthStatus();
    setupRoleSwitcher();
});

// Theme Toggle
function initTheme() {
    const toggleBtn = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    toggleBtn.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        toggleBtn.innerHTML = theme === 'dark' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });
}

// Auth Modal
function initAuthModal() {
    const modal = document.getElementById('authModal');
    const openBtn = document.getElementById('showAuthModalBtn');
    const closeBtn = document.getElementById('closeAuthModal');
    const loginTab = document.getElementById('tabLoginBtn');
    const regTab = document.getElementById('tabRegisterBtn');
    const loginForm = document.getElementById('loginForm');
    const regForm = document.getElementById('registerForm');

    openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));

    loginTab.addEventListener('click', () => {
        loginTab.classList.add('active');
        regTab.classList.remove('active');
        loginForm.classList.remove('hidden');
        regForm.classList.add('hidden');
    });

    regTab.addEventListener('click', () => {
        regTab.classList.add('active');
        loginTab.classList.remove('active');
        regForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
    });

    // Login Form Handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        try {
            const data = await apiRequest('/api/auth/login', 'POST', { email, password });
            state.token = data.access_token;
            state.user = data.user;
            localStorage.setItem('token', state.token);
            localStorage.setItem('user', JSON.stringify(state.user));
            
            modal.classList.add('hidden');
            checkAuthStatus();
            showToast('Logged in successfully', 'success');
        } catch (e) {}
    });

    // Register Form Handler
    regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const full_name = document.getElementById('regFullName').value;
        const email = document.getElementById('regEmail').value;
        const role = document.getElementById('regRole').value;
        const password = document.getElementById('regPassword').value;

        try {
            await apiRequest('/api/auth/register', 'POST', { full_name, email, role, password });
            showToast('Registration successful! Please log in.', 'success');
            loginTab.click();
        } catch (e) {}
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        state.token = null;
        state.user = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        checkAuthStatus();
        showToast('Logged out', 'info');
    });
}

// Check Auth Status & Update UI
async function checkAuthStatus() {
    const userInfo = document.getElementById('userInfo');
    const authPrompt = document.getElementById('authPrompt');
    const roleSwitcher = document.getElementById('roleSwitcherContainer');
    const userAvatar = document.getElementById('userAvatar');
    const userName = document.getElementById('userName');
    const userRoleBadge = document.getElementById('userRoleBadge');

    if (state.token) {
        try {
            const user = await apiRequest('/api/auth/me');
            state.user = user;
            localStorage.setItem('user', JSON.stringify(user));
            
            userInfo.classList.remove('hidden');
            authPrompt.classList.add('hidden');
            userAvatar.innerText = user.full_name.charAt(0).toUpperCase();
            userName.innerText = user.full_name;
            userRoleBadge.innerText = user.role;

            if (user.role === 'ADMIN') {
                roleSwitcher.style.display = 'flex';
            } else {
                roleSwitcher.style.display = 'none';
                switchView('student');
            }

            // Load Chat History
            if (typeof loadChatHistory === 'function') {
                loadChatHistory();
            }
        } catch (err) {
            state.token = null;
            localStorage.removeItem('token');
            userInfo.classList.add('hidden');
            authPrompt.classList.remove('hidden');
            roleSwitcher.style.display = 'none';
        }
    } else {
        userInfo.classList.add('hidden');
        authPrompt.classList.remove('hidden');
        roleSwitcher.style.display = 'none';
    }
}

// Role Switcher (Student vs Admin)
function setupRoleSwitcher() {
    const studentBtn = document.getElementById('switchToStudentBtn');
    const adminBtn = document.getElementById('switchToAdminBtn');

    studentBtn.addEventListener('click', () => switchView('student'));
    adminBtn.addEventListener('click', () => switchView('admin'));
}

function switchView(view) {
    state.currentView = view;
    const studentView = document.getElementById('studentView');
    const adminView = document.getElementById('adminView');
    const studentSidebar = document.getElementById('studentSidebar');
    const adminSidebar = document.getElementById('adminSidebar');
    const studentBtn = document.getElementById('switchToStudentBtn');
    const adminBtn = document.getElementById('switchToAdminBtn');

    if (view === 'student') {
        studentView.classList.remove('hidden');
        adminView.classList.add('hidden');
        studentSidebar.classList.remove('hidden');
        adminSidebar.classList.add('hidden');
        studentBtn.classList.add('active');
        adminBtn.classList.remove('active');
    } else {
        studentView.classList.add('hidden');
        adminView.classList.remove('hidden');
        studentSidebar.classList.add('hidden');
        adminSidebar.classList.remove('hidden');
        adminBtn.classList.add('active');
        studentBtn.classList.remove('active');
        
        // Refresh admin data
        if (typeof loadAdminDocuments === 'function') loadAdminDocuments();
        if (typeof loadAdminStats === 'function') loadAdminStats();
    }
}
