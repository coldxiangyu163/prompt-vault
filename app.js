/* ===== PromptVault App ===== */

const STYLE_TAGS = [
    { key: 'portrait', label: '人像', color: '#a78bfa' },
    { key: 'photography', label: '摄影', color: '#60a5fa' },
    { key: 'fashion', label: '时尚', color: '#f472b6' },
    { key: 'landscape', label: '风景', color: '#34d399' },
    { key: 'anime', label: '动漫', color: '#fb923c' },
    { key: 'infographic', label: '信息图', color: '#2dd4bf' },
    { key: '3D', label: '3D渲染', color: '#22d3ee' },
    { key: 'fantasy', label: '奇幻', color: '#c084fc' },
    { key: '玻璃拟态', label: '玻璃拟态', color: '#e879f9' },
    { key: '产品展示', label: '产品展示', color: '#fbbf24' },
    { key: '卡通', label: '卡通', color: '#f87171' },
];

const TOOL_TAGS = [
    { key: 'Nano Banana Pro', label: 'Nano Banana Pro', color: '#a78bfa' },
    { key: 'Nano Banana', label: 'Nano Banana', color: '#c084fc' },
    { key: 'Gemini', label: 'Gemini', color: '#60a5fa' },
    { key: 'Midjourney', label: 'Midjourney', color: '#fb923c' },
    { key: 'Flux', label: 'Flux', color: '#34d399' },
    { key: 'Stable Diffusion', label: 'Stable Diffusion', color: '#f472b6' },
    { key: 'DALL-E', label: 'DALL-E', color: '#22d3ee' },
];

let allPrompts = [];
let activeFilter = 'all';
let searchQuery = '';
const PAGE_SIZE = 20;
let currentPage = 1;
let isLoading = false;

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

// ===== Render Gallery (paginated) =====
function renderGallery(append = false) {
    const gallery = document.getElementById('gallery');
    const empty = document.getElementById('emptyState');
    const filtered = getFilteredPrompts();

    if (!append) {
        currentPage = 1;
        gallery.innerHTML = '';
    }

    if (filtered.length === 0) {
        gallery.innerHTML = '';
        empty.style.display = 'block';
        updateLoadMore(0, 0);
        return;
    }
    empty.style.display = 'none';

    const start = (currentPage - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, filtered.length);
    const pageItems = filtered.slice(start, end);

    const html = pageItems.map((item, i) => {
        const globalIdx = allPrompts.indexOf(item);
        const delay = append ? i * 0.05 : (start + i) * 0.05;
        const thumbSrc = getThumbUrl(item.images[0]);
        return `
        <div class="card" data-index="${globalIdx}" style="animation-delay:${Math.min(delay, 1)}s">
            <div class="card-image-wrap">
                <img class="card-image" src="${thumbSrc}" data-full="${item.images[0]}" alt="" loading="lazy"
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
        </div>`;
    }).join('');

    gallery.insertAdjacentHTML('beforeend', html);
    updateLoadMore(end, filtered.length);
}

// Thumbnail: use smaller version for cards
function getThumbUrl(url) {
    if (!url) return '';
    // X images: swap name=large to name=small
    if (url.includes('pbs.twimg.com')) {
        return url.replace('name=large', 'name=small').replace('name=medium', 'name=small');
    }
    return url;
}

function updateLoadMore(loaded, total) {
    let el = document.getElementById('loadMoreWrap');
    if (!el) {
        el = document.createElement('div');
        el.id = 'loadMoreWrap';
        el.style.cssText = 'text-align:center;padding:2rem 0;';
        document.getElementById('gallery').parentNode.appendChild(el);
    }
    if (loaded >= total || total === 0) {
        el.innerHTML = total > 0 ? `<span style="color:#666;font-size:0.9rem">已加载全部 ${total} 条</span>` : '';
    } else {
        el.innerHTML = `<button id="loadMoreBtn" class="filter-tag active" style="padding:0.6rem 2rem;font-size:0.95rem">加载更多 (${loaded}/${total})</button>`;
        document.getElementById('loadMoreBtn').addEventListener('click', loadMore);
    }
}

function loadMore() {
    if (isLoading) return;
    isLoading = true;
    currentPage++;
    renderGallery(true);
    isLoading = false;
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

    document.getElementById('modalImage').src = item.images[0]; // full size
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
            renderGallery(false);
        }, 200);
    });

    // Infinite scroll
    window.addEventListener('scroll', () => {
        if (isLoading) return;
        const scrollBottom = window.innerHeight + window.scrollY;
        const docHeight = document.documentElement.scrollHeight;
        if (scrollBottom >= docHeight - 300) {
            const filtered = getFilteredPrompts();
            if (currentPage * PAGE_SIZE < filtered.length) {
                loadMore();
            }
        }
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
