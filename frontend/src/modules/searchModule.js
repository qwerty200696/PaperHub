/**
 * 搜索模块 - 管理搜索状态和操作
 */

import { ref, computed } from 'vue';

// 搜索状态
const searchKeyword = ref('');
const searchResults = ref([]);
const searchSuggestions = ref([]);
const searchHistory = ref([]);
const isSearching = ref(false);
const currentPage = ref(1);
const totalResults = ref(0);
const searchBreakdown = ref({ papers: 0, articles: 0, notes: 0 });
const activeModule = ref('all'); // papers, articles, notes, all

// 从 localStorage 加载搜索历史
function loadSearchHistory() {
    try {
        const saved = localStorage.getItem('search_history');
        if (saved) {
            searchHistory.value = JSON.parse(saved);
        }
    } catch (e) {
        searchHistory.value = [];
    }
}

// 保存搜索历史
function saveSearchHistory(query) {
    if (!query.trim()) return;
    
    // 移除重复项
    searchHistory.value = searchHistory.value.filter(h => h !== query);
    // 添加到开头
    searchHistory.value.unshift(query);
    // 最多保留10条
    searchHistory.value = searchHistory.value.slice(0, 10);
    
    try {
        localStorage.setItem('search_history', JSON.stringify(searchHistory.value));
    } catch (e) {
        console.warn('Failed to save search history');
    }
}

// 获取搜索建议
async function fetchSuggestions(query) {
    if (!query.trim()) {
        searchSuggestions.value = [];
        return;
    }
    
    try {
        const response = await fetch(`/api/search/suggest?q=${encodeURIComponent(query)}&limit=5`);
        const data = await response.json();
        if (data.success) {
            searchSuggestions.value = data.suggestions;
        }
    } catch (e) {
        console.error('Failed to fetch suggestions:', e);
    }
}

// 执行搜索
async function performSearch(query, module = 'all', page = 1) {
    if (!query.trim()) return;
    
    isSearching.value = true;
    activeModule.value = module;
    currentPage.value = page;
    
    try {
        const url = `/api/search?q=${encodeURIComponent(query)}&module=${module}&page=${page}&size=20&highlight=true`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            searchResults.value = data.results;
            totalResults.value = data.total;
            searchBreakdown.value = data.breakdown || { papers: 0, articles: 0, notes: 0 };
            saveSearchHistory(query);
            searchKeyword.value = query;
        } else {
            console.error('Search failed:', data.error);
        }
    } catch (e) {
        console.error('Search error:', e);
    } finally {
        isSearching.value = false;
    }
}

// 清除搜索
function clearSearch() {
    searchKeyword.value = '';
    searchResults.value = [];
    searchSuggestions.value = [];
    totalResults.value = 0;
}

// 搜索结果分组
const groupedResults = computed(() => {
    const groups = {
        papers: { label: '📚 论文库', items: [], count: searchBreakdown.value.papers },
        articles: { label: '📰 文章库', items: [], count: searchBreakdown.value.articles },
        notes: { label: '📝 笔记库', items: [], count: searchBreakdown.value.notes }
    };
    
    searchResults.value.forEach(item => {
        if (item.type === 'paper') {
            groups.papers.items.push(item);
        } else if (item.type === 'article') {
            groups.articles.items.push(item);
        } else if (item.type === 'note') {
            groups.notes.items.push(item);
        }
    });
    
    return groups;
});

// 初始化
loadSearchHistory();

export function useSearch() {
    return {
        // 状态
        searchKeyword,
        searchResults,
        searchSuggestions,
        searchHistory,
        isSearching,
        currentPage,
        totalResults,
        searchBreakdown,
        activeModule,
        groupedResults,
        
        // 方法
        fetchSuggestions,
        performSearch,
        clearSearch,
        saveSearchHistory,
        loadSearchHistory
    };
}