
export const FilterUtils = {
    statusConfig: [
        { icon: '📚', label: '全部', value: null },
        { icon: '⏳', label: '待读', value: 'pending' },
        { icon: '📖', label: '在读', value: 'reading' },
        { icon: '✅', label: '已读', value: 'done' },
        { icon: '🔥', label: '精读', value: 'mastered' }
    ],

    getStatusCount(list, status) {
        if (status === null) return list.length;
        return list.filter(item => item.status === status).length;
    },

    toggleStatusFilter(currentValue, targetValue) {
        return currentValue === targetValue ? null : targetValue;
    },

    filterByStatus(list, selectedStatus) {
        if (!selectedStatus) return list;
        return list.filter(item => item.status === selectedStatus);
    },

    filterByKeyword(list, keyword, fields = ['title', 'author', 'content']) {
        const kw = (keyword || '').toLowerCase().trim();
        if (!kw) return list;
        return list.filter(item => {
            return fields.some(field => {
                const value = item[field] || '';
                return value.toLowerCase().includes(kw);
            });
        });
    },

    filterByTags(list, selectedTagIds) {
        if (!selectedTagIds || selectedTagIds.length === 0) return list;
        return list.filter(item => {
            const itemTagIds = (item.tags || []).map(t => t.id);
            return selectedTagIds.every(id => itemTagIds.includes(id));
        });
    },

    toggleTagFilter(selectedIds, tagId) {
        const idx = selectedIds.indexOf(tagId);
        if (idx > -1) {
            return [...selectedIds.slice(0, idx), ...selectedIds.slice(idx + 1)];
        }
        return [...selectedIds, tagId];
    },

    applyAllFilters(list, { keyword, selectedStatus, selectedTagIds, keywordFields = ['title', 'author'] }) {
        let result = [...list];
        result = FilterUtils.filterByKeyword(result, keyword, keywordFields);
        result = FilterUtils.filterByStatus(result, selectedStatus);
        result = FilterUtils.filterByTags(result, selectedTagIds);
        return result;
    },

    getSourceCount(list, source, sourceField = 'source') {
        if (source === null) return list.length;
        return list.filter(item => item[sourceField] === source).length;
    },

    toggleSourceFilter(currentValue, targetValue) {
        return currentValue === targetValue ? null : targetValue;
    },

    filterBySource(list, selectedSource, sourceField = 'source') {
        if (!selectedSource) return list;
        return list.filter(item => item[sourceField] === selectedSource);
    },

    getNoteTypeCount(list, type) {
        if (type === null || type === 'all') return list.length;
        if (type === 'paper') {
            return list.filter(n => n.papers && n.papers.length > 0).length;
        } else if (type === 'free') {
            return list.filter(n => !n.papers || n.papers.length === 0).length;
        }
        return list.length;
    },

    filterByNoteType(list, type) {
        if (!type || type === 'all') return list;
        if (type === 'paper') {
            return list.filter(n => n.papers && n.papers.length > 0);
        } else if (type === 'free') {
            return list.filter(n => !n.papers || n.papers.length === 0);
        }
        return list;
    },

    getTagCount(list, tagId) {
        return list.filter(item => {
            const itemTagIds = (item.tags || []).map(t => t.id);
            return itemTagIds.includes(tagId);
        }).length;
    },

    filterTagsForList(allTags, list) {
        return allTags.filter(tag => {
            return FilterUtils.getTagCount(list, tag.id) > 0;
        });
    }
};
