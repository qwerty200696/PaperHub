// 筛选逻辑独立模块
// 可独立测试，无副作用

export function createFilterModule({ Vue, ElementPlus, PaperAPI, refs }) {
    const { ref, computed } = Vue;

    // 使用外层 setup 的 ref（模板绑定不用改）
    const {
        selectedSource, selectedStatus, selectedTagIds,
        dateRange, dateGranularity, yearStart, yearEnd,
        monthStartYear, monthStartMonth, monthEndYear, monthEndMonth,
        sourceStats, statusStats
    } = refs;

    // 只读配置
    const sourceFilters = ref([
        { label: '📄 arXiv', value: 'arxiv' },
        { label: '📁 本地PDF', value: 'pdf' }
    ]);
    const statusFilters = ref([
        { icon: '📚', label: '全部', value: null },
        { icon: '⏳', label: '待读', value: 'pending' },
        { icon: '📖', label: '在读', value: 'reading' },
        { icon: '✅', label: '已读', value: 'done' },
        { icon: '🔥', label: '精读', value: 'mastered' }
    ]);

    function toggleSourceFilter(source, reloadCallback) {
        selectedSource.value = selectedSource.value === source ? null : source;
        if (reloadCallback) reloadCallback();
    }

    function toggleStatusFilter(status, reloadCallback) {
        selectedStatus.value = selectedStatus.value === status ? null : status;
        if (reloadCallback) reloadCallback();
    }

    function toggleTagFilter(tagId, reloadCallback) {
        const index = selectedTagIds.value.indexOf(tagId);
        if (index > -1) {
            selectedTagIds.value.splice(index, 1);
        } else {
            selectedTagIds.value.push(tagId);
        }
        if (reloadCallback) reloadCallback();
    }

    function clearDateFilter(reloadCallback) {
        dateRange.value = null;
        yearStart.value = null;
        yearEnd.value = null;
        monthStartYear.value = null;
        monthStartMonth.value = null;
        monthEndYear.value = null;
        monthEndMonth.value = null;
        if (reloadCallback) reloadCallback();
    }

    function clearAllFilters(reloadCallback) {
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
        if (reloadCallback) reloadCallback();
    }

    function onDateGranularityChange() {
        clearDateFilter();
    }

    function filterByDateRange(reloadCallback) {
        yearStart.value = null;
        yearEnd.value = null;
        monthStartYear.value = null;
        monthStartMonth.value = null;
        monthEndYear.value = null;
        monthEndMonth.value = null;
        if (reloadCallback) reloadCallback();
    }

    function applyYearFilter(reloadCallback) {
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
        if (reloadCallback) reloadCallback();
    }

    function applyMonthFilter(reloadCallback) {
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
        if (reloadCallback) reloadCallback();
    }

    // 构建 API 查询参数
    function buildQueryParams() {
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
        return params;
    }

    // 共享状态：使用外层 setup 的 ref
    function useSharedRefs(externalRefs) {
        // 直接用外层的 ref 对象，不用模块内部的了
        // 这样模板绑定完全不用改
        Object.assign(this, externalRefs);
        console.log('📦 [FilterModule] 共享状态绑定完成');
    }

    // 加载论文数据
    async function loadPapers(papersRef, allPapersCacheRef, totalRef, sortFn) {
        console.log('📦 [FilterModule] 加载论文...');
        try {
            const params = buildQueryParams();
            const res = await PaperAPI.getPapers(params);
            console.log('📦 [FilterModule] 论文响应:', res.data);
            allPapersCacheRef.value = (res.data.papers || []).map(p => ({
                ...p,
                starred: Boolean(p.starred)
            }));
            papersRef.value = sortFn ? sortFn(allPapersCacheRef.value) : allPapersCacheRef.value;
            totalRef.value = res.data.total || 0;

            const sStats = {};
            papersRef.value.forEach(p => {
                const s = p.source === 'wechat' ? 'wechat' : p.source;
                sStats[s] = (sStats[s] || 0) + 1;
            });
            sourceStats.value = sStats;

            const stStats = {};
            papersRef.value.forEach(p => {
                stStats[p.status] = (stStats[p.status] || 0) + 1;
            });
            stStats[null] = papersRef.value.length;
            statusStats.value = stStats;
        } catch (e) {
            console.error('📦 [FilterModule] 加载失败:', e);
            ElementPlus.ElMessage.error('加载失败');
        }
    }

    return {
        // 操作
        toggleSourceFilter, toggleStatusFilter, toggleTagFilter,
        clearDateFilter, clearAllFilters, onDateGranularityChange,
        filterByDateRange, applyYearFilter, applyMonthFilter,
        // 核心方法
        buildQueryParams, loadPapers
    };
}
