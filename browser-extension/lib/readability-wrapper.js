/**
 * Readability Wrapper for Browser Extension
 * 确保 Readability 在浏览器全局环境中可用
 */

// 如果 Readability 已经定义（通过 module.exports），将其暴露到全局
if (typeof module !== 'undefined' && module.exports && typeof window.Readability === 'undefined') {
    window.Readability = module.exports;
}

// 如果仍然没有 Readability，尝试从其他常见位置获取
if (typeof window.Readability === 'undefined') {
    console.warn('[Readability Wrapper] Readability not available globally');
} else {
    console.log('[Readability Wrapper] Readability successfully exposed to global scope');
}
