/**
 * 日期筛选模块
 * 处理论文库的日期筛选功能
 */

export function createDateFilterModule({ Vue, ElementPlus, loadPapers }) {
    const { ref } = Vue

    const dateRange = ref(null)
    const dateGranularity = ref('day')
    const currentYear = new Date().getFullYear()
    const yearStart = ref(null)
    const yearEnd = ref(null)
    const monthStartYear = ref(null)
    const monthStartMonth = ref(null)
    const monthEndYear = ref(null)
    const monthEndMonth = ref(null)

    /**
     * 日期粒度改变时清空其他筛选条件
     */
    function onDateGranularityChange() {
        dateRange.value = null
        yearStart.value = null
        yearEnd.value = null
        monthStartYear.value = null
        monthStartMonth.value = null
        monthEndYear.value = null
        monthEndMonth.value = null
    }

    /**
     * 应用日期范围筛选
     */
    function filterByDateRange() {
        yearStart.value = null
        yearEnd.value = null
        monthStartYear.value = null
        monthStartMonth.value = null
        monthEndYear.value = null
        monthEndMonth.value = null
        if (loadPapers) loadPapers()
    }

    /**
     * 应用年份筛选
     */
    function applyYearFilter() {
        if (loadPapers) loadPapers()
    }

    /**
     * 应用月份筛选
     */
    function applyMonthFilter() {
        if (loadPapers) loadPapers()
    }

    /**
     * 清空日期筛选
     */
    function clearDateFilter() {
        dateRange.value = null
        yearStart.value = null
        yearEnd.value = null
        monthStartYear.value = null
        monthStartMonth.value = null
        monthEndYear.value = null
        monthEndMonth.value = null
        if (loadPapers) loadPapers()
    }

    /**
     * 从 localStorage 恢复筛选状态
     */
    function restoreFromStorage(storage) {
        if (!storage) return
        try {
            const state = JSON.parse(storage)
            dateRange.value = state.dateRange
            yearStart.value = state.yearStart
            yearEnd.value = state.yearEnd
            monthStartYear.value = state.monthStartYear
            monthStartMonth.value = state.monthStartMonth
            monthEndYear.value = state.monthEndYear
            monthEndMonth.value = state.monthEndMonth
        } catch (e) {
            console.error('恢复日期筛选状态失败:', e)
        }
    }

    return {
        dateRange,
        dateGranularity,
        currentYear,
        yearStart,
        yearEnd,
        monthStartYear,
        monthStartMonth,
        monthEndYear,
        monthEndMonth,
        onDateGranularityChange,
        filterByDateRange,
        applyYearFilter,
        applyMonthFilter,
        clearDateFilter,
        restoreFromStorage
    }
}

