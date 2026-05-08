// 文章库独立模块
// 可独立测试，无副作用
// 封装所有文章库相关的 state 和 logic

export function createArticleModule({ Vue, ElementPlus, axios }) {
    const { ref, computed } = Vue;

    // ============== State ==============
    const allArticles = ref([]);
    const viewingArticle = ref(null);
    const articleFilterType = ref(null);
    const articleSearchKeyword = ref('');
    const articleSortBy = ref('created_at');
    const articleSelectedTagIds = ref([]);
    const articleTagInput = ref('');
    const articleSelectedStatus = ref(null);
    const articleAllTags = ref([]);
    const linkingArticleId = ref(null);

    const articleStatusFilters = ref([
        { icon: '📚', label: '全部', value: null },
        { icon: '⏳', label: '待读', value: 'pending' },
        { icon: '📖', label: '在读', value: 'reading' },
        { icon: '✅', label: '已读', value: 'done' },
        { icon: '🔥', label: '精读', value: 'mastered' }
    ]);

    // ============== Computed ==============
    function getArticleStatusCount(status) {
        if (status === null) return allArticles.value.length;
        return allArticles.value.filter(a => a.status === status).length;
    }

    const getFilteredArticles = Vue.computed(() => {
        let result = [...allArticles.value];

        if (articleFilterType.value) {
            result = result.filter(a => a.source === articleFilterType.value);
        }

        if (articleSelectedStatus.value) {
            result = result.filter(a => a.status === articleSelectedStatus.value);
        }

        if (articleSelectedTagIds.value.length > 0) {
            result = result.filter(a => {
                const articleTagIds = (a.tags || []).map(t => t.id);
                return articleSelectedTagIds.value.every(id => articleTagIds.includes(id));
            });
        }

        const kw = articleSearchKeyword.value.toLowerCase().trim();
        if (kw) {
            result = result.filter(a =>
                (a.title || '').toLowerCase().includes(kw) ||
                (a.author || '').toLowerCase().includes(kw) ||
                (a.content || '').toLowerCase().includes(kw)
            );
        }

        const sortField = articleSortBy.value;
        result.sort((a, b) => {
            if (sortField === 'title') {
                return (a.title || '').localeCompare(b.title || '');
            }
            return new Date(b[sortField] || 0) - new Date(a[sortField] || 0);
        });

        return result;
    });

    // ============== Methods ==============
    async function loadAllArticles() {
        try {
            const res = await axios.get('/api/articles');
            console.log('[ArticleModule] API returned:', res.data.articles?.length, 'articles');
            allArticles.value = (res.data.articles || []).map(a => ({
                ...a,
                starred: Boolean(a.starred)
            }));
            console.log('[ArticleModule] allArticles.value set to:', allArticles.value.length);
            await loadArticleTags();
        } catch (e) {
            console.error('加载文章列表失败:', e);
        }
    }

    async function loadArticleTags() {
        try {
            const res = await axios.get('/api/tags/articles');
            const tagCounts = {};
            allArticles.value.forEach(a => {
                (a.tags || []).forEach(t => {
                    tagCounts[t.id] = (tagCounts[t.id] || 0) + 1;
                });
            });
            articleAllTags.value = (res.data.tags || []).map(t => ({
                ...t,
                article_count: tagCounts[t.id] || 0
            })).filter(t => t.article_count > 0);
        } catch (e) {
            console.error('加载文章标签失败:', e);
        }
    }

    function toggleArticleStatusFilter(status) {
        articleSelectedStatus.value = articleSelectedStatus.value === status ? null : status;
    }

    function articleToggleTagFilter(tagId) {
        const idx = articleSelectedTagIds.value.indexOf(tagId);
        if (idx > -1) {
            articleSelectedTagIds.value.splice(idx, 1);
        } else {
            articleSelectedTagIds.value.push(tagId);
        }
    }

    function clearArticleFilters() {
        articleSelectedStatus.value = null;
        articleSelectedTagIds.value = [];
    }

    function getArticlePreviewUrl(article) {
        if (!article || !article.file_path) return '';
        if (article.file_path.startsWith('http')) return article.file_path;
        if (article.source === 'wechat') {
            const parts = article.file_path.split('/');
            const filename = parts[parts.length - 1];
            return '/articles/wechat/' + filename;
        }
        if (article.source === 'zhihu') {
            const parts = article.file_path.split('/');
            const filename = parts[parts.length - 1];
            return '/articles/zhihu/' + filename;
        }
        return article.file_path;
    }

    function formatAuthor(authorStr) {
        if (!authorStr) return '';
        try {
            const parsed = JSON.parse(authorStr);
            if (Array.isArray(parsed)) return parsed.join(', ');
            return parsed;
        } catch (e) {
            return authorStr;
        }
    }

    async function viewArticleDetail(article) {
        try {
            const res = await axios.get('/api/articles/' + article.id);
            viewingArticle.value = res.data.article;

            let status = viewingArticle.value.status;
            if (status === 'pending') {
                status = 'reading';
                await updateArticleStatus(article.id, 'reading');
            }
        } catch (e) {
            ElementPlus.ElMessage.error('加载文章详情失败');
        }
    }

    async function toggleArticleStar(article) {
        try {
            article.starred = !article.starred;
            await axios.put(`/api/articles/${article.id}`, {
                starred: article.starred
            });
            if (viewingArticle.value && viewingArticle.value.id === article.id) {
                viewingArticle.value.starred = article.starred;
            }
            ElementPlus.ElMessage.success(article.starred ? '⭐ 已标星' : '已取消标星');
        } catch (e) {
            article.starred = !article.starred;
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    async function updateArticleStatus(articleId, status) {
        try {
            await axios.put(`/api/articles/${articleId}`, { status });
            const idx = allArticles.value.findIndex(a => a.id === articleId);
            if (idx > -1) {
                allArticles.value[idx].status = status;
            }
            if (viewingArticle.value && viewingArticle.value.id === articleId) {
                viewingArticle.value.status = status;
            }
        } catch (e) {
            ElementPlus.ElMessage.error('更新状态失败');
        }
    }

    async function addTagToArticle(article) {
        const name = articleTagInput.value.trim();
        if (!name) return;
        try {
            await axios.post(`/api/articles/${article.id}/tags`, { name });
            articleTagInput.value = '';
            ElementPlus.ElMessage.success('标签已添加');
            const res = await axios.get(`/api/articles/${article.id}`);
            viewingArticle.value = res.data.article;
            loadAllArticles();
        } catch (e) {
            ElementPlus.ElMessage.error('添加标签失败');
        }
    }

    async function addArticleTagInList(article) {
        const name = article.newTagInput?.trim();
        if (!name) return;
        try {
            await axios.post(`/api/articles/${article.id}/tags`, { name });
            article.newTagInput = '';
            ElementPlus.ElMessage.success('标签已添加');
            const res = await axios.get(`/api/articles/${article.id}`);
            const idx = allArticles.value.findIndex(a => a.id === article.id);
            if (idx > -1) {
                allArticles.value[idx] = res.data.article;
            }
            loadArticleTags();
        } catch (e) {
            ElementPlus.ElMessage.error('添加标签失败');
        }
    }

    async function removeTagFromArticle(article, tagId) {
        try {
            await axios.delete(`/api/articles/${article.id}/tags/${tagId}`);
            ElementPlus.ElMessage.success('标签已移除');
            const res = await axios.get(`/api/articles/${article.id}`);
            const idx = allArticles.value.findIndex(a => a.id === article.id);
            if (idx > -1) {
                allArticles.value[idx] = res.data.article;
            }
            if (viewingArticle.value && viewingArticle.value.id === article.id) {
                viewingArticle.value = res.data.article;
            }
            loadArticleTags();
        } catch (e) {
            ElementPlus.ElMessage.error('移除标签失败');
        }
    }

    async function deleteArticle(articleId) {
        try {
            await ElementPlus.ElMessageBox.confirm('确定要删除这篇文章吗？', '确认', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            });
            await axios.delete(`/api/articles/${articleId}`);
            allArticles.value = allArticles.value.filter(a => a.id !== articleId);
            ElementPlus.ElMessage.success('文章已删除');
        } catch (e) {
            if (e !== 'cancel') {
                ElementPlus.ElMessage.error('删除失败');
            }
        }
    }

    function showLinkPaperDialog(articleId) {
        linkingArticleId.value = articleId;
    }

    async function linkPaperToArticle(paperId) {
        try {
            await axios.post(`/api/articles/${linkingArticleId.value}/papers/${paperId}`);
            ElementPlus.ElMessage.success('关联成功');
            const res = await axios.get(`/api/articles/${linkingArticleId.value}`);
            viewingArticle.value = res.data.article;
            linkingArticleId.value = null;
            loadAllArticles();
        } catch (e) {
            ElementPlus.ElMessage.error('关联失败');
        }
    }

    async function unlinkPaperArticle(paperId, articleId) {
        try {
            await axios.delete(`/api/articles/${articleId}/papers/${paperId}`);
            ElementPlus.ElMessage.success('已取消关联');
            const res = await axios.get(`/api/articles/${articleId}`);
            viewingArticle.value = res.data.article;
            loadAllArticles();
        } catch (e) {
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    // ============== Exports ==============
    return {
        // State
        allArticles, viewingArticle,
        articleFilterType, articleSearchKeyword, articleSortBy,
        articleSelectedTagIds, articleTagInput,
        articleSelectedStatus, articleAllTags, articleStatusFilters,
        linkingArticleId,

        // Computed / Helpers
        getArticleStatusCount, getFilteredArticles,
        getArticlePreviewUrl, formatAuthor,

        // Methods
        loadAllArticles, loadArticleTags,
        toggleArticleStatusFilter, articleToggleTagFilter, clearArticleFilters,
        viewArticleDetail, toggleArticleStar, updateArticleStatus,
        addTagToArticle, addArticleTagInList, removeTagFromArticle,
        deleteArticle, showLinkPaperDialog, linkPaperToArticle, unlinkPaperArticle
    };
}
