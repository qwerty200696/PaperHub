/**
 * 统一资源模块管理器
 * 统一管理 paper/article/note 三个模块的加载和协调
 */

export function createResourceManager({ Vue, ElementPlus, axios }) {
    const { ref } = Vue

    // 三个主要的模块实例
    let paperModule = null
    let articleModule = null
    let noteModule = null

    // 全局共享状态
    const activeMenu = ref('library')
    
    // 模块是否已加载
    const modulesLoaded = ref({
        paper: false,
        article: false,
        note: false
    })

    /**
     * 统一的模块工厂
     */
    async function initModules() {
        try {
            // 动态加载三个模块
            const [paperMod, articleMod, noteMod] = await Promise.all([
                import('./paperModule.js'),
                import('./articleModule.js'),
                import('./noteModule.js')
            ])

            paperModule = paperMod.createPaperModule({ Vue, ElementPlus, axios })
            articleModule = articleMod.createArticleModule({ Vue, ElementPlus, axios })
            noteModule = noteMod.createNoteModule({ Vue, ElementPlus, axios })

            modulesLoaded.value.paper = true
            modulesLoaded.value.article = true
            modulesLoaded.value.note = true

            console.log('✅ 所有资源模块加载成功')
            return true
        } catch (e) {
            console.error('❌ 模块加载失败:', e)
            return false
        }
    }

    /**
     * 根据菜单处理
     */
    function handleMenu(index) {
        console.log('Menu clicked:', index)
        activeMenu.value = index
        
        // 清除其他模块的选中状态
        if (paperModule) paperModule.selectedPaper.value = null
        if (articleModule) articleModule.viewingArticle.value = null
        if (noteModule) noteModule.viewingNote.value = null
        
        if (index === 'library') paperModule.loadPapers()
        if (index === 'notes') noteModule.loadAllNotes()
        if (index === 'articles') articleModule.loadAllArticles()
    }

    /**
     * 获取指定模块间的导航 - 从笔记跳转到论文
     */
    function goToPaper(paperId, event) {
        if (event) event.stopPropagation()
        const paper = paperModule.allPapers.value.find(p => p.id === paperId)
        if (paper) {
            paperModule.viewPaper(paper, paperModule.updatePaperStatus)
            activeMenu.value = 'library'
            if (noteModule) noteModule.viewingNote.value = null
            if (articleModule) articleModule.viewingArticle.value = null
        } else {
            ElementPlus.ElMessage.warning('找不到该论文')
        }
    }

    /**
     * 跳转到文章
     */
    function goToArticle(articleId, event) {
        if (event) event.stopPropagation()
        const article = articleModule.allArticles.value.find(a => a.id === articleId)
        if (article) {
            articleModule.viewArticleDetail(article)
            activeMenu.value = 'articles'
            paperModule.selectedPaper.value = null
            if (noteModule) noteModule.viewingNote.value = null
        } else {
            ElementPlus.ElMessage.warning('找不到该文章')
        }
    }

    /**
     * 跳转到笔记
     */
    function goToNote(noteId, event) {
        if (event) event.stopPropagation()
        const note = noteModule.allNotes.value.find(n => n.id === noteId)
        if (note) {
            noteModule.viewNoteDetail(note)
            activeMenu.value = 'notes'
            paperModule.selectedPaper.value = null
            articleModule.viewingArticle.value = null
        } else {
            ElementPlus.ElMessage.warning('找不到该笔记')
        }
    }

    return {
        activeMenu,
        modulesLoaded,
        paperModule,
        articleModule,
        noteModule,
        initModules,
        handleMenu,
        goToPaper,
        goToArticle,
        goToNote
    }
}

