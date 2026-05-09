/**
 * 笔记编辑器模块
 * 封装笔记编辑相关的通用逻辑，支持粘贴图片上传
 */

export function createNoteEditorModule({ Vue, ElementPlus, axios, onNotesChange }) {
    const { ref, nextTick } = Vue

    const noteEditorVisible = ref(false)
    const noteEditorForm = ref({ title: '', content: '' })
    const editingNote = ref(null)
    const noteSaving = ref(false)
    const imageUploading = ref(false)

    /**
     * 显示笔记编辑器
     */
    function showNoteEditor(note) {
        if (note) {
            editingNote.value = note
            noteEditorForm.value = { title: note.title || '', content: note.content || '' }
        } else {
            editingNote.value = null
            noteEditorForm.value = { title: '', content: '' }
        }
        noteEditorVisible.value = true
        nextTick(() => {
            setTimeout(setupPasteHandler, 100)
        })
    }

    /**
     * 设置文本域粘贴图片处理器
     */
    function setupPasteHandler() {
        const textarea = document.querySelector('.el-dialog textarea')
        if (!textarea) return
        
        textarea.addEventListener('paste', async function(e) {
            if (!e.clipboardData) return
            const items = e.clipboardData.items
            for (let i = 0; i < items.length; i++) {
                const item = items[i]
                if (item.type.indexOf('image') !== -1) {
                    e.preventDefault()
                    const blob = item.getAsFile()
                    await uploadPastedImage(blob, textarea)
                    return
                }
            }
        })
    }

    /**
     * 上传粘贴的图片
     */
    async function uploadPastedImage(file, textarea) {
        if (imageUploading.value) {
            ElementPlus.ElMessage.warning('图片正在上传中，请稍候...')
            return
        }
        imageUploading.value = true
        try {
            ElementPlus.ElMessage.success('正在上传图片...')
            const formData = new FormData()
            formData.append('image', file, 'pasted_image.png')
            const res = await axios.post('/api/note-images/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            if (res.data.success) {
                const markdownImage = `![图片](${res.data.url})`
                const start = textarea.selectionStart
                const end = textarea.selectionEnd
                const oldContent = noteEditorForm.value.content
                noteEditorForm.value.content = 
                    oldContent.substring(0, start) + markdownImage + '\n' + oldContent.substring(end)
                nextTick(() => {
                    textarea.focus()
                    const newPos = start + markdownImage.length + 1
                    textarea.setSelectionRange(newPos, newPos)
                })
                ElementPlus.ElMessage.success('图片已插入')
            } else {
                ElementPlus.ElMessage.error('图片上传失败')
            }
        } catch (err) {
            ElementPlus.ElMessage.error('图片上传失败: ' + (err.response?.data?.error || err.message))
        } finally {
            imageUploading.value = false
        }
    }

    /**
     * 保存笔记
     */
    async function saveNote({ selectedPaper, loadPaperNotes, loadAllNotes }) {
        if (!noteEditorForm.value.content.trim()) {
            ElementPlus.ElMessage.warning('笔记内容不能为空')
            return
        }
        noteSaving.value = true
        try {
            if (editingNote.value) {
                await axios.put(`/api/notes/${editingNote.value.id}`, {
                    title: noteEditorForm.value.title,
                    content: noteEditorForm.value.content
                })
                ElementPlus.ElMessage.success('笔记已更新')
            } else {
                const payload = {
                    title: noteEditorForm.value.title,
                    content: noteEditorForm.value.content,
                    source: selectedPaper.value ? 'paper_note' : 'manual'
                }
                if (selectedPaper.value) {
                    payload.paper_ids = [selectedPaper.value.id]
                }
                const res = await axios.post('/api/notes', payload)
                if (res.data.duplicate) {
                    ElementPlus.ElMessage.warning('该笔记已存在，已自动跳转到现有笔记')
                } else {
                    ElementPlus.ElMessage.success('笔记已保存')
                }
            }
            noteEditorVisible.value = false
            if (loadPaperNotes) await loadPaperNotes()
            if (loadAllNotes) await loadAllNotes()
        } catch (e) {
            if (e.response?.status === 409 && e.response?.data?.duplicate) {
                ElementPlus.ElMessage.warning('该笔记已存在，无需重复添加')
                noteEditorVisible.value = false
            } else {
                ElementPlus.ElMessage.error('保存失败: ' + (e.response?.data?.error || e.message))
            }
        } finally {
            noteSaving.value = false
        }
    }

    /**
     * 删除笔记
     */
    async function deleteNote(noteId, { paperNotes, loadPaperNotes, loadAllNotes, viewingNote }) {
        try {
            await ElementPlus.ElMessageBox.confirm('确定要删除这条笔记吗？', '警告', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
            await axios.delete(`/api/notes/${noteId}`)
            ElementPlus.ElMessage.success('笔记已删除')
            if (loadPaperNotes) await loadPaperNotes()
            if (loadAllNotes) await loadAllNotes()
            if (viewingNote && viewingNote.value && viewingNote.value.id === noteId) {
                viewingNote.value = null
            }
        } catch (e) {
            if (e !== 'cancel') {
                ElementPlus.ElMessage.error('删除失败')
            }
        }
    }

    return {
        noteEditorVisible,
        noteEditorForm,
        editingNote,
        noteSaving,
        imageUploading,
        showNoteEditor,
        saveNote,
        deleteNote
    }
}

