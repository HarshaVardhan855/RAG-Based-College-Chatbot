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

// Canonical HTML Escape Function
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;

// API Helper with Cold-Start Handling & Error Management
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

    // Set up a timer to alert the user if Render backend is sleeping (cold start > 3.5s)
    let coldStartTimer = setTimeout(() => {
        showToast('Backend server is waking up... Please wait a few seconds.', 'info');
    }, 3500);

    try {
        const response = await fetch(fullUrl, { method, headers, body });
        clearTimeout(coldStartTimer);

        let data;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            data = await response.json();
        } else {
            const rawText = await response.text();
            data = { detail: rawText || `HTTP ${response.status} ${response.statusText}` };
        }
        
        if (!response.ok) {
            if (response.status === 401) {
                // Expired or invalid token
                state.token = null;
                state.user = null;
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                const userInfo = document.getElementById('userInfo');
                const authPrompt = document.getElementById('authPrompt');
                if (userInfo) userInfo.classList.add('hidden');
                if (authPrompt) authPrompt.classList.remove('hidden');
            }
            const errMsg = data.detail || (typeof data === 'string' ? data : 'API request failed');
            console.error(`[API Error ${response.status}] ${method} ${url}:`, errMsg);
            throw new Error(errMsg);
        }
        return data;
    } catch (err) {
        clearTimeout(coldStartTimer);
        console.error(`[API Network/Error] ${method} ${url}:`, err);
        
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            const netErr = 'Cannot connect to backend server. Please check your internet connection or backend URL.';
            showToast(netErr, 'error');
            throw new Error(netErr);
        }
        
        showToast(err.message || 'An unexpected error occurred.', 'error');
        throw err;
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    
    toast.style.padding = '0.75rem 1.25rem';
    toast.style.marginBottom = '0.5rem';
    toast.style.borderRadius = '8px';
    toast.style.fontSize = '0.85rem';
    toast.style.color = '#fff';
    toast.style.background = type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6';
    
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
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
    if (!toggleBtn) return;
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    toggleBtn.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        toggleBtn.innerHTML = theme === 'dark' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });
}

// Auth Modal & Handlers
function initAuthModal() {
    const modal = document.getElementById('authModal');
    const openBtn = document.getElementById('showAuthModalBtn');
    const closeBtn = document.getElementById('closeAuthModal');
    const loginTab = document.getElementById('tabLoginBtn');
    const regTab = document.getElementById('tabRegisterBtn');
    const loginForm = document.getElementById('loginForm');
    const regForm = document.getElementById('registerForm');
    const loginSubmitBtn = document.getElementById('loginSubmitBtn');
    const regSubmitBtn = document.getElementById('regSubmitBtn');

    if (openBtn) openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
    if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));

    if (loginTab) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            regTab.classList.remove('active');
            loginForm.classList.remove('hidden');
            regForm.classList.add('hidden');
        });
    }

    if (regTab) {
        regTab.addEventListener('click', () => {
            regTab.classList.add('active');
            loginTab.classList.remove('active');
            regForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
        });
    }

    // Login Form Handler with explicit loading state & non-silent error catching
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('loginEmail');
            const passwordInput = document.getElementById('loginPassword');
            const email = emailInput.value.trim();
            const password = passwordInput.value;

            if (!email || !password) {
                showToast('Please enter both email and password.', 'error');
                return;
            }

            // Disable UI elements to prevent duplicate submission
            if (loginSubmitBtn) {
                loginSubmitBtn.disabled = true;
                loginSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Logging in...';
            }
            emailInput.disabled = true;
            passwordInput.disabled = true;

            try {
                const data = await apiRequest('/api/auth/login', 'POST', { email, password });
                state.token = data.access_token;
                state.user = data.user;
                localStorage.setItem('token', state.token);
                localStorage.setItem('user', JSON.stringify(state.user));
                
                modal.classList.add('hidden');
                loginForm.reset();
                await checkAuthStatus();
                showToast('Logged in successfully!', 'success');
            } catch (err) {
                console.error('Login attempt failed:', err);
                // Toast notification is already raised by apiRequest, but we log the detailed error
            } finally {
                // Re-enable UI elements
                if (loginSubmitBtn) {
                    loginSubmitBtn.disabled = false;
                    loginSubmitBtn.innerText = 'Log In';
                }
                emailInput.disabled = false;
                passwordInput.disabled = false;
            }
        });
    }

    // Register Form Handler with explicit loading state & non-silent error catching
    if (regForm) {
        regForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nameInput = document.getElementById('regFullName');
            const emailInput = document.getElementById('regEmail');
            const roleSelect = document.getElementById('regRole');
            const passwordInput = document.getElementById('regPassword');

            const full_name = nameInput.value.trim();
            const email = emailInput.value.trim();
            const role = roleSelect ? roleSelect.value : 'STUDENT';
            const password = passwordInput.value;

            if (!full_name || !email || !password) {
                showToast('Please fill out all required fields.', 'error');
                return;
            }

            if (regSubmitBtn) {
                regSubmitBtn.disabled = true;
                regSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';
            }
            nameInput.disabled = true;
            emailInput.disabled = true;
            passwordInput.disabled = true;

            try {
                await apiRequest('/api/auth/register', 'POST', { full_name, email, role, password });
                showToast('Registration successful! Please log in.', 'success');
                regForm.reset();
                if (loginTab) loginTab.click();
            } catch (err) {
                console.error('Registration attempt failed:', err);
            } finally {
                if (regSubmitBtn) {
                    regSubmitBtn.disabled = false;
                    regSubmitBtn.innerText = 'Create Account';
                }
                nameInput.disabled = false;
                emailInput.disabled = false;
                passwordInput.disabled = false;
            }
        });
    }

    // Logout Handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            state.token = null;
            state.user = null;
            state.currentSessionId = null;
            state.sessions = [];
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            
            if (typeof clearChatArea === 'function') {
                clearChatArea();
            }
            
            checkAuthStatus();
            showToast('Logged out successfully', 'info');
        });
    }
}

// Check Auth Status & Synchronize Application State
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
            
            if (userInfo) userInfo.classList.remove('hidden');
            if (authPrompt) authPrompt.classList.add('hidden');
            if (userAvatar) userAvatar.innerText = (user.full_name || 'U').charAt(0).toUpperCase();
            if (userName) userName.innerText = user.full_name || 'User';
            if (userRoleBadge) userRoleBadge.innerText = user.role || 'STUDENT';

            if (user.role === 'ADMIN') {
                if (roleSwitcher) roleSwitcher.style.display = 'flex';
            } else {
                if (roleSwitcher) roleSwitcher.style.display = 'none';
                switchView('student');
            }

            // Load Chat History for logged in student
            if (typeof loadChatHistory === 'function') {
                loadChatHistory();
            }
        } catch (err) {
            console.warn('Auth token verification failed:', err);
            state.token = null;
            state.user = null;
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            if (userInfo) userInfo.classList.add('hidden');
            if (authPrompt) authPrompt.classList.remove('hidden');
            if (roleSwitcher) roleSwitcher.style.display = 'none';
        }
    } else {
        if (userInfo) userInfo.classList.add('hidden');
        if (authPrompt) authPrompt.classList.remove('hidden');
        if (roleSwitcher) roleSwitcher.style.display = 'none';
    }
}

// Role Switcher (Student vs Admin)
function setupRoleSwitcher() {
    const studentBtn = document.getElementById('switchToStudentBtn');
    const adminBtn = document.getElementById('switchToAdminBtn');

    if (studentBtn) studentBtn.addEventListener('click', () => switchView('student'));
    if (adminBtn) adminBtn.addEventListener('click', () => switchView('admin'));
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
        if (studentView) studentView.classList.remove('hidden');
        if (adminView) adminView.classList.add('hidden');
        if (studentSidebar) studentSidebar.classList.remove('hidden');
        if (adminSidebar) adminSidebar.classList.add('hidden');
        if (studentBtn) studentBtn.classList.add('active');
        if (adminBtn) adminBtn.classList.remove('active');
    } else {
        if (studentView) studentView.classList.add('hidden');
        if (adminView) adminView.classList.remove('hidden');
        if (studentSidebar) studentSidebar.classList.add('hidden');
        if (adminSidebar) adminSidebar.classList.remove('hidden');
        if (adminBtn) adminBtn.classList.add('active');
        if (studentBtn) studentBtn.classList.remove('active');
        
        // Refresh admin data
        if (typeof loadAdminDocuments === 'function') loadAdminDocuments();
        if (typeof loadAdminStats === 'function') loadAdminStats();
    }
}
