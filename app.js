/* ===== PromptVault App ===== */

const STYLE_TAGS = [
    { key: '玻璃拟态', label: '玻璃拟态', color: '#a78bfa' },
    { key: 'bento', label: 'Bento', color: '#60a5fa' },
    { key: '3D', label: '3D渲染', color: '#f472b6' },
    { key: '卡通', label: '卡通', color: '#fb923c' },
    { key: '扁平', label: '扁平插画', color: '#34d399' },
    { key: '像素', label: '像素', color: '#22d3ee' },
    { key: '水彩', label: '水彩', color: '#c084fc' },
    { key: '赛博朋克', label: '赛博朋克', color: '#e879f9' },
    { key: '产品展示', label: '产品展示', color: '#fbbf24' },
    { key: '信息图', label: '信息图', color: '#2dd4bf' },
    { key: '海报', label: '海报', color: '#f87171' },
    { key: '旅游攻略', label: '旅游攻略', color: '#38bdf8' },
];

const TOOL_TAGS = [
    { key: 'Gemini', label: 'Gemini', color: '#60a5fa' },
    { key: 'Midjourney', label: 'Midjourney', color: '#a78bfa' },
    { key: 'DALL-E', label: 'DALL-E', color: '#34d399' },
    { key: 'Flux', label: 'Flux', color: '#fb923c' },
    { key: 'Seedance', label: 'Seedance', color: '#f472b6' },
];

let allPrompts = [];
let activeFilter = 'all';
let searchQuery = '';

// ===== Init =====
document.addEventListener('DOMContentLoaded', async () => {
    renderFilterTags();
    await loadPrompts();
    bindEvents();
});

// ===== Load Data =====
async function loadPrompts() {
    try {
        const res = await fetch('data/prompts.json');
        allPrompts = await res.json();
        document.getElementById('totalCount').textContent = allPrompts.length;
        renderGallery();
    } catch (e) {
        console.error('Failed to load prompts:', e);
    }
}

// ===== Render Filter Tags =====
function renderFilterTags() {
    const styleContainer = document.getElementById('styleTags');
    const toolContainer = document.getElementById('toolTags');

    STYLE_TAGS.forEach(tag => {
        styleContainer.appendChild(createFilterBtn(tag));
    });
    TOOL_TAGS.forEach(tag => {
        toolContainer.appendChild(createFilterBtn(tag));
    });
}

function createFilterBtn({ key, label, color }) {
    const btn = document.createElement('button');
    btn.className = 'filter-tag';
    btn.dataset.filter = key;
    btn.innerHTML = `<span class="tag-dot" style="background:${color}"></span>${label}`;
    return btn;
}

// ===== Render Gallery =====
function renderGallery() {
    const gallery = document.getElementById('gallery');
    const empty = document.getElementById('emptyState');
    const filtered = getFilteredPrompts();

    if (filtered.length === 0) {
        gallery.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    gallery.innerHTML = filtered.map((item, i) => `
        <div class="card" data-index="${allPrompts.indexOf(item)}" style="animation-delay:${i * 0.05}s">
            <div class="card-image-wrap">
                <img class="card-image" src="${item.images[0]}" alt="" loading="lazy"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 400 300%22><rect fill=%22%2318182a%22 width=%22400%22 height=%22300%22/><text x=%2250%25%22 y=%2250%25%22 fill=%22%2355556a%22 font-size=%2240%22 text-anchor=%22middle%22 dy=%22.3em%22>🎨</text></svg>'">
            </div>
            <div class="card-body">
                <p class="card-prompt">${escapeHtml(item.prompt.substring(0, 120))}...</p>
            </div>
            <div class="card-footer">
                <div class="card-tags">
                    ${item.tags.slice(0, 3).map(t => `<span class="card-tag">${t}</span>`).join('')}
                </div>
                <div class="card-meta">
                    <span class="card-author">${item.author}</span>
                    <span>${item.tool}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// ===== Filter =====
function getFilteredPrompts() {
    return allPrompts.filter(item => {
        const matchFilter = activeFilter === 'all' ||
            item.tags.some(t => t.includes(activeFilter)) ||
            item.style === activeFilter ||
            item.tool === activeFilter;

        const matchSearch = !searchQuery ||
            item.prompt.toLowerCase().includes(searchQuery) ||
            item.tags.some(t => t.toLowerCase().includes(searchQuery)) ||
            item.author.toLowerCase().includes(searchQuery) ||
            item.tool.toLowerCase().includes(searchQuery);

        return matchFilter && matchSearch;
    });
}

// ===== Modal =====
function openModal(index) {
    const item = allPrompts[index];
    if (!item) return;

    document.getElementById('modalImage').src = item.images[0];
    document.getElementById('modalAuthor').textContent = item.author;
    document.getElementById('modalTool').textContent = item.tool;
    document.getElementById('modalDate').textContent = item.created_at;
    document.getElementById('modalPrompt').textContent = item.prompt;

    const tagsHtml = item.tags.map(t =>
        `<span class="modal-tag-item">${t}</span>`
    ).join('');
    document.getElementById('modalTags').innerHTML = tagsHtml;

    const sourceEl = document.getElementById('modalSource');
    if (item.source_url) {
        sourceEl.href = item.source_url;
        sourceEl.style.display = 'inline-flex';
    } else {
        sourceEl.style.display = 'none';
    }

    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
}

// ===== Events =====
function bindEvents() {
    // Filter clicks
    document.querySelector('.filter-bar').addEventListener('click', e => {
        const btn = e.target.closest('.filter-tag');
        if (!btn) return;

        document.querySelectorAll('.filter-tag').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        renderGallery();
    });

    // Card clicks
    document.getElementById('gallery').addEventListener('click', e => {
        const card = e.target.closest('.card');
        if (!card) return;
        openModal(parseInt(card.dataset.index));
    });

    // Modal close
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeModal();
    });

    // Copy button
    document.getElementById('copyBtn').addEventListener('click', async () => {
        const text = document.getElementById('modalPrompt').textContent;
        try {
            await navigator.clipboard.writeText(text);
            const btn = document.getElementById('copyBtn');
            btn.classList.add('copied');
            btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="20 6 9 17 4 12"/></svg>已复制`;
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>复制`;
            }, 2000);
        } catch (err) {
            console.error('Copy failed:', err);
        }
    });

    // Search
    const searchInput = document.getElementById('searchInput');
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchQuery = searchInput.value.toLowerCase().trim();
            renderGallery();
        }, 200);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
        if (e.key === 'Escape') {
            if (document.getElementById('modalOverlay').classList.contains('active')) {
                closeModal();
            } else {
                searchInput.blur();
                searchInput.value = '';
                searchQuery = '';
                renderGallery();
            }
        }
    });
}

// ===== Utils =====
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
