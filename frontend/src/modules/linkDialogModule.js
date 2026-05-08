/**
 * 关联对话框模块
 * 统一处理 paper/article/note 之间的关联逻辑
 */

export function createLinkDialogModule({ Vue, ElementPlus, axios }) {
    const { ref } = Vue

    // 关联论文对话框（用于笔记和文章）
    const linkPaperDialogVisible = ref(false)
    const linkPaperSearchKeyword = ref('')
    const searchablePapers = ref([])
    const linkingNoteId = ref(null)
    const linkingArticleId = ref(null)

    /**
     * 显示关联论文对话框
     */
    async function showLinkPaperDialog({ noteId, articleId, viewingNote, allPapers }) {
        if (noteId) linkingNoteId.value = noteId
        if (articleId) linkingArticleId.value = articleId
        linkPaperSearchKeyword.value = ''
        searchablePapers.value = []

        try {
            const res = await axios.get('/api/papers?per_page=500')
            const all = res.data.papers || []
            let linkedIds = []

            if (viewingNote && viewingNote.value && viewingNote.value.papers) {
                linkedIds = viewingNote.value.papers.map(p => p.id)
            }

            searchablePapers.value = all.filter(p => !linkedIds.includes(p.id))
            linkPaperDialogVisible.value = true
        } catch (e) {
            console.error('加载论文列表失败:', e)
            searchablePapers.value = []
            linkPaperDialogVisible.value = true
        }
    }

    /**
     * 搜索论文用于关联
     */
    async function searchPapersForLink() {
        if (!linkPaperSearchKeyword.value.trim()) {
            ElementPlus.ElMessage.warning('请输入搜索关键词')
            return
        }
        try {
            const res = await axios.get(
                '/api/papers?search=' + encodeURIComponent(linkPaperSearchKeyword.value) + '&per_page=50'
            )
            searchablePapers.value = res.data.papers || []
        } catch (e) {
            console.error('搜索论文失败:', e)
        }
    }

    /**
     * 关联论文到笔记
     */
    async function linkNoteToPaper(paperId, { viewingNote, loadAllNotes }) {
        if (!linkingNoteId.value) return
        try {
            await axios.post(
                `/api/notes/${linkingNoteId.value}/papers`,
                { paper_id: paperId }
            )
            ElementPlus.ElMessage.success('关联成功')
            const res = await axios.get(`/api/notes/${linkingNoteId.value}`)
            if (viewingNote) viewingNote.value = res.data.note
            if (loadAllNotes) await loadAllNotes()
            linkPaperDialogVisible.value = false
        } catch (e) {
            ElementPlus.ElMessage.error('关联失败')
        }
    }

    /**
     * 关联论文到文章
     */
    async function linkPaperToArticle(paperId, { viewingArticle, allArticles, loadAllArticles }) {
        try {
            await axios.post(
                `/api/articles/${linkingArticleId.value}/papers`,
                { paper_id: paperId }
            )
            ElementPlus.ElMessage.success('关联成功')
            linkPaperDialogVisible.value = false
            const article = allArticles.find(a => a.id === linkingArticleId.value)
            if (article && loadAllArticles) {
                await loadAllArticles()
            }
            if (viewingArticle) {
                const res = await axios.get(`/api/articles/${viewingArticle.value.id}`)
                viewingArticle.value = res.data.article
            }
        } catch (e) {
            ElementPlus.ElMessage.error('关联失败')
        }
    }

    /**
     * 取消论文和笔记的关联
     */
    async function unlinkNotePaper(noteId, paperId, { viewingNote, loadAllNotes }) {
        try {
            await axios.delete(`/api/notes/${noteId}/papers/${paperId}`)
            ElementPlus.ElMessage.success('已取消关联')
            const res = await axios.get(`/api/notes/${noteId}`)
            if (viewingNote) viewingNote.value = res.data.note
            if (loadAllNotes) await loadAllNotes()
        } catch (e) {
            ElementPlus.ElMessage.error('取消关联失败')
        }
    }

    /**
     * 取消论文和文章的关联
     */
    async function unlinkPaperFromArticle(articleId, paperId, { viewingArticle, allArticles, loadAllArticles }) {
        try {
            await axios.delete(`/api/articles/${articleId}/papers/${paperId}`)
            ElementPlus.ElMessage.success('取消关联成功')
            if (viewingArticle) {
                const res = await axios.get(`/api/articles/${articleId}`)
                const idx = allArticles.findIndex(a => a.id === articleId)
                if (idx !== -1) {
                    allArticles[idx] = res.data.article
                }
                if (viewingArticle.value && viewingArticle.value.id === articleId) {
                    viewingArticle.value = res.data.article
                }
            }
            if (loadAllArticles) await loadAllArticles()
        } catch (e) {
            ElementPlus.ElMessage.error('取消关联失败')
        }
    }

    return {
        linkPaperDialogVisible,
        linkPaperSearchKeyword,
        searchablePapers,
        linkingNoteId,
        linkingArticleId,
        showLinkPaperDialog,
        searchPapersForLink,
        linkNoteToPaper,
        linkPaperToArticle,
        unlinkNotePaper,
        unlinkPaperFromArticle
    }
}

