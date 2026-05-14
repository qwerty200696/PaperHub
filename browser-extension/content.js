/**
 * PaperHub Clipper - Content Script
 * 负责网页内容提取、元数据解析、浮动工具栏
 */

// ==================== 全局变量 ====================
let selectedText = '';
let selectedRange = null;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('[PaperHub Clipper] Content script loaded');
});

// 立即执行的初始化（不等待 DOMContentLoaded）
console.log('[PaperHub Clipper] Content script executing...');

// 确保 Readability 在全局可用
if (typeof Readability === 'undefined') {
    console.warn('[PaperHub Clipper] Readability not found in global scope, trying to load from module...');
    // Readability.js 可能以模块形式加载，尝试从其他位置获取
    if (typeof module !== 'undefined' && module.exports) {
        window.Readability = module.exports;
    }
}

console.log('[PaperHub Clipper] Readability available:', typeof Readability !== 'undefined');

// ==================== 划词选择监听 ====================
document.addEventListener('mouseup', () => {
    const selection = window.getSelection();
    selectedText = selection.toString().trim();
    
    if (selectedText.length > 0) {
        selectedRange = selection.getRangeAt(0);
        showFloatingToolbar(selectedRange);
    } else {
        hideFloatingToolbar();
    }
});

// 点击其他地方隐藏工具栏
document.addEventListener('mousedown', (e) => {
    const toolbar = document.getElementById('paperhub-floating-toolbar');
    if (toolbar) {
        // 如果点击的是工具栏内部，不要隐藏
        if (toolbar.contains(e.target)) {
            console.log('[PaperHub Clipper] Clicked inside toolbar, keeping it visible');
            return;
        }
        // 点击外部才隐藏
        hideFloatingToolbar();
    }
});

// ==================== 浮动工具栏 ====================
function showFloatingToolbar(range) {
    // 移除旧工具栏
    hideFloatingToolbar();
    
    const toolbar = document.createElement('div');
    toolbar.id = 'paperhub-floating-toolbar';
    toolbar.className = 'paperhub-toolbar';
    toolbar.innerHTML = `
        <button class="toolbar-btn" data-action="clip_to_note" title="剪藏到笔记">
            📝 笔记
        </button>
        <button class="toolbar-btn" data-action="clip_to_article" title="剪藏到文章">
            📄 文章
        </button>
        <button class="toolbar-btn" data-action="copy" title="复制">
            📋 复制
        </button>
    `;
    
    // 定位到选区上方
    const rect = range.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    toolbar.style.top = `${rect.top + scrollTop - 50}px`;
    toolbar.style.left = `${rect.left}px`;
    
    document.body.appendChild(toolbar);
    
    // 绑定事件
    console.log('[PaperHub Clipper] Binding toolbar events...');
    toolbar.querySelectorAll('.toolbar-btn').forEach((btn, index) => {
        console.log(`[PaperHub Clipper] Binding event for button ${index}:`, btn.dataset.action);
        btn.addEventListener('click', (e) => {
            console.log('[PaperHub Clipper] Button clicked:', btn.dataset.action);
            e.preventDefault();
            e.stopPropagation();
            const action = btn.dataset.action;
            handleToolbarAction(action);
        });
    });
    console.log('[PaperHub Clipper] Toolbar events bound successfully');
}

function hideFloatingToolbar() {
    const toolbar = document.getElementById('paperhub-floating-toolbar');
    if (toolbar) {
        toolbar.remove();
    }
}

async function handleToolbarAction(action) {
    console.log('[PaperHub Clipper] Toolbar action clicked:', action);
    
    switch (action) {
        case 'clip_to_note':
            await clipSelectionToNote();
            break;
        case 'clip_to_article':
            await clipSelectionToArticle();
            break;
        case 'copy':
            copySelection();
            break;
        default:
            console.warn('[PaperHub Clipper] Unknown action:', action);
    }
    hideFloatingToolbar();
}

// ==================== 剪藏功能 ====================

/**
 * 全文剪藏 - 提取网页正文
 */
async function extractFullPage() {
    try {
        // 使用 Readability.js 提取正文
        const documentClone = document.cloneNode(true);
        const article = new Readability(documentClone, {
            charThreshold: 20,
            keepClasses: true
        }).parse();
        
        if (!article) {
            throw new Error('无法提取页面内容');
        }
        
        // 提取元数据
        const metadata = {
            title: article.title || document.title,
            author: extractAuthor(),
            description: article.excerpt || extractMetaDescription(),
            content: article.content, // HTML 格式
            text_content: article.textContent, // 纯文本
            url: window.location.href,
            published_date: extractPublishDate(),
            images: extractImages(),
            site_name: extractSiteName()
        };
        
        console.log('[PaperHub Clipper] Full page extracted:', metadata.title);
        return metadata;
        
    } catch (error) {
        console.error('[PaperHub Clipper] Extraction failed:', error);
        throw error;
    }
}

/**
 * 选择剪藏 - 保存到笔记库
 */
async function clipSelectionToNote() {
    if (!selectedText) {
        alert('请先选中要剪藏的内容');
        return;
    }
    
    console.log('[PaperHub Clipper] Clipping selection to note:', selectedText.substring(0, 50));
    
    const noteData = {
        title: `剪藏：${document.title.substring(0, 50)}`,
        content: selectedText,
        source_url: window.location.href,
        source_title: document.title,
        tags: [],
        created_at: new Date().toISOString()
    };
    
    // 发送到 background script
    try {
        chrome.runtime.sendMessage({
            action: 'clip_selection',
            data: noteData,
            target_library: 'note'
        }, (response) => {
            console.log('[PaperHub Clipper] Response received:', response);
            if (chrome.runtime.lastError) {
                console.error('[PaperHub Clipper] Send message error:', chrome.runtime.lastError);
                showNotification('❌ 发送失败: ' + chrome.runtime.lastError.message);
                return;
            }
            if (response && response.success) {
                showNotification('✅ 已保存到笔记库');
            } else {
                showNotification('❌ 保存失败: ' + (response?.message || '未知错误'));
            }
        });
    } catch (error) {
        console.error('[PaperHub Clipper] Failed to send message:', error);
        showNotification('❌ 发送失败');
    }
}

/**
 * 选择剪藏 - 保存到文章库
 */
async function clipSelectionToArticle() {
    if (!selectedText) {
        alert('请先选中要剪藏的内容');
        return;
    }
    
    console.log('[PaperHub Clipper] Clipping selection to article:', selectedText.substring(0, 50));
    
    const articleData = {
        title: `剪藏：${document.title.substring(0, 50)}`,
        content: `<blockquote>${selectedText.replace(/\n/g, '<br>')}</blockquote>`,
        source_url: window.location.href,
        original_url: window.location.href,
        author: extractAuthor(),
        published_date: extractPublishDate()
    };
    
    try {
        chrome.runtime.sendMessage({
            action: 'clip_selection',
            data: articleData,
            target_library: 'article'
        }, (response) => {
            console.log('[PaperHub Clipper] Response received:', response);
            if (chrome.runtime.lastError) {
                console.error('[PaperHub Clipper] Send message error:', chrome.runtime.lastError);
                showNotification('❌ 发送失败: ' + chrome.runtime.lastError.message);
                return;
            }
            if (response && response.success) {
                showNotification('✅ 已保存到文章库');
            } else {
                showNotification('❌ 保存失败: ' + (response?.message || '未知错误'));
            }
        });
    } catch (error) {
        console.error('[PaperHub Clipper] Failed to send message:', error);
        showNotification('❌ 发送失败');
    }
}

/**
 * 复制选中文本
 */
function copySelection() {
    navigator.clipboard.writeText(selectedText).then(() => {
        showNotification('📋 已复制到剪贴板');
    });
}

// ==================== 元数据提取辅助函数 ====================

function extractAuthor() {
    // 尝试多种选择器
    const selectors = [
        'meta[name="author"]',
        'meta[property="article:author"]',
        'meta[name="twitter:creator"]',
        '.author',
        '[rel="author"]'
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.content || element.textContent;
        }
    }
    
    return null;
}

function extractMetaDescription() {
    const meta = document.querySelector('meta[name="description"]') ||
                 document.querySelector('meta[property="og:description"]');
    return meta ? meta.content : '';
}

function extractPublishDate() {
    // 尝试多种日期格式
    const selectors = [
        'meta[property="article:published_time"]',
        'meta[name="publication-date"]',
        'time[datetime]',
        '.publish-date',
        '.post-date'
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.content || element.datetime || element.textContent;
        }
    }
    
    return new Date().toISOString();
}

function extractSiteName() {
    const meta = document.querySelector('meta[property="og:site_name"]');
    return meta ? meta.content : new URL(window.location.href).hostname;
}

function extractImages() {
    const images = [];
    const imgElements = document.querySelectorAll('img');
    
    imgElements.forEach(img => {
        if (img.src && !img.src.includes('data:image')) {
            images.push({
                src: img.src,
                alt: img.alt || '',
                width: img.naturalWidth,
                height: img.naturalHeight
            });
        }
    });
    
    return images.slice(0, 10); // 最多提取10张图片
}

// ==================== 通知提示 ====================
function showNotification(message) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = 'paperhub-notification';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 2秒后自动消失
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// ==================== 检测学术网站 ====================
function detectAcademicPage() {
    const url = window.location.href;
    
    if (url.includes('arxiv.org')) {
        return 'arxiv';
    }
    if (url.includes('ieee.org')) {
        return 'ieee';
    }
    if (url.includes('dl.acm.org')) {
        return 'acm';
    }
    if (url.includes('springer.com')) {
        return 'springer';
    }
    
    return null;
}

// ==================== 导出函数供 popup 调用 ====================
console.log('[PaperHub Clipper] Exporting PaperHubClipper...');
window.PaperHubClipper = {
    extractFullPage,
    detectAcademicPage,
    getSelectedText: () => selectedText
};
console.log('[PaperHub Clipper] PaperHubClipper exported:', window.PaperHubClipper);
