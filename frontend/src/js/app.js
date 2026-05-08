/**
 * PaperHub 应用主入口文件
 * 整合所有模块，提供统一的应用实例
 */

export function initApp({ Vue, ElementPlus, axios, FilterUtils, SortUtils, createIngestModule, createFileUploadModule }) {
    const { ref, computed, onMounted, watch } = Vue

    console.log('✅ PaperHub 应用初始化开始')

    // ==================== 模块加载状态 ====================
    const modulesReady = ref({
        utils: false,
        ingest: false,
        upload: false
    })

    // ==================== 工具模块 ====================
    let filterUtils = null
    let sortUtils = null
    let ingestModule = null
    let fileUploadModule = null

    // ==================== 核心状态 ====================
    const sidebarRef = ref(null)
    const resizing = ref(false)

    // ==================== 全局共享状态 ====================
    const activeMenu = ref('library')
    const ingestTab = ref('arxiv')

    // 笔记展示相关（用于论文详情页）
    const paperNotes = ref([])
    const showFullNote = ref(null)

    // ==================== 通用工具函数 ====================
    function displayAuthors(authorsStr) {
        if (!authorsStr) return ''
        try {
            const authors = JSON.parse(authorsStr)
            return authors.slice(0, 5).join(', ') + (authors.length > 5 ? ' 等' : '')
        } catch (e) {
            return authorsStr
        }
    }

    function formatDateTime(dt) {
        if (!dt) return ''
        const date = new Date(dt)
        return date.toLocaleString('zh-CN')
    }

    // ==================== 侧边栏拖拽 ====================
    function startResize(e) {
        resizing.value = true
        document.addEventListener('mousemove', doResize)
        document.addEventListener('mouseup', stopResize)
        document.body.style.cursor = 'col-resize'
        document.body.style.userSelect = 'none'
    }

    function doResize(e) {
        if (!sidebarRef.value) return
        const newWidth = e.clientX - sidebarRef.value.getBoundingClientRect().left
        if (newWidth >= 180 && newWidth <= 450) {
            sidebarRef.value.style.width = newWidth + 'px'
        }
    }

    function stopResize() {
        resizing.value = false
        document.removeEventListener('mousemove', doResize)
        document.removeEventListener('mouseup', stopResize)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
    }

    // ==================== 菜单切换 ====================
    function handleMenu(index) {
        console.log('Menu clicked:', index)
        activeMenu.value = index
    }

    function showIngest() {
        activeMenu.value = 'ingest'
    }

    // ==================== 模块初始化 ====================
    async function loadAllModules() {
        try {
            console.log('📦 加载模块...')

            filterUtils = FilterUtils
            sortUtils = SortUtils
            modulesReady.value.utils = true

            if (createIngestModule) {
                ingestModule = createIngestModule({
                    Vue, ElementPlus,
                    refs: {}
                })
                modulesReady.value.ingest = true
            }

            if (createFileUploadModule) {
                fileUploadModule = createFileUploadModule({
                    Vue, ElementPlus,
                    refs: {}
                })
                modulesReady.value.upload = true
            }

            console.log('✅ 所有模块加载成功')
            return true
        } catch (e) {
            console.error('❌ 模块加载失败:', e)
            return false
        }
    }

    // ==================== 导出给模板使用 ====================
    return {
        modulesReady,
        filterUtils,
        sortUtils,
        ingestModule,
        fileUploadModule,

        sidebarRef,
        resizing,
        activeMenu,
        ingestTab,
        paperNotes,
        showFullNote,

        displayAuthors,
        formatDateTime,

        startResize,
        doResize,
        stopResize,
        handleMenu,
        showIngest,

        loadAllModules
    }
}

