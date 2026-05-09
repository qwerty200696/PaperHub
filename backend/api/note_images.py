"""
笔记图片上传 API
支持粘贴截图上传，保存到本地文件夹
"""
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify

try:
    from backend.config import NOTE_IMAGES_DIR
except ImportError:
    from config import NOTE_IMAGES_DIR

bp = Blueprint('note_images', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/api/note-images/upload', methods=['POST'])
def upload_note_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有找到图片文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        if not file:
            return jsonify({'error': '文件为空'}), 400
        
        ext = 'png'
        if file.filename and '.' in file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                ext = 'png'
        
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        save_path = NOTE_IMAGES_DIR / unique_filename
        
        file.save(str(save_path))
        
        return jsonify({
            'success': True,
            'url': f'/static/note_images/{unique_filename}',
            'filename': unique_filename
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
