// PaperHub 工具函数模块

// 显示作者
export function displayAuthors(authorsStr) {
    if (!authorsStr) return '';
    try {
        const authors = JSON.parse(authorsStr);
        return authors.slice(0, 5).join(', ') + (authors.length > 5 ? ' 等' : '');
    } catch (e) {
        return authorsStr;
    }
}

// 状态文本
export function statusText(status) {
    const map = { pending: '待读', reading: '在读', done: '已读', mastered: '精读' };
    return map[status] || status;
}

// 状态类型
export function statusType(status) {
    const map = { pending: 'info', reading: 'warning', done: 'success', mastered: 'danger' };
    return map[status] || 'info';
}

// 获取当前时间字符串（用于表单）
export function getCurrentDateTime() {
    return new Date().toISOString().slice(0, 16);
}

// 从内容提取标题
export function extractTitleFromContent(content) {
    if (!content.trim()) return '';
    const firstLine = content.trim().split('\n')[0];
    return firstLine.replace(/^#+\s*/, '').replace(/\s+#+\s*$/, '').trim();
}

// 验证年份
export function validateYear(year) {
    const y = parseInt(year);
    return !isNaN(y) && y >= 2000 && y <= 2100;
}

// 验证月份
export function validateMonth(month) {
    const m = parseInt(month);
    return !isNaN(m) && m >= 1 && m <= 12;
}
