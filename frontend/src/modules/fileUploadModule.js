// 文件上传模块
// PDF/HTML 文件上传处理

export function createFileUploadModule({ Vue, ElementPlus, axios, refs }) {
    const { ref, computed } = Vue;

    const { uploadFiles, uploading, uploadRef, pdfSourceUrl, activeMenu, loadPapers, loadAllNotes, loadAllArticles } = refs;

    function handleFileChange(file, fileList) {
        uploadFiles.value = fileList;
    }

    function handleFileRemove(file, fileList) {
        uploadFiles.value = fileList;
    }

    function handleUploadSuccess(response) {
        uploading.value = false;
        uploadFiles.value = [];
        if (uploadRef.value) {
            uploadRef.value.clearFiles();
        }
        ElementPlus.ElMessage.success(response.message);

        // 判断是否有导入到笔记库/文章库的内容
        const hasNotes = response.results?.some(r => r.note_id);
        const hasArticles = response.results?.some(r => r.article_id);
        const hasPapers = response.results?.some(r => r.paper_id);

        if (hasArticles && !hasNotes && !hasPapers) {
            // 只导入了文章（微信公众号HTML）
            activeMenu.value = 'articles';
            loadAllArticles();
        } else if (hasNotes && !hasArticles && !hasPapers) {
            // 只导入了笔记
            activeMenu.value = 'notes';
            loadAllNotes();
        } else if (hasPapers && !hasNotes && !hasArticles) {
            // 只导入了论文
            activeMenu.value = 'library';
            loadPapers();
        } else {
            // 都有，默认跳转到论文库
            activeMenu.value = 'library';
            loadPapers();
            loadAllNotes();
            loadAllArticles();
        }
    }

    function handleUploadError(error) {
        uploading.value = false;
        ElementPlus.ElMessage.error('上传失败: ' + (error.message || '未知错误'));
    }

    async function startUpload() {
        if (uploadFiles.value.length === 0) return;
        uploading.value = true;

        const pdfUrl = pdfSourceUrl.value?.trim();

        if (pdfUrl) {
            try {
                const formData = new FormData();
                for (const fileItem of uploadFiles.value) {
                    formData.append('file', fileItem.raw);
                }
                if (pdfUrl) {
                    formData.append('pdf_url', pdfUrl);
                }

                const response = await axios.post('/api/ingest/pdf', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
                handleUploadSuccess(response.data);
                return;
            } catch (error) {
                handleUploadError(error);
                return;
            }
        }

        uploadRef.value.submit();
    }

    function clearUpload() {
        uploadFiles.value = [];
        pdfSourceUrl.value = '';
        if (uploadRef.value) {
            uploadRef.value.clearFiles();
        }
    }

    function getCurrentDateTime() {
        return new Date().toISOString().slice(0, 16);
    }

    return {
        handleFileChange,
        handleFileRemove,
        handleUploadSuccess,
        handleUploadError,
        startUpload,
        clearUpload,
        getCurrentDateTime
    };
}
