// 标签管理模块
// 独立无副作用，可单独测试

export function createTagModule({ Vue, ElementPlus, PaperAPI, refs }) {
    const { ref, computed } = Vue;

    const { allTags, newTagName, loadPapers } = refs;

    async function loadTags() {
        try {
            const res = await PaperAPI.getTags();
            allTags.value = (res.data.tags || []).filter(t => t.count > 0);
        } catch (e) {
            console.error('📦 [TagModule] 加载标签失败:', e);
        }
    }

    async function addTagToPaper(paper) {
        if (!newTagName.value.trim()) return;
        try {
            const res = await PaperAPI.addTag(paper.id, newTagName.value.trim());
            paper.tags = res.data.tags;
            newTagName.value = '';
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

    async function addTagInList(paper) {
        if (!paper.newTagInput?.trim()) return;
        try {
            const res = await PaperAPI.addTag(paper.id, paper.newTagInput.trim());
            paper.tags = res.data.tags;
            paper.newTagInput = '';
            loadTags();
            ElementPlus.ElMessage.success('标签添加成功');
        } catch (e) {
            ElementPlus.ElMessage.error('标签添加失败');
        }
    }

    return {
        loadTags,
        addTagToPaper,
        removeTagFromPaper,
        addTagInList
    };
}
