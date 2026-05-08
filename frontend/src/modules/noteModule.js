// 笔记库独立模块
// 可独立测试，无副作用
// 封装所有笔记库相关的 state 和 logic

export function createNoteModule({ Vue, ElementPlus, axios }) {
    const { ref, computed } = Vue;

    // ============== State ==============
    const allNotes = ref([]);
    const viewingNote = ref(null);
    const noteFilterType = ref(null);
    const noteSearchKeyword = ref('');
    const noteSortBy = ref('created_at');
    const noteSelectedTagIds = ref([]);
    const noteTagInput = ref('');
    const noteSelectedStatus = ref(null);
    const noteAllTags = ref([]);
    const linkingPaperId = ref(null);
    const linkingArticleId = ref(null);

    const noteStatusFilters = ref([
        { icon: '📚', label: '全部', value: null },
        { icon: '⏳', label: '待读', value: 'pending' },
        { icon: '📖', label: '在读', value: 'reading' },
        { icon: '✅', label: '已读', value: 'done' },
        { icon: '🔥', label: '精读', value: 'mastered' }
    ]);

    const noteSources = ref([
        { label: '📝 自由笔记', value: 'manual' },
        { label: '📚 论文笔记', value: 'paper' }
    ]);

    const noteTypeFilters = ref([
        { icon: '📝', label: '全部', value: null },
        { icon: '✏️', label: '自由笔记', value: 'manual' },
        { icon: '📚', label: '论文笔记', value: 'paper' }
    ]);

    // ============== Computed ==============
    function getNoteStatusCount(status) {
        if (status === null) return allNotes.value.length;
        return allNotes.value.filter(n => n.status === status).length;
    }

    const getFilteredNotes = Vue.computed(() => {
        let result = [...allNotes.value];

        if (noteFilterType.value) {
            result = result.filter(n => n.source === noteFilterType.value);
        }

        if (noteSelectedStatus.value) {
            result = result.filter(n => n.status === noteSelectedStatus.value);
        }

        if (noteSelectedTagIds.value.length > 0) {
            result = result.filter(n => {
                const noteTagIds = (n.tags || []).map(t => t.id);
                return noteSelectedTagIds.value.every(id => noteTagIds.includes(id));
            });
        }

        const kw = noteSearchKeyword.value.toLowerCase().trim();
        if (kw) {
            result = result.filter(n =>
                (n.title || '').toLowerCase().includes(kw) ||
                (n.content || '').toLowerCase().includes(kw)
            );
        }

        const sortField = noteSortBy.value;
        result.sort((a, b) => {
            const aStar = a.starred ? 0 : 1;
            const bStar = b.starred ? 0 : 1;
            if (aStar !== bStar) return aStar - bStar;

            const statusOrder = { pending: 0, reading: 1, done: 2, mastered: 3 };
            const aStatus = statusOrder[a.status] || 9;
            const bStatus = statusOrder[b.status] || 9;
            if (aStatus !== bStatus) return aStatus - bStatus;

            return new Date(b[sortField] || 0) - new Date(a[sortField] || 0);
        });

        return result;
    });

    function noteSourceText(source) {
        const map = { manual: '📝 自由笔记', paper: '📚 论文笔记', doubao: '🤖 豆包', chatgpt: '🤖 ChatGPT' };
        return map[source] || source;
    }

    // ============== Methods ==============
    async function loadAllNotes() {
        try {
            const res = await axios.get('/api/notes?per_page=500');
            allNotes.value = (res.data.notes || []).map(n => ({
                ...n,
                starred: Boolean(n.starred)
            }));
            await loadNoteTags();
        } catch (e) {
            console.error('加载笔记列表失败:', e);
        }
    }

    async function loadNoteTags() {
        try {
            const res = await axios.get('/api/tags/notes');
            const tagCounts = {};
            allNotes.value.forEach(n => {
                (n.tags || []).forEach(t => {
                    tagCounts[t.id] = (tagCounts[t.id] || 0) + 1;
                });
            });
            noteAllTags.value = (res.data.tags || []).map(t => ({
                ...t,
                note_count: tagCounts[t.id] || 0
            })).filter(t => t.note_count > 0);
        } catch (e) {
            console.error('加载笔记标签失败:', e);
        }
    }

    function toggleNoteStatusFilter(status) {
        noteSelectedStatus.value = noteSelectedStatus.value === status ? null : status;
    }

    function noteToggleTagFilter(tagId) {
        const idx = noteSelectedTagIds.value.indexOf(tagId);
        if (idx > -1) {
            noteSelectedTagIds.value.splice(idx, 1);
        } else {
            noteSelectedTagIds.value.push(tagId);
        }
    }

    function clearNoteFilters() {
        noteSelectedStatus.value = null;
        noteSelectedTagIds.value = [];
    }

    async function viewNoteDetail(note) {
        try {
            const res = await axios.get('/api/notes/' + note.id);
            viewingNote.value = res.data.note;

            let status = viewingNote.value.status;
            if (status === 'pending') {
                status = 'reading';
                await updateNoteStatus(note.id, 'reading');
            }
        } catch (e) {
            ElementPlus.ElMessage.error('加载笔记详情失败');
        }
    }

    async function toggleNoteStar(note) {
        try {
            note.starred = !note.starred;
            await axios.put(`/api/notes/${note.id}`, {
                starred: note.starred
            });
            if (viewingNote.value && viewingNote.value.id === note.id) {
                viewingNote.value.starred = note.starred;
            }
            ElementPlus.ElMessage.success(note.starred ? '⭐ 已标星' : '已取消标星');
        } catch (e) {
            note.starred = !note.starred;
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    async function updateNoteStatus(noteId, status) {
        try {
            await axios.put(`/api/notes/${noteId}`, { status });
            const idx = allNotes.value.findIndex(n => n.id === noteId);
            if (idx > -1) {
                allNotes.value[idx].status = status;
            }
            if (viewingNote.value && viewingNote.value.id === noteId) {
                viewingNote.value.status = status;
            }
        } catch (e) {
            ElementPlus.ElMessage.error('更新状态失败');
        }
    }

    async function addNoteTag(note, name) {
        if (!name) return;
        try {
            await axios.post(`/api/notes/${note.id}/tags`, { name });
            ElementPlus.ElMessage.success('标签已添加');
            const res = await axios.get(`/api/notes/${note.id}`);
            const idx = allNotes.value.findIndex(n => n.id === note.id);
            if (idx > -1) {
                allNotes.value[idx] = res.data.note;
            }
            if (viewingNote.value && viewingNote.value.id === note.id) {
                viewingNote.value = res.data.note;
            }
            loadNoteTags();
        } catch (e) {
            ElementPlus.ElMessage.error('添加标签失败');
        }
    }

    async function removeNoteTag(note, tagId) {
        try {
            await axios.delete(`/api/notes/${note.id}/tags/${tagId}`);
            ElementPlus.ElMessage.success('标签已移除');
            const res = await axios.get(`/api/notes/${note.id}`);
            const idx = allNotes.value.findIndex(n => n.id === note.id);
            if (idx > -1) {
                allNotes.value[idx] = res.data.note;
            }
            if (viewingNote.value && viewingNote.value.id === note.id) {
                viewingNote.value = res.data.note;
            }
            loadNoteTags();
        } catch (e) {
            ElementPlus.ElMessage.error('移除标签失败');
        }
    }

    async function syncRelatedTags(note) {
        try {
            await axios.post(`/api/notes/${note.id}/sync-tags`);
            ElementPlus.ElMessage.success('✅ 已同步关联论文/文章的标签');
            const res = await axios.get(`/api/notes/${note.id}`);
            if (viewingNote.value && viewingNote.value.id === note.id) {
                viewingNote.value = res.data.note;
            }
            loadNoteTags();
        } catch (e) {
            ElementPlus.ElMessage.error('同步失败');
        }
    }

    function renderMarkdown(content) {
        if (!content) return '';
        if (typeof marked === 'undefined') {
            return content.replace(/\n/g, '<br>');
        }
        return marked.parse(content);
    }

    async function deleteNote(noteId) {
        try {
            await ElementPlus.ElMessageBox.confirm('确定要删除这条笔记吗？', '确认', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            });
            await axios.delete(`/api/notes/${noteId}`);
            allNotes.value = allNotes.value.filter(n => n.id !== noteId);
            viewingNote.value = null;
            ElementPlus.ElMessage.success('笔记已删除');
        } catch (e) {
            if (e !== 'cancel') {
                ElementPlus.ElMessage.error('删除失败');
            }
        }
    }

    function showLinkPaperDialog(noteId) {
        linkingPaperId.value = noteId;
    }

    async function linkNoteToPaper(paperId) {
        try {
            await axios.post(`/api/notes/${linkingPaperId.value}/papers/${paperId}`);
            ElementPlus.ElMessage.success('关联成功');
            const res = await axios.get(`/api/notes/${linkingPaperId.value}`);
            viewingNote.value = res.data.note;
            linkingPaperId.value = null;
            loadAllNotes();
        } catch (e) {
            ElementPlus.ElMessage.error('关联失败');
        }
    }

    async function unlinkNotePaper(noteId, paperId) {
        try {
            await axios.delete(`/api/notes/${noteId}/papers/${paperId}`);
            ElementPlus.ElMessage.success('已取消关联');
            const res = await axios.get(`/api/notes/${noteId}`);
            viewingNote.value = res.data.note;
            loadAllNotes();
        } catch (e) {
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    function showLinkArticleDialog(noteId) {
        linkingArticleId.value = noteId;
    }

    async function linkNoteToArticle(articleId) {
        try {
            await axios.post(`/api/notes/${linkingArticleId.value}/articles`, { article_id: articleId });
            ElementPlus.ElMessage.success('关联成功');
            const res = await axios.get(`/api/notes/${linkingArticleId.value}`);
            viewingNote.value = res.data.note;
            linkingArticleId.value = null;
            loadAllNotes();
        } catch (e) {
            ElementPlus.ElMessage.error('关联失败');
        }
    }

    async function unlinkNoteArticle(noteId, articleId) {
        try {
            await axios.delete(`/api/notes/${noteId}/articles/${articleId}`);
            ElementPlus.ElMessage.success('已取消关联');
            const res = await axios.get(`/api/notes/${noteId}`);
            viewingNote.value = res.data.note;
            loadAllNotes();
        } catch (e) {
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    // ============== Exports ==============
    return {
        // State
        allNotes, viewingNote,
        noteFilterType, noteSearchKeyword, noteSortBy,
        noteSelectedTagIds, noteTagInput,
        noteSelectedStatus, noteAllTags, noteStatusFilters,
        noteSources, noteTypeFilters,
        linkingPaperId, linkingArticleId,

        // Computed / Helpers
        getNoteStatusCount, getFilteredNotes,
        noteSourceText, renderMarkdown,

        // Methods
        loadAllNotes, loadNoteTags,
        toggleNoteStatusFilter, noteToggleTagFilter, clearNoteFilters,
        viewNoteDetail, toggleNoteStar, updateNoteStatus,
        addNoteTag, removeNoteTag, syncRelatedTags,
        deleteNote, showLinkPaperDialog, linkNoteToPaper, unlinkNotePaper,
        showLinkArticleDialog, linkNoteToArticle, unlinkNoteArticle
    };
}
