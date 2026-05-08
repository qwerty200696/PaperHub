// PaperHub API 模块
// 使用 CDN 全局 axios

// 论文相关 API
export const PaperAPI = {
    getPapers(params = {}) {
        return axios.get('/api/papers', { params });
    },
    getPaper(id) {
        return axios.get(`/api/papers/${id}`);
    },
    updatePaper(id, data) {
        return axios.put(`/api/papers/${id}`, data);
    },
    deletePaper(id) {
        return axios.delete(`/api/papers/${id}`);
    },
    downloadUrl(id) {
        return `/api/papers/${id}/download`;
    },
    getTags() {
        return axios.get('/api/tags');
    },
    addTag(paperId, tagName) {
        return axios.post(`/api/papers/${paperId}/tags`, { name: tagName });
    },
    removeTag(paperId, tagId) {
        return axios.delete(`/api/papers/${paperId}/tags/${tagId}`);
    },
    updateStatus(id, status) {
        return axios.put(`/api/papers/${id}`, { status });
    },
    toggleStar(id, starred) {
        return axios.put(`/api/papers/${id}`, { starred });
    }
};

// 入库相关 API
export const IngestAPI = {
    arxiv(input) {
        return axios.post('/api/ingest/arxiv', { input });
    },
    ingestArxiv(input) {
        return axios.post('/api/ingest/arxiv', { input });
    },
    wechat(url, extractContentOnly = false) {
        return axios.post('/api/ingest/wechat', { url, extract_content_only: extractContentOnly });
    },
    ingestWechat(url, extractContentOnly = false) {
        return axios.post('/api/ingest/wechat', { url, extract_content_only: extractContentOnly });
    },
    note(data) {
        return axios.post('/api/ingest/note', data);
    },
    ingestNote(data) {
        return axios.post('/api/ingest/note', data);
    },
    zhihu(data) {
        return axios.post('/api/ingest/zhihu', data);
    },
    ingestZhihu(data) {
        return axios.post('/api/ingest/zhihu', data);
    },
    pdfUploadUrl() {
        return '/api/ingest/pdf';
    }
};
