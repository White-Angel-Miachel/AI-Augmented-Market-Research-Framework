/**
 * AI Market Research Pipeline — Frontend Logic
 * Handles drag-and-drop uploads, processing, and result display
 */

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const uploadBtn = document.getElementById('uploadBtn');
const processing = document.getElementById('processing');
const resultsSection = document.getElementById('resultsSection');
const errorMsg = document.getElementById('errorMsg');
const uploadCard = document.getElementById('uploadCard');

let selectedFile = null;
let rawMarkdown = '';

// ── Drag & Drop ──────────────────────────────────────────
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) selectFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) selectFile(e.target.files[0]);
});

function selectFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(ext)) {
        showError('Unsupported file type. Please upload PDF, DOCX, or TXT files.');
        return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatSize(file.size);
    fileInfo.classList.add('visible');
    uploadBtn.disabled = false;
    hideError();
}

function removeFile(e) {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.remove('visible');
    uploadBtn.disabled = true;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Upload & Process ─────────────────────────────────────
uploadBtn.addEventListener('click', () => {
    if (!selectedFile) return;
    uploadAndProcess();
});

async function uploadAndProcess() {
    // Show processing state
    uploadCard.style.display = 'none';
    processing.classList.add('visible');
    resultsSection.classList.remove('visible');
    hideError();

    // Reset steps
    const steps = document.querySelectorAll('.step');
    steps.forEach(s => { s.classList.remove('active', 'done'); });

    // Animate steps progressively
    let currentStep = 0;
    function advanceStep() {
        if (currentStep > 0 && currentStep <= steps.length) {
            steps[currentStep - 1].classList.remove('active');
            steps[currentStep - 1].classList.add('done');
        }
        if (currentStep < steps.length) {
            steps[currentStep].classList.add('active');
        }
        currentStep++;
    }

    advanceStep(); // Step 1: Parsing
    const stepTimer = setInterval(() => {
        if (currentStep < steps.length) advanceStep();
    }, 8000);

    // Upload
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(stepTimer);
        // Mark all steps as done
        steps.forEach(s => { s.classList.remove('active'); s.classList.add('done'); });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Processing failed');
        }

        // Brief pause for visual completion, then show results
        setTimeout(() => {
            processing.classList.remove('visible');
            displayResults(data);
        }, 600);

    } catch (err) {
        clearInterval(stepTimer);
        processing.classList.remove('visible');
        uploadCard.style.display = 'block';
        showError('Analysis failed: ' + err.message);
    }
}

// ── Display Results ──────────────────────────────────────
function displayResults(data) {
    // Meta info
    document.getElementById('resSector').textContent = data.sector || 'N/A';

    const strength = data.signal_strength;
    const strengthEl = document.getElementById('resStrength');
    if (strength && strength !== 'N/A') {
        strengthEl.textContent = strength + '/10';
    } else {
        strengthEl.textContent = 'N/A';
    }

    document.getElementById('resTime').textContent = formatTimestamp(data.processed_at);

    // Download buttons
    const grid = document.getElementById('downloadGrid');
    grid.innerHTML = '';
    const iconMap = {
        'md':   { label: 'MD',   desc: 'Markdown Report', cls: 'md' },
        'docx': { label: 'DOC',  desc: 'Word Document',   cls: 'docx' },
        'json': { label: '{ }',  desc: 'JSON Data',       cls: 'json' },
        'xlsx': { label: 'XLS',  desc: 'Excel Summary',   cls: 'xlsx' }
    };

    data.files.forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        const info = iconMap[ext] || { label: '?', desc: file.type, cls: '' };
        const a = document.createElement('a');
        a.href = `/download/${file.name}`;
        a.className = 'download-item';
        a.innerHTML = `
            <div class="dl-icon ${info.cls}">${info.label}</div>
            <div class="dl-info">
                <div class="dl-type">${info.desc}</div>
                <div class="dl-desc">${file.name}</div>
            </div>
        `;
        grid.appendChild(a);
    });

    // Preview — render markdown to HTML
    rawMarkdown = data.preview || '';
    const renderedPreview = document.getElementById('renderedPreview');
    const rawPreview = document.getElementById('rawPreview');

    if (typeof marked !== 'undefined' && rawMarkdown) {
        renderedPreview.innerHTML = marked.parse(rawMarkdown);
    } else {
        renderedPreview.textContent = rawMarkdown || 'No preview available.';
    }
    rawPreview.textContent = rawMarkdown;

    // Reset to rendered tab
    switchTab('rendered');

    resultsSection.classList.add('visible');
}

function formatTimestamp(iso) {
    if (!iso) return 'Just now';
    const d = new Date(iso);
    return d.toLocaleString();
}

// ── Preview Tabs ─────────────────────────────────────────
function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(t => t.classList.remove('active'));

    const rendered = document.getElementById('renderedPreview');
    const raw = document.getElementById('rawPreview');

    if (tabName === 'rendered') {
        tabs[0].classList.add('active');
        rendered.style.display = 'block';
        raw.style.display = 'none';
    } else {
        tabs[1].classList.add('active');
        rendered.style.display = 'none';
        raw.style.display = 'block';
    }
}

// ── New Analysis ─────────────────────────────────────────
function newAnalysis() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.remove('visible');
    uploadBtn.disabled = true;
    resultsSection.classList.remove('visible');
    processing.classList.remove('visible');
    uploadCard.style.display = 'block';
    hideError();

    document.querySelectorAll('.step').forEach(s => {
        s.classList.remove('active', 'done');
    });

    // Refresh history
    loadHistory();
}

// ── Error ────────────────────────────────────────────────
function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.add('visible');
}

function hideError() {
    errorMsg.classList.remove('visible');
}

// ── Load Previous Results ────────────────────────────────
async function loadHistory() {
    try {
        const res = await fetch('/results');
        const data = await res.json();
        const list = document.getElementById('historyList');

        if (data.length === 0) {
            list.innerHTML = '<p style="color: var(--text-dim); font-size: 0.85rem; text-align: center; padding: 1.5rem;">No previous analyses found. Upload a report to get started.</p>';
            return;
        }

        list.innerHTML = '';
        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';

            const actions = item.files.map(f =>
                `<a href="/download/${f.name}" title="Download ${f.type}">${f.type}</a>`
            ).join('');

            const ts = item.timestamp;
            const formattedTime = ts
                ? `${ts.slice(0,4)}-${ts.slice(4,6)}-${ts.slice(6,8)} ${ts.slice(9,11)}:${ts.slice(11,13)}`
                : '';

            div.innerHTML = `
                <span class="hist-name">${item.report_name}</span>
                <span class="hist-time">${formattedTime}</span>
                <div class="hist-actions">${actions}</div>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

// Init
document.addEventListener('DOMContentLoaded', loadHistory);
