/* ===== PromptVault App ===== */

// 标签颜色映射（已知标签给固定颜色，未知标签自动分配）
const TAG_COLORS = {
    'infographic': '#2dd4bf', '信息图': '#2dd4bf',
    'poster': '#f472b6', 'movie-poster': '#c084fc',
    'fashion': '#f472b6', 'collage': '#fb923c',
    'layout': '#60a5fa', 'template': '#a78bfa',
    'recipe-card': '#34d399', '3D': '#22d3ee',
    'portrait': '#a78bfa', 'landscape': '#34d399',
    'retro': '#e879f9', 'ad-poster': '#fbbf24',
    'product-showcase': '#38bdf8', 'packaging': '#38bdf8',
    'branding': '#fb7185', 'sports': '#f87171',
    'business-card': '#a3e635', 'landing-page': '#22d3ee',
    'illustration': '#f87171', 'data-visualization': '#fbbf24',
    '玻璃拟态': '#a3e635', '产品展示': '#38bdf8', '卡通': '#fb7185',
    'bento': '#60a5fa', '旅游攻略': '#34d399', '哆啦A梦': '#22d3ee',
};
const TAG_LABELS = {
    'infographic': '信息图', '信息图': '信息图',
    'poster': '海报', 'movie-poster': '电影海报',
    'fashion': '时尚', 'collage': '拼贴',
    'layout': '布局', 'template': '模板',
    'recipe-card': '食谱卡', '3D': '3D渲染',
    'portrait': '人像', 'landscape': '风景',
    'retro': '复古', 'ad-poster': '广告海报',
    'product-showcase': '产品展示', 'packaging': '包装',
    'branding': '品牌', 'sports': '运动',
    'business-card': '名片', 'landing-page': '落地页',
    'illustration': '插画', 'data-visualization': '数据可视化',
    '玻璃拟态': '玻璃拟态', '产品展示': '产品展示', '卡通': '卡通',
    'bento': 'Bento', '旅游攻略': '旅游攻略', '哆啦A梦': '哆啦A梦',
};
const PALETTE = ['#a78bfa','#60a5fa','#f472b6','#34d399','#fb923c','#22d3ee','#c084fc','#e879f9','#fbbf24','#f87171','#a3e635','#38bdf8','#fb7185'];

// 动态从数据生成 STYLE_TAGS（加载数据后调用）
let STYLE_TAGS = [];

const TOOL_TAGS = [
    { key: 'Nano Banana Pro', label: 'Nano Banana Pro', color: '#a78bfa' },
    { key: 'Nano Banana', label: 'Nano Banana', color: '#c084fc' },
    { key: 'Gemini', label: 'Gemini', color: '#60a5fa' },
    { key: 'Midjourney', label: 'Midjourney', color: '#fb923c' },
    { key: 'Flux', label: 'Flux', color: '#34d399' },
    { key: 'Stable Diffusion', label: 'Stable Diffusion', color: '#f472b6' },
    { key: 'DALL-E', label: 'DALL-E', color: '#22d3ee' },
];

// Will be updated after data loads
function updateToolTagCounts() {
    const toolCount = {};
    allPrompts.forEach(p => { toolCount[p.tool] = (toolCount[p.tool] || 0) + 1; });
    TOOL_TAGS.forEach(t => {
        const count = toolCount[t.key] || 0;
        t.label = `${t.key} (${count})`;
    });
}

let allPrompts = [];
let activeFilter = 'all';
let searchQuery = '';
const PAGE_SIZE = 20;
let currentPage = 1;
let isLoading = false;
let currentModalIndex = -1; // Track current modal prompt index

// ===== Init =====
document.addEventListener('DOMContentLoaded', async () => {
    await loadPrompts();
    bindEvents();
});

// ===== Load Data =====
async function loadPrompts() {
    const spinner = document.getElementById('loadingSpinner');
    try {
        const res = await fetch('data/prompts.json');
        allPrompts = await res.json();
        document.getElementById('totalCount').textContent = allPrompts.length;
        buildDynamicTags();
        updateToolTagCounts();
        renderFilterTags();
        renderGallery();
        // Check deep link
        handleDeepLink();
    } catch (e) {
        console.error('Failed to load prompts:', e);
    } finally {
        if (spinner) spinner.style.display = 'none';
    }
}

function buildDynamicTags() {
    // 统计所有标签出现次数
    const tagCount = {};
    allPrompts.forEach(p => {
        (p.tags || []).forEach(t => { tagCount[t] = (tagCount[t] || 0) + 1; });
    });
    // 按出现次数排序，取 top 15
    const sorted = Object.entries(tagCount).sort((a, b) => b[1] - a[1]).slice(0, 15);
    let colorIdx = 0;
    STYLE_TAGS = sorted.map(([key, count]) => ({
        key,
        label: (TAG_LABELS[key] || key) + ` (${count})`,
        color: TAG_COLORS[key] || PALETTE[colorIdx++ % PALETTE.length],
    }));
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

    // Set initial max-height for collapsible sections
    document.querySelectorAll('.sidebar-section-body').forEach(body => {
        body.style.maxHeight = body.scrollHeight + 'px';
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
        const isNew = item.created_at && (Date.now() - new Date(item.created_at).getTime()) < 7 * 24 * 60 * 60 * 1000;
        return `
        <div class="card" data-index="${globalIdx}" style="animation-delay:${Math.min(delay, 1)}s">
            <div class="card-image-wrap">
                ${isNew ? '<span class="card-badge-new">NEW</span>' : ''}
                <img class="card-image" src="${thumbSrc}" data-full="${item.images[0]}" alt="" loading="lazy"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 400 300%22><rect fill=%22%2318182a%22 width=%22400%22 height=%22300%22/><text x=%2250%25%22 y=%2250%25%22 fill=%22%2355556a%22 font-size=%2240%22 text-anchor=%22middle%22 dy=%22.3em%22>🎨</text></svg>'">
            </div>
            <div class="card-body">
                <p class="card-prompt">${escapeHtml(item.prompt.length > 120 ? item.prompt.substring(0, 120) + '...' : item.prompt)}</p>
            </div>
            <div class="card-footer">
                <div class="card-tags">
                    ${item.tags.slice(0, 3).map(t => {
                        const c = TAG_COLORS[t] || '';
                        return c ? `<span class="card-tag" style="border-left:2px solid ${c};padding-left:5px">${t}</span>` : `<span class="card-tag">${t}</span>`;
                    }).join('')}
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

// ===== OG Meta Helpers =====
const OG_DEFAULTS = {
    'og:title': 'PromptVault — AI 生图提示词视觉图库',
    'og:description': '190+ 精选 AI 绘图提示词，免费开源一键复用',
    'twitter:title': 'PromptVault - AI Prompt Gallery',
    'twitter:description': 'Discover and share AI art prompts for Stable Diffusion, Midjourney, DALL-E and more',
};

function updateMetaTag(attr, attrValue, content) {
    let el = document.querySelector(`meta[${attr}="${attrValue}"]`);
    if (el) {
        el.setAttribute('content', content);
    }
}

function setOGForPrompt(item) {
    const title = `${item.prompt.substring(0, 60)}... | PromptVault`;
    const desc = `${item.tool} prompt by ${item.author} — ${item.tags.slice(0, 3).join(', ')}`;
    updateMetaTag('property', 'og:title', title);
    updateMetaTag('property', 'og:description', desc);
    updateMetaTag('name', 'twitter:title', title);
    updateMetaTag('name', 'twitter:description', desc);
}

function restoreOGDefaults() {
    updateMetaTag('property', 'og:title', OG_DEFAULTS['og:title']);
    updateMetaTag('property', 'og:description', OG_DEFAULTS['og:description']);
    updateMetaTag('name', 'twitter:title', OG_DEFAULTS['twitter:title']);
    updateMetaTag('name', 'twitter:description', OG_DEFAULTS['twitter:description']);
}

// ===== Modal =====
function openModal(index) {
    const item = allPrompts[index];
    if (!item) return;
    currentModalIndex = index;

    const modalImg = document.getElementById('modalImage');
    modalImg.src = item.images[0];
    modalImg.onerror = function() {
        this.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400"><rect fill="#18182a" width="600" height="400"/><text x="50%" y="50%" fill="#55556a" font-size="48" text-anchor="middle" dy=".3em">🎨 图片加载失败</text></svg>');
    };
    document.getElementById('modalAuthor').textContent = item.author;
    document.getElementById('modalTool').textContent = item.tool;
    document.getElementById('modalDate').textContent = item.created_at;
    document.getElementById('modalPrompt').textContent = item.prompt;

    // Show character count
    const charCount = item.prompt ? item.prompt.length : 0;
    const promptHeader = document.querySelector('.modal-prompt-header');
    if (promptHeader) {
        promptHeader.innerHTML = `📋 提示词 <span style="font-size:0.75em;color:var(--fg-muted);font-weight:normal;margin-left:6px">(${charCount} chars)</span>`;
    }

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

    // Update URL with deep link
    const url = new URL(window.location);
    url.searchParams.set('id', index);
    window.history.replaceState(null, '', url);

    // Update OG meta for social sharing
    setOGForPrompt(item);

    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
    currentModalIndex = -1;
    // Restore default OG meta
    restoreOGDefaults();
    // Remove id from URL
    const url = new URL(window.location);
    url.searchParams.delete('id');
    window.history.replaceState(null, '', url);
}

// Navigate to prev/next prompt in modal
function navigateModal(direction) {
    const filtered = getFilteredPrompts();
    if (filtered.length === 0) return;
    const currentItem = allPrompts[currentModalIndex];
    const currentFilteredIdx = filtered.indexOf(currentItem);
    if (currentFilteredIdx === -1) return;
    const nextFilteredIdx = (currentFilteredIdx + direction + filtered.length) % filtered.length;
    const nextGlobalIdx = allPrompts.indexOf(filtered[nextFilteredIdx]);
    openModal(nextGlobalIdx);
}

// Deep link handler
function handleDeepLink() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (id !== null && allPrompts[parseInt(id)]) {
        openModal(parseInt(id));
    }
}

// ===== Update Clear Button Visibility =====
function updateClearBtn() {
    const btn = document.getElementById('filterClear');
    if (activeFilter !== 'all' || searchQuery) {
        btn.classList.add('visible');
    } else {
        btn.classList.remove('visible');
    }
}

// ===== Events =====
function bindEvents() {
    const sidebar = document.getElementById('sidebar');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebarExpand = document.getElementById('sidebarExpand');
    const mobileFilterBtn = document.getElementById('mobileFilterBtn');
    const drawerOverlay = document.getElementById('drawerOverlay');

    // Sidebar collapse/expand (desktop)
    sidebarCollapse.addEventListener('click', () => {
        sidebar.classList.add('collapsed');
    });
    sidebarExpand.addEventListener('click', () => {
        sidebar.classList.remove('collapsed');
    });

    // Mobile drawer open/close
    mobileFilterBtn.addEventListener('click', () => {
        sidebar.classList.add('mobile-open');
        drawerOverlay.classList.add('active');
    });
    drawerOverlay.addEventListener('click', () => {
        sidebar.classList.remove('mobile-open');
        drawerOverlay.classList.remove('active');
    });

    // Section collapse/expand
    document.querySelectorAll('.sidebar-section-title').forEach(title => {
        title.addEventListener('click', () => {
            title.classList.toggle('collapsed');
            const body = title.nextElementSibling;
            body.classList.toggle('collapsed');
        });
    });

    // Filter clicks (sidebar)
    sidebar.addEventListener('click', e => {
        const btn = e.target.closest('.filter-tag');
        if (!btn) return;

        document.querySelectorAll('.filter-tag').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        updateClearBtn();
        renderGallery();

        // Close mobile drawer after selection
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('mobile-open');
            drawerOverlay.classList.remove('active');
        }
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

    // Modal navigation buttons
    document.getElementById('modalPrev').addEventListener('click', (e) => {
        e.stopPropagation();
        navigateModal(-1);
    });
    document.getElementById('modalNext').addEventListener('click', (e) => {
        e.stopPropagation();
        navigateModal(1);
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

    // Copy link button
    document.getElementById('copyLinkBtn').addEventListener('click', async () => {
        const btn = document.getElementById('copyLinkBtn');
        const spanEl = btn.querySelector('span');
        try {
            await navigator.clipboard.writeText(window.location.href);
            btn.classList.add('copied');
            if (spanEl) spanEl.textContent = '已复制';
            setTimeout(() => { btn.classList.remove('copied'); if (spanEl) spanEl.textContent = '复制链接'; }, 2000);
        } catch (err) { console.error('Copy link failed:', err); }
    });

    // Twitter share button
    document.getElementById('shareTwitterBtn').addEventListener('click', () => {
        const item = allPrompts[currentModalIndex];
        if (!item) return;
        const text = `${item.prompt.substring(0, 200)}${item.prompt.length > 200 ? '...' : ''}\n\n🎨 via PromptVault`;
        const shareUrl = window.location.href;
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`;
        window.open(twitterUrl, '_blank', 'width=600,height=400,noopener,noreferrer');
    });

    // Native share button (Web Share API)
    const shareNativeBtn = document.getElementById('shareNativeBtn');
    if (navigator.share) {
        shareNativeBtn.addEventListener('click', async () => {
            const item = allPrompts[currentModalIndex];
            if (!item) return;
            try {
                await navigator.share({
                    title: `PromptVault — ${item.tool} prompt`,
                    text: item.prompt.substring(0, 200),
                    url: window.location.href,
                });
            } catch (err) {
                if (err.name !== 'AbortError') console.error('Share failed:', err);
            }
        });
    } else {
        // Hide native share button if Web Share API not supported
        shareNativeBtn.style.display = 'none';
    }

    // Clear filter button
    const clearBtn = document.getElementById('filterClear');
    clearBtn.addEventListener('click', () => {
        activeFilter = 'all';
        searchQuery = '';
        searchInput.value = '';
        document.querySelectorAll('.filter-tag').forEach(b => b.classList.remove('active'));
        document.querySelector('.filter-tag[data-filter="all"]').classList.add('active');
        clearBtn.classList.remove('visible');
        renderGallery();
    });

    // Search
    const searchInput = document.getElementById('searchInput');
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchQuery = searchInput.value.toLowerCase().trim();
            updateClearBtn();
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
        const modalActive = document.getElementById('modalOverlay').classList.contains('active');
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
        if (e.key === 'Escape') {
            if (modalActive) {
                closeModal();
            } else {
                searchInput.blur();
                searchInput.value = '';
                searchQuery = '';
                renderGallery();
            }
        }
        // Arrow key navigation in modal
        if (modalActive && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
            e.preventDefault();
            navigateModal(e.key === 'ArrowRight' ? 1 : -1);
        }
    });

    // Touch swipe navigation for modal (mobile)
    let touchStartX = 0;
    let touchStartY = 0;
    const modalOverlay = document.getElementById('modalOverlay');
    modalOverlay.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });
    modalOverlay.addEventListener('touchend', e => {
        if (!modalOverlay.classList.contains('active')) return;
        const dx = e.changedTouches[0].screenX - touchStartX;
        const dy = e.changedTouches[0].screenY - touchStartY;
        // Only trigger if horizontal swipe > 50px and more horizontal than vertical
        if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
            navigateModal(dx < 0 ? 1 : -1);
        }
    }, { passive: true });
}

// ===== Utils =====
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ===== Back to Top =====
(function() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;
    window.addEventListener('scroll', () => {
        if (window.scrollY > 400) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
