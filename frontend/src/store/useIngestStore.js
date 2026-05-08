// 入库功能状态管理
// 依赖注入模式，支持 CDN 全局变量

export function useIngestStore({ Vue, ElementPlus, IngestAPI, utils }) {
    const { ref } = Vue;
    const { getCurrentDateTime, extractTitleFromContent } = utils;

    // 导航与视图
    const ingestTab = ref('arxiv');
    const arxivInput = ref('');
    const ingesting = ref(false);

    // 微信相关
    const wechatUrl = ref('');
    const wechatIngesting = ref(false);
    const wechatContent = ref('');
    const wechatExtractOnly = ref(false);

    // 文件上传
    const uploadRef = ref(null);
    const uploadFiles = ref([]);
    const uploading = ref(false);

    // 笔记相关
    const noteIngesting = ref(false);
    const noteSources = ref(['豆包', 'DeepSeek', '千问', 'Kimi', '元宝', 'Claude', 'ChatGPT', '其他']);
    const customSource = ref('');
    const noteForm = ref({
        title: '',
        source: '豆包',
        created_at: getCurrentDateTime(),
        content: ''
    });

    // 知乎相关
    const zhihuMode = ref('url');
    const zhihuIngesting = ref(false);
    const zhihuForm = ref({
        title: '',
        author: '',
        created_at: getCurrentDateTime(),
        content: ''
    });
    const zhihuUrlForm = ref({
        url: '',
        cookie: localStorage.getItem('zhihu_cookie') || ''
    });

    // arXiv 入库
    async function ingestArxiv(onSuccess) {
        if (!arxivInput.value.trim()) return;
        ingesting.value = true;
        try {
            await IngestAPI.arxiv(arxivInput.value);
            ElementPlus.ElMessage.success('入库成功！');
            arxivInput.value = '';
            if (onSuccess) onSuccess();
        } catch (e) {
            const msg = e.response?.data?.error || '入库失败';
            ElementPlus.ElMessage.error(msg);
        } finally {
            ingesting.value = false;
        }
    }

    // 微信入库
    async function ingestWechat(onSuccess) {
        if (!wechatUrl.value.trim()) return;
        wechatIngesting.value = true;
        try {
            await IngestAPI.wechat(wechatUrl.value, wechatExtractOnly.value);
            ElementPlus.ElMessage.success('公众号文章入库成功！');
            wechatUrl.value = '';
            if (onSuccess) onSuccess();
        } catch (e) {
            const msg = e.response?.data?.error || '入库失败';
            ElementPlus.ElMessage.error(msg);
        } finally {
            wechatIngesting.value = false;
        }
    }

    // 文件上传
    function handleFileChange(file, fileList) {
        uploadFiles.value = fileList;
    }

    function handleFileRemove(file, fileList) {
        uploadFiles.value = fileList;
    }

    function handleUploadSuccess(response, onSuccess) {
        uploading.value = false;
        uploadFiles.value = [];
        if (uploadRef.value) {
            uploadRef.value.clearFiles();
        }
        ElementPlus.ElMessage.success(response.message);
        if (onSuccess) onSuccess();
    }

    function handleUploadError(error) {
        uploading.value = false;
        ElementPlus.ElMessage.error('上传失败: ' + (error.message || '未知错误'));
    }

    function startUpload() {
        if (uploadFiles.value.length === 0) return;
        uploading.value = true;
        uploadRef.value.submit();
    }

    function clearUpload() {
        uploadFiles.value = [];
        if (uploadRef.value) {
            uploadRef.value.clearFiles();
        }
    }

    // 笔记导入
    async function ingestNote(onSuccess) {
        let actualTitle = noteForm.value.title.trim();
        if (!actualTitle && noteForm.value.content.trim()) {
            actualTitle = extractTitleFromContent(noteForm.value.content);
        }
        if (!actualTitle) {
            ElementPlus.ElMessage.warning('请输入标题或正文内容');
            return;
        }

        let actualSource = noteForm.value.source;
        if (actualSource === '其他' && customSource.value.trim()) {
            actualSource = customSource.value.trim();
        }
        if (!actualSource || actualSource === '其他') {
            ElementPlus.ElMessage.warning('请选择或输入来源');
            return;
        }
        if (!noteForm.value.content.trim()) {
            ElementPlus.ElMessage.warning('请输入正文内容');
            return;
        }

        noteIngesting.value = true;
        try {
            const submitData = {
                ...noteForm.value,
                title: actualTitle,
                source: actualSource
            };
            await IngestAPI.note(submitData);
            ElementPlus.ElMessage.success('笔记导入成功！');
            clearNoteForm();
            if (onSuccess) onSuccess();
        } catch (e) {
            const msg = e.response?.data?.error || '导入失败';
            ElementPlus.ElMessage.error(msg);
        } finally {
            noteIngesting.value = false;
        }
    }

    function addCustomSource() {
        if (customSource.value.trim() && !noteSources.value.includes(customSource.value.trim())) {
            noteSources.value.splice(noteSources.value.length - 1, 0, customSource.value.trim());
            noteForm.value.source = customSource.value.trim();
            customSource.value = '';
        }
    }

    function clearNoteForm() {
        noteForm.value = {
            title: '',
            source: '豆包',
            created_at: getCurrentDateTime(),
            content: ''
        };
        customSource.value = '';
    }

    // 知乎导入
    async function ingestZhihuManual(onSuccess) {
        let actualTitle = zhihuForm.value.title.trim();
        if (!actualTitle && zhihuForm.value.content.trim()) {
            actualTitle = extractTitleFromContent(zhihuForm.value.content);
        }
        if (!actualTitle) {
            ElementPlus.ElMessage.warning('请输入标题或正文内容');
            return;
        }
        if (!zhihuForm.value.content.trim()) {
            ElementPlus.ElMessage.warning('请粘贴知乎文章内容');
            return;
        }

        zhihuIngesting.value = true;
        try {
            const submitData = {
                ...zhihuForm.value,
                title: actualTitle
            };
            await IngestAPI.zhihu(submitData);
            ElementPlus.ElMessage.success('知乎文章导入成功！');
            clearZhihuForm();
            if (onSuccess) onSuccess();
        } catch (e) {
            const msg = e.response?.data?.error || '导入失败';
            ElementPlus.ElMessage.error(msg);
        } finally {
            zhihuIngesting.value = false;
        }
    }

    async function ingestZhihuUrl(onSuccess) {
        if (!zhihuUrlForm.value.url.trim()) {
            ElementPlus.ElMessage.warning('请输入知乎文章链接');
            return;
        }
        if (!zhihuUrlForm.value.cookie.trim()) {
            ElementPlus.ElMessage.warning('请输入知乎 Cookie');
            return;
        }

        localStorage.setItem('zhihu_cookie', zhihuUrlForm.value.cookie);
        zhihuIngesting.value = true;
        try {
            await IngestAPI.zhihu(zhihuUrlForm.value);
            ElementPlus.ElMessage.success('知乎文章自动解析并导入成功！');
            zhihuUrlForm.value.url = '';
            if (onSuccess) onSuccess();
        } catch (e) {
            const msg = e.response?.data?.error || '导入失败，请检查 Cookie 是否有效';
            ElementPlus.ElMessage.error(msg);
        } finally {
            zhihuIngesting.value = false;
        }
    }

    function clearZhihuForm() {
        zhihuForm.value = {
            title: '',
            author: '',
            created_at: getCurrentDateTime(),
            content: ''
        };
    }

    function clearZhihuUrlForm() {
        zhihuUrlForm.value = {
            url: '',
            cookie: zhihuUrlForm.value.cookie
        };
    }

    return {
        // 导航
        ingestTab,
        // arXiv
        arxivInput, ingesting, ingestArxiv,
        // 微信
        wechatUrl, wechatIngesting, wechatContent, wechatExtractOnly, ingestWechat,
        // 文件上传
        uploadRef, uploadFiles, uploading,
        handleFileChange, handleFileRemove, handleUploadSuccess, handleUploadError,
        startUpload, clearUpload,
        // 笔记
        noteIngesting, noteSources, customSource, noteForm,
        ingestNote, addCustomSource, clearNoteForm,
        // 知乎
        zhihuMode, zhihuIngesting, zhihuForm, zhihuUrlForm,
        ingestZhihuManual, ingestZhihuUrl, clearZhihuForm, clearZhihuUrlForm
    };
}
