/**
 * PaperHub Clipper - Background Service Worker
 * 负责消息路由、与后端 API 通信
 */

// 默认 PaperHub 后端地址
const DEFAULT_PAPERHUB_API = 'http://localhost:5000';

// 获取配置的 API 地址
async function getApiBaseUrl() {
    try {
        const result = await chrome.storage.local.get(['apiConfig']);
        return result.apiConfig?.baseUrl || DEFAULT_PAPERHUB_API;
    } catch (error) {
        console.error('[PaperHub Clipper] Failed to get API config:', error);
        return DEFAULT_PAPERHUB_API;
    }
}

// ==================== 消息监听 ====================
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[PaperHub Clipper] Received message:', request.action);
    
    switch (request.action) {
        case 'clip_full_page':
            handleClipFullPage(request.data)
                .then(sendResponse)
                .catch(error => sendResponse({ success: false, message: error.message }));
            return true; // 保持消息通道开放
            
        case 'clip_selection':
            handleClipSelection(request.data)
                .then(sendResponse)
                .catch(error => sendResponse({ success: false, message: error.message }));
            return true;
            
        case 'test_connection':
            testConnection()
                .then(sendResponse)
                .catch(error => sendResponse({ success: false, message: error.message }));
            return true;
            
        default:
            sendResponse({ success: false, message: 'Unknown action' });
    }
});

// ==================== 全文剪藏处理 ====================
async function handleClipFullPage(data) {
    try {
        console.log('[PaperHub Clipper] Processing full page clip...');
        
        const baseUrl = await getApiBaseUrl();
        
        // 调用后端 API
        const response = await fetch(`${baseUrl}/api/ingest/browser_clipper`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'article',
                title: data.title,
                url: data.url,
                author: data.author,
                published_date: data.published_date,
                content: data.content,
                text_content: data.text_content,
                description: data.description,
                images: data.images,
                tags: data.tags || [],
                source: 'browser_clipper'
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '保存失败');
        }
        
        const result = await response.json();
        console.log('[PaperHub Clipper] Full page saved successfully:', result);
        
        return {
            success: true,
            message: '全文剪藏成功',
            data: result
        };
        
    } catch (error) {
        console.error('[PaperHub Clipper] Full page clip failed:', error);
        throw error;
    }
}

// ==================== 选择剪藏处理 ====================
async function handleClipSelection(data) {
    try {
        console.log('[PaperHub Clipper] Processing selection clip...');
        
        const baseUrl = await getApiBaseUrl();
        const targetLibrary = data.target_library || 'note';
        
        let apiUrl, payload;
        
        if (targetLibrary === 'note') {
            // 保存到笔记库
            apiUrl = `${baseUrl}/api/notes`;
            payload = {
                title: data.title,
                content: data.content,
                source_url: data.source_url,
                source_title: data.source_title,
                tags: data.tags || [],
                source: 'browser_clipper'
            };
        } else {
            // 保存到文章库
            apiUrl = `${baseUrl}/api/articles`;
            payload = {
                title: data.title,
                content: data.content,
                original_url: data.source_url,
                author: data.author,
                published_date: data.published_date,
                tags: data.tags || [],
                source: 'browser_clipper'
            };
        }
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '保存失败');
        }
        
        const result = await response.json();
        console.log('[PaperHub Clipper] Selection saved successfully:', result);
        
        return {
            success: true,
            message: '选择剪藏成功',
            data: result
        };
        
    } catch (error) {
        console.error('[PaperHub Clipper] Selection clip failed:', error);
        throw error;
    }
}

// ==================== 测试连接 ====================
async function testConnection() {
    try {
        const baseUrl = await getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/papers?page=1&per_page=1`);
        
        if (!response.ok) {
            throw new Error('无法连接到 PaperHub 后端');
        }
        
        return {
            success: true,
            message: '连接成功'
        };
        
    } catch (error) {
        console.error('[PaperHub Clipper] Connection test failed:', error);
        throw error;
    }
}

// ==================== 插件安装/更新事件 ====================
chrome.runtime.onInstalled.addListener((details) => {
    console.log('[PaperHub Clipper] Extension installed/updated:', details.reason);
    
    if (details.reason === 'install') {
        // 首次安装，可以打开欢迎页面
        chrome.tabs.create({
            url: 'https://github.com/your-repo/paperhub#browser-extension'
        });
    }
});

// ==================== 日志记录 ====================
console.log('[PaperHub Clipper] Background service worker initialized');
