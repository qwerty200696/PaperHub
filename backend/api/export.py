"""
Export API - 数据导出功能
支持 JSON/CSV/Markdown 格式导出
"""
from flask import Blueprint, jsonify, request, send_file
import json
import csv
import io
import os
from datetime import datetime
import tempfile
import zipfile

try:
    from backend.models import Paper, Article, Note, Tag
except ImportError:
    from models import Paper, Article, Note, Tag

bp = Blueprint('export', __name__)


def get_db_session():
    """获取数据库会话"""
    try:
        from backend.config import get_session
        return get_session()
    except ImportError:
        from config import get_session
        return get_session()


def cleanup_temp_file(path):
    """清理临时文件"""
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass


@bp.route('/export/json', methods=['POST'])
def export_json():
    """
    导出为 JSON 格式

    请求体（可选）:
    {
        "types": ["papers", "articles", "notes"],  // 要导出的数据类型
        "include_tags": true,  // 是否包含标签信息
        "include_content": true  // 是否包含完整内容
    }

    返回: JSON 文件下载
    """
    tmp_path = None
    try:
        session = get_db_session()
        data = request.get_json(silent=True) or {}

        types_to_export = data.get('types', ['papers', 'articles', 'notes'])
        include_tags = data.get('include_tags', True)

        export_data = {}
        total_counts = {}

        if 'papers' in types_to_export:
            papers = session.query(Paper).all()
            export_data['papers'] = [paper.to_dict(
                include_tags=include_tags,
                include_articles=False,
                include_notes=False
            ) for paper in papers]
            total_counts['papers'] = len(export_data['papers'])

        if 'articles' in types_to_export:
            articles = session.query(Article).filter_by(is_deleted=False).all()
            export_data['articles'] = [article.to_dict(
                include_tags=include_tags,
                include_papers=False,
                include_notes=False
            ) for article in articles]
            total_counts['articles'] = len(export_data['articles'])

        if 'notes' in types_to_export:
            notes = session.query(Note).filter_by(is_deleted=False).all()
            export_data['notes'] = [note.to_dict(
                include_tags=include_tags,
                include_papers=False,
                include_articles=False
            ) for note in notes]
            total_counts['notes'] = len(export_data['notes'])

        if not any(total_counts.values()):
            return jsonify({'error': '没有数据可导出'}), 404

        # 添加元数据
        export_data['metadata'] = {
            'export_time': datetime.now().isoformat(),
            'version': '1.0',
            'total_items': total_counts
        }

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as tmp_file:
            json.dump(export_data, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = tmp_file.name

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"paperhub_export_{timestamp}.json"

        response = send_file(
            tmp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )

        # 使用 call_on_close 在响应发送后清理临时文件
        @response.call_on_close
        def cleanup():
            cleanup_temp_file(tmp_path)

        return response

    except Exception as e:
        cleanup_temp_file(tmp_path)
        return jsonify({'error': str(e)}), 500


@bp.route('/export/csv', methods=['POST'])
def export_csv():
    """
    导出为 CSV 格式

    请求体（可选）:
    {
        "type": "papers",  // 要导出的数据类型: papers/articles/notes
        "fields": ["title", "authors", "abstract"]  // 要导出的字段
    }

    返回: CSV 文件下载
    """
    tmp_path = None
    try:
        session = get_db_session()
        data = request.get_json(silent=True) or {}

        export_type = data.get('type', 'papers')
        fields = data.get('fields', None)

        output = io.StringIO()
        writer = None

        if export_type == 'papers':
            papers = session.query(Paper).all()
            if not papers:
                return jsonify({'error': '没有论文数据可导出'}), 404

            default_fields = [
                'id', 'title', 'authors', 'abstract', 'source',
                'category_l1', 'category_l2', 'status', 'starred',
                'published_at', 'created_at'
            ]
            selected_fields = fields or default_fields

            writer = csv.DictWriter(output, fieldnames=selected_fields)
            writer.writeheader()

            for paper in papers:
                row = {}
                for field in selected_fields:
                    value = getattr(paper, field, None)
                    if isinstance(value, list):
                        value = '; '.join(value) if value else ''
                    elif hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row[field] = value if value is not None else ''
                writer.writerow(row)

        elif export_type == 'articles':
            articles = session.query(Article).filter_by(is_deleted=False).all()
            if not articles:
                return jsonify({'error': '没有文章数据可导出'}), 404

            default_fields = [
                'id', 'title', 'author', 'source', 'url',
                'status', 'starred', 'published_at', 'created_at'
            ]
            selected_fields = fields or default_fields

            writer = csv.DictWriter(output, fieldnames=selected_fields)
            writer.writeheader()

            for article in articles:
                row = {}
                for field in selected_fields:
                    value = getattr(article, field, None)
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row[field] = value if value is not None else ''
                writer.writerow(row)

        elif export_type == 'notes':
            notes = session.query(Note).filter_by(is_deleted=False).all()
            if not notes:
                return jsonify({'error': '没有笔记数据可导出'}), 404

            default_fields = [
                'id', 'title', 'source', 'url', 'status',
                'starred', 'pinned', 'created_at', 'updated_at'
            ]
            selected_fields = fields or default_fields

            writer = csv.DictWriter(output, fieldnames=selected_fields)
            writer.writeheader()

            for note in notes:
                row = {}
                for field in selected_fields:
                    value = getattr(note, field, None)
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row[field] = value if value is not None else ''
                writer.writerow(row)
        else:
            return jsonify({'error': f'不支持的导出类型: {export_type}'}), 400

        # 创建临时文件（使用 utf-8-sig 确保 Excel 正确识别中文）
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False, encoding='utf-8-sig'
        ) as tmp_file:
            tmp_file.write(output.getvalue())
            tmp_path = tmp_file.name

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"paperhub_{export_type}_{timestamp}.csv"

        response = send_file(
            tmp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv; charset=utf-8-sig'
        )

        @response.call_on_close
        def cleanup():
            cleanup_temp_file(tmp_path)

        return response

    except Exception as e:
        cleanup_temp_file(tmp_path)
        return jsonify({'error': str(e)}), 500


@bp.route('/export/markdown', methods=['POST'])
def export_markdown():
    """
    导出为 Markdown 格式

    请求体（可选）:
    {
        "types": ["papers", "articles", "notes"],  // 要导出的数据类型
        "separate_files": false  // 是否分离为多个文件
    }

    返回: ZIP 文件或单个 Markdown 文件
    """
    tmp_path = None
    try:
        session = get_db_session()
        data = request.get_json(silent=True) or {}

        types_to_export = data.get('types', ['papers', 'articles', 'notes'])
        separate_files = data.get('separate_files', False)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if separate_files:
            # 创建ZIP文件，包含多个Markdown文件
            zip_buffer = io.BytesIO()
            has_data = False

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if 'papers' in types_to_export:
                    papers = session.query(Paper).all()
                    if papers:
                        has_data = True
                        md_content = generate_papers_markdown(papers)
                        zip_file.writestr(f'papers_{timestamp}.md', md_content)

                if 'articles' in types_to_export:
                    articles = session.query(Article).filter_by(is_deleted=False).all()
                    if articles:
                        has_data = True
                        md_content = generate_articles_markdown(articles)
                        zip_file.writestr(f'articles_{timestamp}.md', md_content)

                if 'notes' in types_to_export:
                    notes = session.query(Note).filter_by(is_deleted=False).all()
                    if notes:
                        has_data = True
                        md_content = generate_notes_markdown(notes)
                        zip_file.writestr(f'notes_{timestamp}.md', md_content)

                if not has_data:
                    return jsonify({'error': '没有数据可导出'}), 404

                # 添加README
                readme_content = generate_export_readme(types_to_export, timestamp)
                zip_file.writestr('README.md', readme_content)

            zip_buffer.seek(0)
            filename = f"paperhub_markdown_{timestamp}.zip"

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
        else:
            # 生成单个Markdown文件
            md_parts = []
            has_data = False

            if 'papers' in types_to_export:
                papers = session.query(Paper).all()
                if papers:
                    has_data = True
                    md_parts.append(generate_papers_markdown(papers))

            if 'articles' in types_to_export:
                articles = session.query(Article).filter_by(is_deleted=False).all()
                if articles:
                    has_data = True
                    md_parts.append(generate_articles_markdown(articles))

            if 'notes' in types_to_export:
                notes = session.query(Note).filter_by(is_deleted=False).all()
                if notes:
                    has_data = True
                    md_parts.append(generate_notes_markdown(notes))

            if not has_data:
                return jsonify({'error': '没有数据可导出'}), 404

            md_content = "# PaperHub 数据导出\n\n"
            md_content += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md_content += "---\n\n"
            md_content += "\n---\n\n".join(md_parts)

            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.md', delete=False, encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(md_content)
                tmp_path = tmp_file.name

            filename = f"paperhub_export_{timestamp}.md"

            response = send_file(
                tmp_path,
                as_attachment=True,
                download_name=filename,
                mimetype='text/markdown'
            )

            @response.call_on_close
            def cleanup():
                cleanup_temp_file(tmp_path)

            return response

    except Exception as e:
        cleanup_temp_file(tmp_path)
        return jsonify({'error': str(e)}), 500


def generate_papers_markdown(papers):
    """生成论文的Markdown内容"""
    md = "## 📚 论文列表\n\n"
    md += f"共 {len(papers)} 篇论文\n\n"

    for i, paper in enumerate(papers, 1):
        md += f"### {i}. {paper.title}\n\n"

        if paper.authors:
            try:
                authors = json.loads(paper.authors) if isinstance(paper.authors, str) else paper.authors
                if isinstance(authors, list):
                    md += f"**作者**: {'; '.join(authors)}\n\n"
                else:
                    md += f"**作者**: {authors}\n\n"
            except (json.JSONDecodeError, TypeError):
                md += f"**作者**: {paper.authors}\n\n"

        if paper.abstract:
            md += f"**摘要**:\n\n{paper.abstract}\n\n"

        if paper.url:
            md += f"**链接**: [{paper.url}]({paper.url})\n\n"

        if paper.source:
            md += f"**来源**: {paper.source}\n\n"

        if paper.category_l1:
            md += f"**分类**: {paper.category_l1}"
            if paper.category_l2:
                md += f" > {paper.category_l2}"
            md += "\n\n"

        if paper.published_at:
            md += f"**发表日期**: {paper.published_at}\n\n"

        if paper.tags:
            tag_names = [tag.name for tag in paper.tags]
            if tag_names:
                md += f"**标签**: {', '.join(tag_names)}\n\n"

        md += "---\n\n"

    return md


def generate_articles_markdown(articles):
    """生成文章的Markdown内容"""
    md = "## 📰 文章列表\n\n"
    md += f"共 {len(articles)} 篇文章\n\n"

    for i, article in enumerate(articles, 1):
        md += f"### {i}. {article.title}\n\n"

        if article.author:
            md += f"**作者**: {article.author}\n\n"

        if article.content:
            content_preview = article.content[:500] + "..." if len(article.content) > 500 else article.content
            md += f"**内容预览**:\n\n{content_preview}\n\n"

        if article.url:
            md += f"**链接**: [{article.url}]({article.url})\n\n"

        if article.source:
            md += f"**来源**: {article.source}\n\n"

        if article.published_at:
            md += f"**发表日期**: {article.published_at}\n\n"

        if article.tags:
            tag_names = [tag.name for tag in article.tags]
            if tag_names:
                md += f"**标签**: {', '.join(tag_names)}\n\n"

        md += "---\n\n"

    return md


def generate_notes_markdown(notes):
    """生成笔记的Markdown内容"""
    md = "## 📝 笔记列表\n\n"
    md += f"共 {len(notes)} 条笔记\n\n"

    for i, note in enumerate(notes, 1):
        title = note.title or f"笔记 {i}"
        md += f"### {i}. {title}\n\n"

        if note.content:
            md += f"{note.content}\n\n"

        if note.url:
            md += f"**相关链接**: [{note.url}]({note.url})\n\n"

        if note.source:
            md += f"**来源**: {note.source}\n\n"

        if note.created_at:
            md += f"**创建时间**: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if note.tags:
            tag_names = [tag.name for tag in note.tags]
            if tag_names:
                md += f"**标签**: {', '.join(tag_names)}\n\n"

        md += "---\n\n"

    return md


def generate_export_readme(types, timestamp):
    """生成导出说明文档"""
    md = "# PaperHub 数据导出说明\n\n"
    md += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += f"**导出类型**: {', '.join(types)}\n\n"
    md += "---\n\n"

    md += "## 文件说明\n\n"

    if 'papers' in types:
        md += f"- `papers_{timestamp}.md` - 论文数据\n"
    if 'articles' in types:
        md += f"- `articles_{timestamp}.md` - 文章数据\n"
    if 'notes' in types:
        md += f"- `notes_{timestamp}.md` - 笔记数据\n"

    md += "\n## 使用建议\n\n"
    md += "- 可以直接在支持Markdown的编辑器中查看\n"
    md += "- 可以导入到Notion、Obsidian等笔记工具\n"
    md += "- 可以使用Pandoc转换为其他格式\n"

    return md
