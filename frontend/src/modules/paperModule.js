// 论文库独立自治模块
// 与笔记库 articleModule 100% 同构设计
// 可独立测试，无副作用
// 封装所有论文库相关的 state 和 logic

export function createPaperModule({ Vue, ElementPlus, axios, FilterUtils, SortUtils }) {
    const { ref } = Vue;

    // ============== State ==============
    const allPapers = ref([]);
    const selectedPaper = ref(null);
    const searchKeyword = ref('');
    const sortBy = ref(localStorage.getItem('paper_sort_by') || 'created_at');
    const selectedTagIds = ref([]);
    const selectedStatus = ref(null);
    const selectedSource = ref(null);
    const allTags = ref([]);
    const total = ref(0);

    // arXiv 搜索相关状态
    const arxivSearchVisible = ref(false);
    const arxivKeywords = ref('');
    const arxivCategories = ref([]);
    const arxivMaxResults = ref(20);
    const arxivStartDate = ref('');
    const arxivEndDate = ref('');
    const arxivSearchResults = ref([]);
    const arxivAllCategories = ref({});
    const arxivGroupedCategories = ref({});
    const selectedArxivPapers = ref([]);
    const arxivSearchLoading = ref(false);

    const statusFilters = ref([
        { icon: '📚', label: '全部', value: null },
        { icon: '⏳', label: '待读', value: 'pending' },
        { icon: '📖', label: '在读', value: 'reading' },
        { icon: '✅', label: '已读', value: 'done' },
        { icon: '🔥', label: '精读', value: 'mastered' }
    ]);

    const sourceFilters = ref([
        { label: '📄 arXiv', value: 'arxiv' },
        { label: '📁 本地PDF', value: 'pdf' }
    ]);

    // ============== Computed ==============
    function getStatusCount(status) {
        return FilterUtils.getStatusCount(getFilteredPapers.value, status);
    }

    function getSourceCount(source) {
        return FilterUtils.getSourceCount(getFilteredPapers.value, source);
    }

    function getTagCount(tagId) {
        return FilterUtils.getTagCount(getFilteredPapers.value, tagId);
    }

    // 计算属性
    const getFilteredPapers = Vue.computed(() => {
        if (!FilterUtils || !SortUtils) return allPapers.value || [];
        let papers = [...allPapers.value];
        papers = FilterUtils.applyAllFilters(papers, {
            keyword: searchKeyword.value,
            selectedStatus: selectedStatus.value,
            selectedTagIds: selectedTagIds.value,
            keywordFields: ['title', 'author']
        });
        if (selectedSource.value) {
            papers = papers.filter(p => p.source === selectedSource.value);
        }
        papers = SortUtils.sortList(papers, sortBy.value);
        return papers;
    });

    const visiblePaperTags = Vue.computed(() => {
        if (!FilterUtils) return [];
        return FilterUtils.filterTagsForList(allTags.value, getFilteredPapers.value);
    });

    // ============== Methods ==============
    async function loadPapers() {
        try {
            const res = await axios.get('/api/papers', { params: { page: 1, per_page: 500 } });
            allPapers.value = res.data.papers || [];
            total.value = res.data.total || allPapers.value.length;
        } catch (e) {
            console.error('加载论文失败:', e);
            ElementPlus.ElMessage.error('加载论文失败，请刷新重试');
            allPapers.value = [];
        }
    }

    async function loadTags() {
        try {
            const res = await axios.get('/api/tags');
            allTags.value = res.data.tags || [];
        } catch (e) {
            console.error('加载标签失败:', e);
        }
    }

    function toggleStatusFilter(status) {
        selectedStatus.value = FilterUtils.toggleStatusFilter(selectedStatus.value, status);
    }

    function toggleSourceFilter(source) {
        selectedSource.value = FilterUtils.toggleSourceFilter(selectedSource.value, source);
    }

    function toggleTagFilter(tagId) {
        selectedTagIds.value = FilterUtils.toggleTagFilter(selectedTagIds.value, tagId);
    }

    function clearAllFilters() {
        selectedStatus.value = null;
        selectedSource.value = null;
        selectedTagIds.value = [];
        searchKeyword.value = '';
    }

    async function viewPaper(paper, updatePaperStatus) {
        console.log('📄 [PaperModule] 查看论文:', paper);
        try {
            const res = await axios.get(`/api/papers/${paper.id}`);
            const paperDetail = res.data;
            selectedPaper.value = paperDetail;
            if (paperDetail.status === 'pending') {
                paperDetail.status = 'reading';
                await updatePaperStatus(paperDetail);
            }
        } catch (e) {
            console.error('加载论文详情失败:', e);
            selectedPaper.value = paper;
        }
    }

    async function toggleStar(paper) {
        paper.starred = !paper.starred;
        try {
            await axios.put(`/api/papers/${paper.id}`, { starred: paper.starred });
            ElementPlus.ElMessage.success(paper.starred ? '⭐ 已标星' : '已取消标星');
            if (selectedPaper.value && selectedPaper.value.id === paper.id) {
                selectedPaper.value.starred = paper.starred;
            }
        } catch (e) {
            paper.starred = !paper.starred;
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    async function updatePaperStatus(paper) {
        try {
            await axios.put(`/api/papers/${paper.id}`, { status: paper.status });
            if (selectedPaper.value && selectedPaper.value.id === paper.id) {
                selectedPaper.value.status = paper.status;
            }
        } catch (e) {
            ElementPlus.ElMessage.error('更新失败');
        }
    }

    async function deletePaper(paper) {
        try {
            await ElementPlus.ElMessageBox.confirm(
                '确定要删除这篇论文吗？',
                '警告',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            );
            await axios.delete(`/api/papers/${paper.id}`);
            ElementPlus.ElMessage.success('删除成功');
            selectedPaper.value = null;
            allPapers.value = allPapers.value.filter(p => p.id !== paper.id);
        } catch (e) {
            if (e !== 'cancel') {
                ElementPlus.ElMessage.error('删除失败');
            }
        }
    }

    async function downloadPaper(paper, pdfUrl) {
        if (!paper.file_path) {
            ElementPlus.ElMessage.warning('无文件可下载');
            return;
        }
        try {
            const res = await axios.get(`/api/papers/${paper.id}/download`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${paper.title.replace(/\//g, '_')}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            ElementPlus.ElMessage.success('下载成功');
        } catch (e) {
            ElementPlus.ElMessage.error('下载失败');
        }
    }

    async function addTagToPaper(paper, name) {
        if (!name) return;
        try {
            await axios.post(`/api/papers/${paper.id}/tags`, { name });
            ElementPlus.ElMessage.success('标签已添加');
            const res = await axios.get(`/api/papers/${paper.id}`);
            selectedPaper.value = res.data;
            loadTags();
        } catch (e) {
            ElementPlus.ElMessage.error('添加标签失败');
        }
    }

    async function removeTagFromPaper(paper, tagId) {
        try {
            await axios.delete(`/api/papers/${paper.id}/tags/${tagId}`);
            ElementPlus.ElMessage.success('标签已移除');
            const res = await axios.get(`/api/papers/${paper.id}`);
            selectedPaper.value = res.data;
            loadTags();
        } catch (e) {
            ElementPlus.ElMessage.error('移除标签失败');
        }
    }

    async function updateSaveLocal(paper, saveLocal) {
        try {
            await axios.put(`/api/papers/${paper.id}`, { save_local: saveLocal });
            paper.save_local = saveLocal;
            if (selectedPaper.value && selectedPaper.value.id === paper.id) {
                selectedPaper.value.save_local = saveLocal;
            }
            ElementPlus.ElMessage.success(
                saveLocal ? '已设置为保存本地' : '已设置为不保存本地'
            );
        } catch (e) {
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    async function updatePaperUrl(paper, url) {
        try {
            await axios.put(`/api/papers/${paper.id}`, { url: url });
            paper.url = url;
            if (selectedPaper.value && selectedPaper.value.id === paper.id) {
                selectedPaper.value.url = url;
            }
            ElementPlus.ElMessage.success('来源URL已更新');
        } catch (e) {
            ElementPlus.ElMessage.error('操作失败');
        }
    }

    // ============== arXiv 搜索相关方法 ==============
    async function loadArxivCategories() {
        try {
            const res = await axios.get('/api/papers/search/categories');
            arxivAllCategories.value = res.data.categories || {};
            arxivGroupedCategories.value = res.data.grouped_categories || {};
        } catch (e) {
            console.error('加载arXiv分类失败:', e);
        }
    }

    async function searchArxiv() {
        arxivSearchLoading.value = true;
        try {
            const params = {
                keywords: arxivKeywords.value || undefined,
                categories: arxivCategories.value.length > 0 ? arxivCategories.value.join(',') : undefined,
                max_results: arxivMaxResults.value,
                start_date: arxivStartDate.value || undefined,
                end_date: arxivEndDate.value || undefined
            };
            const res = await axios.get('/api/papers/search', { params });
            arxivSearchResults.value = res.data.results || [];
            selectedArxivPapers.value = [];
            ElementPlus.ElMessage.success(`找到 ${arxivSearchResults.value.length} 篇论文`);
        } catch (e) {
            console.error('搜索arXiv失败:', e);
            ElementPlus.ElMessage.error('搜索失败，请稍后重试');
        } finally {
            arxivSearchLoading.value = false;
        }
    }

    function toggleArxivSearch() {
        arxivSearchVisible.value = !arxivSearchVisible.value;
        if (arxivSearchVisible.value && Object.keys(arxivAllCategories.value).length === 0) {
            loadArxivCategories();
        }
    }

    function toggleArxivCategory(code) {
        const index = arxivCategories.value.indexOf(code);
        if (index > -1) {
            arxivCategories.value.splice(index, 1);
        } else {
            arxivCategories.value.push(code);
        }
    }

    function toggleArxivPaperSelection(arxivId) {
        const index = selectedArxivPapers.value.indexOf(arxivId);
        if (index > -1) {
            selectedArxivPapers.value.splice(index, 1);
        } else {
            selectedArxivPapers.value.push(arxivId);
        }
    }

    function selectAllArxivPapers() {
        if (selectedArxivPapers.value.length === arxivSearchResults.value.length) {
            selectedArxivPapers.value = [];
        } else {
            selectedArxivPapers.value = arxivSearchResults.value.map(p => p.arxiv_id);
        }
    }

    async function importSelectedPapers(savePdf = false) {
        if (selectedArxivPapers.value.length === 0) {
            ElementPlus.ElMessage.warning('请先选择要导入的论文');
            return;
        }

        const papersToImport = arxivSearchResults.value.filter(
            p => selectedArxivPapers.value.includes(p.arxiv_id)
        );

        try {
            const res = await axios.post('/api/papers/search/import', {
                papers: papersToImport,
                save_pdf: savePdf
            });

            ElementPlus.ElMessage.success(
                `成功导入 ${res.data.imported} 篇论文，跳过 ${res.data.skipped} 篇重复论文`
            );

            if (res.data.errors && res.data.errors.length > 0) {
                console.warn('导入错误:', res.data.errors);
            }

            await loadPapers();
            selectedArxivPapers.value = [];
            arxivSearchResults.value = [];
        } catch (e) {
            console.error('导入失败:', e);
            ElementPlus.ElMessage.error('导入失败');
        }
    }

    function clearArxivSearch() {
        arxivKeywords.value = '';
        arxivCategories.value = [];
        arxivMaxResults.value = 20;
        arxivStartDate.value = '';
        arxivEndDate.value = '';
        arxivSearchResults.value = [];
        selectedArxivPapers.value = [];
    }

    // ============== Exports ==============
    return {
        // State
        allPapers, selectedPaper,
        searchKeyword, sortBy,
        selectedTagIds, selectedStatus, selectedSource,
        allTags, total,
        statusFilters, sourceFilters,

        // arXiv 搜索相关 State
        arxivSearchVisible,
        arxivKeywords,
        arxivCategories,
        arxivMaxResults,
        arxivStartDate,
        arxivEndDate,
        arxivSearchResults,
        arxivAllCategories,
        arxivGroupedCategories,
        selectedArxivPapers,
        arxivSearchLoading,

        // Computed / Helpers
        getStatusCount, getSourceCount, getTagCount,
        getFilteredPapers, visiblePaperTags,

        // Methods
        loadPapers, loadTags,
        toggleStatusFilter, toggleSourceFilter, toggleTagFilter,
        clearAllFilters,
        viewPaper, toggleStar, updatePaperStatus,
        deletePaper, downloadPaper,
        addTagToPaper, removeTagFromPaper,
        updateSaveLocal, updatePaperUrl,

        // arXiv 搜索相关 Methods
        loadArxivCategories,
        searchArxiv,
        toggleArxivSearch,
        toggleArxivCategory,
        toggleArxivPaperSelection,
        selectAllArxivPapers,
        importSelectedPapers,
        clearArxivSearch
    };
}
