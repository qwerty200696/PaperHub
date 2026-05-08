
export const SortUtils = {
    statusOrder: { pending: 0, reading: 1, done: 2, mastered: 3 },

    sortByStarred(list, statusField = 'status') {
        return [...list].sort((a, b) => {
            const aStar = a.starred ? 0 : 1;
            const bStar = b.starred ? 0 : 1;
            if (aStar !== bStar) return aStar - bStar;
            const aStatus = SortUtils.statusOrder[a[statusField]] || 9;
            const bStatus = SortUtils.statusOrder[b[statusField]] || 9;
            if (aStatus !== bStatus) return aStatus - bStatus;
            return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        });
    },

    sortByStatus(list, statusField = 'status') {
        return [...list].sort((a, b) => {
            const aStatus = SortUtils.statusOrder[a[statusField]] || 9;
            const bStatus = SortUtils.statusOrder[b[statusField]] || 9;
            if (aStatus !== bStatus) return aStatus - bStatus;
            const aStar = a.starred ? 0 : 1;
            const bStar = b.starred ? 0 : 1;
            if (aStar !== bStar) return aStar - bStar;
            return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        });
    },

    sortByTitle(list) {
        return [...list].sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    },

    sortByDate(list, dateField = 'created_at') {
        return [...list].sort((a, b) => new Date(b[dateField] || 0) - new Date(a[dateField] || 0));
    },

    sortList(list, sortBy, statusField = 'status', dateField = 'created_at') {
        switch (sortBy) {
            case 'starred':
                return SortUtils.sortByStarred(list, statusField);
            case 'status':
                return SortUtils.sortByStatus(list, statusField);
            case 'title':
                return SortUtils.sortByTitle(list);
            case 'published_at':
                return SortUtils.sortByDate(list, 'published_at');
            case 'created_at':
            default:
                return SortUtils.sortByDate(list, dateField);
        }
    }
};
