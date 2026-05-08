// 论文状态管理 - 组合式函数
// 依赖注入模式，支持 CDN 全局变量

export function usePaperStore({ Vue, ElementPlus, PaperAPI, utils }) {
    const { ref, computed } = Vue;
    const { displayAuthors, statusText, statusType } = utils;

    // 数据状态
    const papers = ref([]);
    const allPapersCache = ref([]);
    const selectedPaper = ref(null);
    const total = ref(0);
    const allTags = ref([]);
    const selectedTagIds = ref([]);
    const sortBy = ref(localStorage.getItem('paper_sort_by') || 'created_at');
    const newTagName = ref('');

    // 筛选状态
    const selectedStatus = ref(null);
    const selectedSource = ref(null);
    const dateRange = ref(null);
    const dateGranularity = ref('day');
    const yearStart = ref(null);
    const yearEnd = ref(null);
    const monthStartYear = ref(null);
    const monthStartMonth = ref(null);
    const monthEndYear = ref(null);
    const monthEndMonth = ref(null);

    // 统计
    const statusFilters = ref([
        { icon: '📚', label: '全部', value: null },
        { icon: '⏳', label: '待读', value: 'pending' },
        { icon: '📖', label: '在读', value: 'reading' },
        { icon: '✅', label: '已读', value: 'done' },
        { icon: '🔥', label: '精读', value: 'mastered' }
    ]);
    const sourceFilters = ref([
        { label: 'arXiv', value: 'arxiv' },
        { label: '微信URL', value: 'wechat' },
        { label: '对话笔记', value: 'note' },
        { label: '知乎专栏', value: 'zhihu' }
    ]);
    const statusStats = ref({});
    const sourceStats = ref({});

    // 计算属性
    const pdfUrl = computed(() => {
        if (!selectedPaper.value?.id) return '';
        return PaperAPI.downloadUrl(selectedPaper.value.id);
    });

    // 排序逻辑
    function sortPapers(list) {
        const papers = [...list];
        const statusOrder = { pending: 0, reading: 1, mastered: 2, done: 3 };
        switch (sortBy.value) {
            case 'starred':
                papers.sort((a, b) => {
                    const aStar = a.starred ? 0 : 1;
                    const bStar = b.starred ? 0 : 1;
                    if (aStar !== bStar) return aStar - bStar;
                    const aStatus = statusOrder[a.status] ?? 9;
                    const bStatus = statusOrder[b.status] ?? 9;
                    if (aStatus !== bStatus) return aStatus - bStatus;
                    return new Date(b.created_at || 0) - new Date(a.created_at || 0);
                });
                break;
            case 'status':
                papers.sort((a, b) => {
                    const aStatus = statusOrder[a.status] ?? 9;
                    const bStatus = statusOrder[b.status] ?? 9;
                    if (aStatus !== bStatus) return aStatus - bStatus;
                    return new Date(b.created_at || 0) - new Date(a.created_at || 0);
                });
                break;
            case 'published_at':
                papers.sort((a, b) => new Date(b.published_at || 0) - new Date(a.published_at || 0));
                break;
            case 'title':
                papers.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'));
                break;
            case 'created_at':
            default:
                papers.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
                break;
        }
        return papers;
    }

    function applySort() {
        localStorage.setItem('paper_sort_by', sortBy.value);
        papers.value = sortPapers(allPapersCache.value);
    }

    // 加载数据
    async function loadPapers() {
        console.log('Loading papers...');
        try {
            const params = { page: 1, per_page: 100 };
            if (selectedTagIds.value.length > 0) {
                params.tag_ids = selectedTagIds.value.join(',');
            }
            if (selectedSource.value) {
                params.source = selectedSource.value;
            }
            if (selectedStatus.value) {
                params.status = selectedStatus.value;
            }
            if (dateRange.value && dateRange.value.length === 2) {
                params.start_date = dateRange.value[0];
                params.end_date = dateRange.value[1];
            }
            if (yearStart.value) {
                params.start_year = yearStart.value;
                if (yearEnd.value) {
                    params.end_year = yearEnd.value;
                }
            }
            if (monthStartYear.value && monthStartMonth.value) {
                params.start_month = `${monthStartYear.value}-${String(monthStartMonth.value).padStart(2, '0')}`;
                if (monthEndYear.value && monthEndMonth.value) {
                    params.end_month = `${monthEndYear.value}-${String(monthEndMonth.value).padStart(2, '0')}`;
                }
            }
            const res = await PaperAPI.getPapers(params);
            console.log('Papers response:', res.data);
            allPapersCache.value = (res.data.papers || []).map(p => ({
                ...p,
                starred: Boolean(p.starred)
            }));
            papers.value = sortPapers(allPapersCache.value);
            total.value = res.data.total || 0;

            const sStats = {};
            papers.value.forEach(p => {
                const s = p.source === 'wechat' ? 'wechat' : p.source;
                sStats[s] = (sStats[s] || 0) + 1;
            });
            sourceStats.value = sStats;

            const stStats = {};
            papers.value.forEach(p => {
                stStats[p.status] = (stStats[p.status] || 0) + 1;
            });
            stStats[null] = papers.value.length;
            statusStats.value = stStats;
        } catch (e) {
            console.error('Load papers error:', e);
            ElementPlus.ElMessage.error('加载失败');
        }
    }

    async function loadTags() {
        try {
            const res = await PaperAPI.getTags();
            allTags.value = (res.data.tags || []).filter(t => t.count > 0);
        } catch (e) {
            console.error('Load tags error:', e);
        }
    }

    // 筛选操作
    function toggleSourceFilter(source) {
        selectedSource.value = selectedSource.value === source ? null : source;
        loadPapers();
    }

    function toggleStatusFilter(status) {
        selectedStatus.value = selectedStatus.value === status ? null : status;
        loadPapers();
    }

    function toggleTagFilter(tagId) {
        const index = selectedTagIds.value.indexOf(tagId);
        if (index > -1) {
            selectedTagIds.value.splice(index, 1);
        } else {
            selectedTagIds.value.push(tagId);
        }
        loadPapers();
    }

    function clearDateFilter() {
        dateRange.value = null;
        yearStart.value = null;
        yearEnd.value = null;
        monthStartYear.value = null;
        monthStartMonth.value = null;
        monthEndYear.value = null;
        monthEndMonth.value = null;
        loadPapers();
    }

    function clearAllFilters() {
        selectedSource.value = null;
        selectedStatus.value = null;
        dateRange.value = null;
        yearStart.value = null;
        yearEnd.value = null;
        monthStartYear.value = null;
        monthStartMonth.value = null;
        monthEndYear.value = null;
        monthEndMonth.value = null;
        selectedTagIds.value = [];
        loadPapers();
    }

    function onDateGranularityChange() {
        clearDateFilter();
    }

    function filterByDateRange() {
        yearStart.value = null;
        yearEnd.value = null;
        monthStartYear.value = null;
        monthStartMonth.value = null;
        monthEndYear.value = null;
        monthEndMonth.value = null;
        loadPapers();
    }

    function applyYearFilter() {
        const y1 = parseInt(yearStart.value);
        const y2 = yearEnd.value ? parseInt(yearEnd.value) : null;
        if (isNaN(y1) || y1 < 2000 || y1 > 2100) {
            ElementPlus.ElMessage.warning('请输入有效的年份');
            return;
        }
        if (y2 && (isNaN(y2) || y2 < 2000 || y2 > 2100)) {
            ElementPlus.ElMessage.warning('请输入有效的结束年份');
            return;
        }
        yearStart.value = y1;
        yearEnd.value = y2;
        dateRange.value = null;
        monthStartYear.value = null;
        monthStartMonth.value = null;
        monthEndYear.value = null;
        monthEndMonth.value = null;
        loadPapers();
    }

    function applyMonthFilter() {
        const y1 = parseInt(monthStartYear.value);
        const m1 = parseInt(monthStartMonth.value);
        const y2 = monthEndYear.value ? parseInt(monthEndYear.value) : null;
        const m2 = monthEndMonth.value ? parseInt(monthEndMonth.value) : null;

        if (isNaN(y1) || y1 < 2000 || y1 > 2100) {
            ElementPlus.ElMessage.warning('请输入有效的年份');
            return;
        }
        if (isNaN(m1) || m1 < 1 || m1 > 12) {
            ElementPlus.ElMessage.warning('请输入有效的月份 1-12');
            return;
        }
        if (y2 && (isNaN(y2) || y2 < 2000 || y2 > 2100)) {
            ElementPlus.ElMessage.warning('请输入有效的结束年份');
            return;
        }
        if (m2 && (isNaN(m2) || m2 < 1 || m2 > 12)) {
            ElementPlus.ElMessage.warning('请输入有效的结束月份 1-12');
            return;
        }

        monthStartYear.value = y1;
        monthStartMonth.value = m1;
        monthEndYear.value = y2;
        monthEndMonth.value = m2;
        dateRange.value = null;
        yearStart.value = null;
        yearEnd.value = null;
        loadPapers();
    }

    // 论文操作
    async function viewPaper(paper) {
        console.log('Viewing paper:', paper);
        selectedPaper.value = paper;
        if (paper.status === 'pending') {
            paper.status = 'reading';
            await updatePaperStatus(paper);
        }
    }

    async function updatePaperStatus(paper) {
        await PaperAPI.updateStatus(paper.id, paper.status);
        ElementPlus.ElMessage.success('状态已更新');
    }

    async function toggleStar(paper) {
        paper.starred = !paper.starred;
        await PaperAPI.toggleStar(paper.id, paper.starred);
        ElementPlus.ElMessage.success(paper.starred ? '已标星' : '已取消标星');
    }

    async function deletePaper(paper) {
        try {
            await ElementPlus.ElMessageBox.confirm(
                `确定要删除论文「${paper.title}」吗？\n删除后无法恢复，本地文件也将一并删除！`,
                '确认删除',
                {
                    confirmButtonText: '确定删除',
                    cancelButtonText: '取消',
                    type: 'warning',
                    dangerouslyUseHTMLString: false
                }
            );

            await PaperAPI.deletePaper(paper.id);
            papers.value = papers.value.filter(p => p.id !== paper.id);
            if (selectedPaper.value && selectedPaper.value.id === paper.id) {
                selectedPaper.value = null;
            }
            ElementPlus.ElMessage.success('论文已删除');
        } catch (e) {
            if (e !== 'cancel') {
                console.error('Delete error:', e);
                ElementPlus.ElMessage.error('删除失败');
            }
        }
    }

    function downloadPaper(paper) {
        window.open(PaperAPI.downloadUrl(paper.id), '_blank');
    }

    // 标签操作
    async function addTagToPaper(paper, tagName) {
        if (!tagName.trim()) return;
        try {
            const res = await PaperAPI.addTag(paper.id, tagName.trim());
            paper.tags = res.data.tags;
            loadTags();
            ElementPlus.ElMessage.success('标签添加成功');
        } catch (e) {
            ElementPlus.ElMessage.error('标签添加失败');
        }
    }

    async function removeTagFromPaper(paper, tag) {
        try {
            await PaperAPI.removeTag(paper.id, tag.id);
            paper.tags = paper.tags.filter(t => t.id !== tag.id);
            loadTags();
            ElementPlus.ElMessage.success('标签已移除');
        } catch (e) {
            ElementPlus.ElMessage.error('标签移除失败');
        }
    }

    async function addTagInList(paper, tagName) {
        await addTagToPaper(paper, tagName);
        newTagName.value = '';
    }

    return {
        // 数据
        papers, allPapersCache, selectedPaper, total, allTags, selectedTagIds, sortBy, newTagName,
        // 筛选状态
        selectedStatus, selectedSource, dateRange, dateGranularity,
        yearStart, yearEnd, monthStartYear, monthStartMonth, monthEndYear, monthEndMonth,
        // 统计
        statusFilters, sourceFilters, statusStats, sourceStats,
        // 计算属性
        pdfUrl,
        // 排序
        sortPapers, applySort,
        // 加载
        loadPapers, loadTags,
        // 筛选
        toggleSourceFilter, toggleStatusFilter, toggleTagFilter,
        clearDateFilter, clearAllFilters,
        onDateGranularityChange, filterByDateRange,
        applyYearFilter, applyMonthFilter,
        // 论文操作
        viewPaper, updatePaperStatus, toggleStar, deletePaper, downloadPaper,
        // 标签操作
        addTagToPaper, removeTagFromPaper, addTagInList,
        // 工具
        displayAuthors, statusText, statusType
    };
}
