/**
 * PaperHub Clipper - Popup Script
 * 主控制面板逻辑
 */

// ==================== 全局状态 ====================
let currentPageInfo = null;
let selectedMode = 'full'; // full | selection | smart | quick
let isProcessing = false;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[PaperHub Clipper] Popup loaded');
    
    // 获取当前页面信息
    await loadCurrentPageInfo();
    
    // 绑定事件
    bindEvents();
});

// ==================== 加载页面信息 ====================
async function loadCurrentPageInfo() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab) {
            showError('无法获取当前页面信息');
            return;
        }
        
        currentPageInfo = {
            title: tab.title,
            url: tab.url,
            id: tab.id
        };
        
        // 更新 UI
        document.getElementById('page-title').textContent = tab.title;
        document.getElementById('page-url').textContent = tab.url;
        
        // 显示主内容
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        
        // 检测是否为学术网站
        await checkAcademicPage(tab.id);
        
    } catch (error) {
        console.error('[PaperHub Clipper] Failed to load page info:', error);
        showError('加载页面信息失败');
    }
}

// ==================== 检测学术网站 ====================
async function checkAcademicPage(tabId) {
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: () => {
                // 这个函数会在页面上下文中执行
                if (window.PaperHubClipper) {
                    return window.PaperHubClipper.detectAcademicPage();
                }
                return null;
            }
        });
        
        const academicType = results[0]?.result;
        
        if (academicType) {
            console.log('[PaperHub Clipper] Detected academic page:', academicType);
            // 可以在此处调整 UI，突出显示论文剪藏模式
        }
        
    } catch (error) {
        console.warn('[PaperHub Clipper] Academic detection failed:', error);
    }
}

// ==================== 事件绑定 ====================
function bindEvents() {
    // 模式选择
    document.querySelectorAll('.mode-card').forEach(card => {
        card.addEventListener('click', () => {
            selectMode(card.dataset.mode);
        });
    });
    
    // 保存按钮
    document.getElementById('clip-btn').addEventListener('click', handleClip);
    
    // 取消按钮
    document.getElementById('cancel-btn').addEventListener('click', () => {
        window.close();
    });
}

// ==================== 模式选择 ====================
function selectMode(mode) {
    selectedMode = mode;
    
    // 更新 UI
    document.querySelectorAll('.mode-card').forEach(card => {
        card.classList.remove('active');
        if (card.dataset.mode === mode) {
            card.classList.add('active');
        }
    });
    
    console.log('[PaperHub Clipper] Selected mode:', mode);
}

// ==================== 执行剪藏 ====================
async function handleClip() {
    if (isProcessing) return;
    
    const clipBtn = document.getElementById('clip-btn');
    const tagsInput = document.getElementById('tags-input');
    
    // 解析标签
    const tags = tagsInput.value
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);
    
    try {
        isProcessing = true;
        clipBtn.disabled = true;
        clipBtn.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; border-width: 2px; margin: 0;"></span> 处理中...';
        
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        let result;
        
        switch (selectedMode) {
            case 'full':
                result = await clipFullPage(tab.id, tags);
                break;
            case 'selection':
                result = await clipSelection(tab.id, tags);
                break;
            case 'smart':
                result = await clipSmart(tab.id, tags);
                break;
            case 'quick':
                result = await clipQuickNote(tags);
                break;
        }
        
        if (result && result.success) {
            showSuccess('✅ 保存成功！');
            setTimeout(() => window.close(), 1500);
        } else {
            showError(result?.message || '保存失败');
        }
        
    } catch (error) {
        console.error('[PaperHub Clipper] Clip failed:', error);
        showError('保存失败: ' + error.message);
    } finally {
        isProcessing = false;
        clipBtn.disabled = false;
        clipBtn.innerHTML = '<span>💾</span><span>保存到 PaperHub</span>';
    }
}

// ==================== 全文剪藏 ====================
async function clipFullPage(tabId, tags) {
    console.log('[PaperHub Clipper] Clipping full page...');
    
    try {
        // 在页面上下文中执行提取
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: () => {
                if (window.PaperHubClipper) {
                    return window.PaperHubClipper.extractFullPage();
                }
                throw new Error('PaperHub Clipper not loaded');
            }
        });
        
        const pageData = results[0]?.result;
        
        if (!pageData) {
            throw new Error('无法提取页面内容');
        }
        
        // 发送到 background script
        return await sendMessageToBackground({
            action: 'clip_full_page',
            data: {
                ...pageData,
                tags: tags,
                target_library: 'article'
            }
        });
        
    } catch (error) {
        console.error('[PaperHub Clipper] Full page clip failed:', error);
        throw error;
    }
}

// ==================== 选择剪藏 ====================
async function clipSelection(tabId, tags) {
    console.log('[PaperHub Clipper] Clipping selection...');
    
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: () => {
                if (window.PaperHubClipper) {
                    return {
                        selectedText: window.PaperHubClipper.getSelectedText(),
                        title: document.title,
                        url: window.location.href
                    };
                }
                return { selectedText: '', title: '', url: '' };
            }
        });
        
        const { selectedText, title, url } = results[0]?.result || {};
        
        if (!selectedText) {
            throw new Error('请先在页面上选中要剪藏的内容');
        }
        
        return await sendMessageToBackground({
            action: 'clip_selection',
            data: {
                title: `剪藏：${title.substring(0, 50)}`,
                content: selectedText,
                source_url: url,
                source_title: title,
                tags: tags,
                target_library: 'note'
            }
        });
        
    } catch (error) {
        console.error('[PaperHub Clipper] Selection clip failed:', error);
        throw error;
    }
}

// ==================== 智能剪藏（TODO）====================
async function clipSmart(tabId, tags) {
    console.log('[PaperHub Clipper] Smart clipping (TODO)...');
    
    // 先提取全文
    const fullPageResult = await clipFullPage(tabId, tags);
    
    // TODO: 调用后端 AI 接口进行智能提取
    // 目前暂时返回全文剪藏结果
    
    return fullPageResult;
}

// ==================== 速记笔记（TODO）====================
async function clipQuickNote(tags) {
    console.log('[PaperHub Clipper] Quick note (TODO)...');
    
    // TODO: 打开一个快速编辑器
    // 目前提示用户先实现
    
    return {
        success: false,
        message: '速记笔记功能开发中，敬请期待'
    };
}

// ==================== 消息通信 ====================
function sendMessageToBackground(message) {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(message, (response) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
            } else {
                resolve(response);
            }
        });
    });
}

// ==================== UI 辅助函数 ====================
function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    const successEl = document.getElementById('success-message');
    successEl.textContent = message;
    successEl.style.display = 'block';
    
    document.getElementById('error-message').style.display = 'none';
}
