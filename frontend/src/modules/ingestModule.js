// 入库功能模块
// arXiv + 微信公众号 入库

export function createIngestModule({ Vue, ElementPlus, IngestAPI, refs }) {
    const { ref, computed } = Vue;

    const { arxivInput, ingesting, wechatUrl, wechatIngesting, wechatExtractOnly, activeMenu, loadPapers, loadAllNotes, loadAllArticles } = refs;

    async function ingestArxiv() {
        if (!arxivInput.value.trim()) return;
        ingesting.value = true;
        try {
            await IngestAPI.ingestArxiv(arxivInput.value);
            ElementPlus.ElMessage.success('入库成功！');
            arxivInput.value = '';
            activeMenu.value = 'library';
            loadPapers();
        } catch (e) {
            const msg = e.response?.data?.error || '入库失败';
            ElementPlus.ElMessage.error(msg);
        } finally {
            ingesting.value = false;
        }
    }

    async function ingestWechat() {
        if (!wechatUrl.value.trim()) return;
        wechatIngesting.value = true;
        try {
            await IngestAPI.ingestWechat(wechatUrl.value, wechatExtractOnly.value);
            ElementPlus.ElMessage.success('公众号文章入库成功！');
            wechatUrl.value = '';
            activeMenu.value = 'articles';
            loadAllArticles();
        } catch (e) {
            const msg = e.response?.data?.error || '入库失败';
            ElementPlus.ElMessage.error(msg);
        } finally {
            wechatIngesting.value = false;
        }
    }

    return {
        ingestArxiv,
        ingestWechat
    };
}
