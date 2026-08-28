// Admin Dashboard Module

document.addEventListener('DOMContentLoaded', () => {
    setupAdminListeners();
});

function setupAdminListeners() {
    setupAdminNavTabs();
    setupFileUploadDropZone();
    setupUploadForm();
}

function setupAdminNavTabs() {
    const navItems = document.querySelectorAll('#adminSidebar .nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            const tabName = item.getAttribute('data-tab');
            switchAdminTab(tabName);
        });
    });
}

function switchAdminTab(tabName) {
    const docsTab      = document.getElementById('adminDocsTab');
    const uploadTab    = document.getElementById('adminUploadTab');
    const queriesTab   = document.getElementById('adminQueriesTab');
    const statsTab     = document.getElementById('adminStatsTab');

    // Hide all tabs
    [docsTab, uploadTab, queriesTab, statsTab].forEach(t => t && t.classList.add('hidden'));

    if (tabName === 'adminDocs' || tabName === 'adminDocsTab') {
        docsTab.classList.remove('hidden');
        loadAdminDocuments();
    } else if (tabName === 'adminUpload' || tabName === 'adminUploadTab') {
        uploadTab.classList.remove('hidden');
    } else if (tabName === 'adminQueries' || tabName === 'adminQueriesTab') {
        queriesTab.classList.remove('hidden');
        loadStudentQueries();
    } else if (tabName === 'adminStats' || tabName === 'adminStatsTab') {
        statsTab.classList.remove('hidden');
        loadAdminStats();
    }
}

function setupFileUploadDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('docFileInput');
    const namePreview = document.getElementById('selectedFileName');

    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            namePreview.innerText = `Selected: ${fileInput.files[0].name}`;
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-blue)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border-color)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            namePreview.innerText = `Selected: ${fileInput.files[0].name}`;
        }
    });
}

function setupUploadForm() {
    const form = document.getElementById('uploadDocForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const title      = document.getElementById('docTitle').value.trim();
        const department = document.getElementById('docDept').value;
        const category   = document.getElementById('docCategory').value;
        const fileInput  = document.getElementById('docFileInput');

        if (!fileInput.files || fileInput.files.length === 0) {
            showToast('Please select a document file.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('title', title);
        formData.append('department', department);
        formData.append('category', category);

        const submitBtn = document.getElementById('uploadSubmitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing & Chunking...';

        try {
            await apiRequest('/api/admin/documents', 'POST', formData, true);
            showToast('Document uploaded and stored in Knowledge Base!', 'success');
            form.reset();
            document.getElementById('selectedFileName').innerText = '';
            switchAdminTab('adminDocs');
        } catch (err) {
            showToast(err.message || 'Upload failed', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-gears"></i> Process & Store Document';
        }
    });
}

async function loadAdminDocuments() {
    const tbody = document.getElementById('documentsTableBody');
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Loading documents...</td></tr>';

    try {
        const docs = await apiRequest('/api/admin/documents');
        tbody.innerHTML = '';

        if (docs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No documents in Knowledge Base yet. Upload one!</td></tr>';
            return;
        }

        docs.forEach(d => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <strong>${escapeHtml(d.title)}</strong><br>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(d.file_name)}</span>
                </td>
                <td><span class="role-badge">${d.file_type}</span></td>
                <td>${escapeHtml(d.department)}</td>
                <td>${escapeHtml(d.category)}</td>
                <td>${d.upload_date}</td>
                <td><strong>${d.chunks_count}</strong></td>
                <td><span style="color: var(--accent-green); font-weight: 600;">PROCESSED</span></td>
                <td>
                    <button class="icon-btn" title="Reprocess Document" onclick="reprocessDoc(${d.id})">
                        <i class="fa-solid fa-rotate"></i>
                    </button>
                    <button class="icon-btn text-danger" title="Delete Document" onclick="deleteDoc(${d.id})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {}
}

async function reprocessDoc(docId) {
    if (!confirm('Reprocess document? This will recreate all vector chunks.')) return;
    try {
        await apiRequest(`/api/admin/documents/${docId}/reprocess`, 'POST');
        showToast('Document reprocessed successfully', 'success');
        loadAdminDocuments();
    } catch (err) {}
}

async function deleteDoc(docId) {
    if (!confirm('Are you sure you want to delete this document from the knowledge base? This action cannot be undone.')) return;
    try {
        await apiRequest(`/api/admin/documents/${docId}`, 'DELETE');
        showToast('Document deleted from knowledge base', 'info');
        loadAdminDocuments();
    } catch (err) {}
}

// ─── Student Queries (Admin-Only) ─────────────────────────────────────────────

async function loadStudentQueries() {
    const tbody = document.getElementById('queriesTableBody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Loading queries...</td></tr>';

    try {
        const queries = await apiRequest('/api/admin/queries?limit=100');
        tbody.innerHTML = '';

        if (!queries || queries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted);">No student queries recorded yet.</td></tr>';
            return;
        }

        queries.forEach(q => {
            const tr = document.createElement('tr');

            // Format sources
            let sourcesHtml = '<span style="color:var(--text-muted);font-size:0.78rem;">—</span>';
            if (q.sources && q.sources.length > 0) {
                sourcesHtml = q.sources.map(s =>
                    `<span style="font-size:0.75rem;display:block;">📄 ${escapeHtml(s.document_name || '')} p.${s.page || '?'}</span>`
                ).join('');
            }

            tr.innerHTML = `
                <td>
                    <strong style="font-size:0.82rem;">${escapeHtml(q.student_name)}</strong><br>
                    <span style="color:var(--text-muted);font-size:0.75rem;">${escapeHtml(q.student_email)}</span>
                </td>
                <td style="max-width:200px; font-size:0.83rem;">${escapeHtml(q.question)}</td>
                <td style="max-width:240px; font-size:0.82rem; color:var(--text-muted);">${escapeHtml((q.answer||'').substring(0,180))}${(q.answer||'').length>180?'…':''}</td>
                <td>${sourcesHtml}</td>
                <td style="font-size:0.78rem; color:var(--text-muted); white-space:nowrap;">${escapeHtml(q.timestamp)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--accent-red);">Failed to load queries.</td></tr>';
    }
}

// ─── Extended Analytics ────────────────────────────────────────────────────────

async function loadAdminStats() {
    try {
        const stats = await apiRequest('/api/admin/analytics');

        // Primary stat cards
        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val ?? '—'; };
        setEl('statTotalStudents',  stats.total_students);
        setEl('statActiveStudents', stats.active_students);
        setEl('statTotalQuestions', stats.total_questions);
        setEl('statTotalSessions',  stats.total_sessions);
        setEl('statTotalDocs',      stats.total_documents);
        setEl('statTotalChunks',    stats.total_chunks);

        // Render question trends bar chart (pure CSS/HTML bars)
        renderTrendsChart(stats.question_trends || []);

        // Top questions
        renderTopQuestions(stats.top_questions || []);

        // Recent activity
        renderRecentActivity(stats.recent_activity || []);

    } catch (err) {
        showToast('Failed to load analytics', 'error');
    }
}

function renderTrendsChart(trends) {
    const container = document.getElementById('trendsChart');
    if (!container) return;

    const maxCount = Math.max(...trends.map(t => t.count), 1);

    container.innerHTML = `
        <div style="display:flex; align-items:flex-end; gap:8px; height:100px; padding-bottom: 4px;">
            ${trends.map(t => {
                const heightPct = Math.max(4, Math.round((t.count / maxCount) * 100));
                return `
                    <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:4px;">
                        <span style="font-size:0.7rem; color:var(--text-muted);">${t.count}</span>
                        <div style="
                            width:100%;
                            height:${heightPct}px;
                            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple, #7c3aed));
                            border-radius:4px 4px 0 0;
                            transition: height 0.4s ease;
                        " title="${t.date}: ${t.count} question${t.count !== 1 ? 's' : ''}"></div>
                        <span style="font-size:0.65rem; color:var(--text-muted);">${t.date}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderTopQuestions(questions) {
    const list = document.getElementById('topQuestionsList');
    if (!list) return;

    if (!questions || questions.length === 0) {
        list.innerHTML = '<li style="color:var(--text-muted)">No questions asked yet.</li>';
        return;
    }

    list.innerHTML = questions.map(q =>
        `<li title="${escapeHtml(q.question)}">
            ${escapeHtml(q.question.length > 70 ? q.question.substring(0, 70) + '…' : q.question)}
            <span style="color:var(--accent-blue); font-size:0.75rem; margin-left:4px;">(${q.count}×)</span>
        </li>`
    ).join('');
}

function renderRecentActivity(activity) {
    const container = document.getElementById('recentActivityList');
    if (!container) return;

    if (!activity || activity.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted)">No recent activity.</p>';
        return;
    }

    container.innerHTML = activity.map(a => `
        <div style="border-bottom: 1px solid var(--border-color); padding: 6px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:0.8rem;">${escapeHtml(a.student_name)}</strong>
                <span style="color:var(--text-muted); font-size:0.72rem;">${escapeHtml(a.timestamp)}</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.78rem; margin-top:2px; line-height:1.4;">
                ${escapeHtml(a.question.length > 90 ? a.question.substring(0, 90) + '…' : a.question)}
            </div>
        </div>
    `).join('');
}

// Helper (shared with chat.js)
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
