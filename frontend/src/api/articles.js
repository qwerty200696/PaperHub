import axios from './axios.js';


export const ArticleAPI = {
    list(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return axios.get(`/api/articles${queryString ? '?' + queryString : ''}`);
    },

    get(id) {
        return axios.get(`/api/articles/${id}`);
    },

    create(data) {
        return axios.post('/api/articles', data);
    },

    update(id, data) {
        return axios.put(`/api/articles/${id}`, data);
    },

    delete(id) {
        return axios.delete(`/api/articles/${id}`);
    },

    linkPaper(articleId, paperId) {
        return axios.post(`/api/articles/${articleId}/papers`, { paper_id: paperId });
    },

    unlinkPaper(articleId, paperId) {
        return axios.delete(`/api/articles/${articleId}/papers/${paperId}`);
    }
};
