"""
微信读书 API - 微信读书搜索相关 API
"""
import os
import requests
from flask import Blueprint, jsonify, request, send_file

bp = Blueprint('weread', __name__)

API_BASE_URL = "https://i.weread.qq.com/api/agent/gateway"
SKILL_VERSION = "1.0.3"
COVER_CACHE_DIR = "/tmp/weread_covers"

# 确保封面缓存目录存在
os.makedirs(COVER_CACHE_DIR, exist_ok=True)


def _make_api_call(payload, api_key):
    """调用微信读书 API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(API_BASE_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _get_hd_cover_url(cover_url):
    """将微信读书封面 URL 转换为 CDN 高清版本
    
    API 返回的 cover_url 格式如:
      /wrepub/695233/t6_695233.jpg  (70x101 缩略图)
    
    高清图在 CDN 上，格式如:
      https://cdn.weread.qq.com/weread/cover/80/yuewen_695233/t7_yuewen_6952331740758482.jpg
    
    策略:
      1. 如果 cover_url 已经是 CDN 链接，尝试把 t6 换成 t7 获取高清版
      2. 从 API 返回的 cover_url 提取 bookId，构造 CDN URL
      3. 如果构造失败，回退到原图
    """
    if not cover_url:
        return None
    
    # 如果已经是 CDN 链接，尝试升级 t6 -> t7
    if 'cdn.weread.qq.com' in cover_url:
        if 't6_' in cover_url:
            return cover_url.replace('t6_', 't7_')
        return cover_url
    
    # 提取 bookId
    book_id = None
    parts = cover_url.split('/')
    for part in parts:
        if part.isdigit():
            book_id = part
            break
    
    if not book_id:
        return cover_url if cover_url.startswith('http') else f"https://weread.qq.com{cover_url}"
    
    # 尝试构造 CDN 高清 URL
    # hash_prefix 是 bookId 的后两位
    hash_prefix = book_id[-2:] if len(book_id) >= 2 else book_id
    
    # 尝试 t7 高清版本 (285x411)
    hd_url = f"https://cdn.weread.qq.com/weread/cover/{hash_prefix}/yuewen_{book_id}/t7_yuewen_{book_id}.jpg"
    
    return hd_url


def _fetch_hd_cover_from_web(book_id, book_title=None):
    """从微信读书网页搜索获取真实的高清封面 URL
    
    网页搜索结果中包含 CDN 封面 URL，格式如:
      https://cdn.weread.qq.com/weread/cover/80/yuewen_695233/t7_yuewen_6952331740758482.jpg
    
    HTML中可能有两种格式:
      1. 正常格式: <img src="https://cdn.weread.qq.com/.../t6_xxx.jpg">
      2. JSON转义格式: https:\u002F\u002Fcdn.weread.qq.com\u002F...\u002Fs_xxx.jpg
    
    注意: 用 bookId 搜索时微信读书可能不返回结果，需要用中文书名搜索
    
    返回: 高清封面 URL 或 None
    """
    if not book_id:
        return None
    
    try:
        import re
        import urllib.parse
        
        # 尝试用书名搜索（更可靠）
        search_keywords = []
        if book_title:
            search_keywords.append(urllib.parse.quote(book_title))
        search_keywords.append(book_id)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for keyword in search_keywords:
            search_url = f"https://weread.qq.com/web/search/books?keyword={keyword}"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue
                
            html = response.text
            
            # 策略1: 匹配正常 HTML img src 中的 t6 URL
            # 如: <img src="https://cdn.weread.qq.com/.../t6_xxx.jpg">
            pattern1 = r'https://cdn\.weread\.qq\.com/weread/cover/\d+/[^"]+_' + re.escape(str(book_id)) + r'/t6_[^"]+\.jpg'
            matches1 = re.findall(pattern1, html)
            if matches1:
                # t6 -> t7 获取高清版
                return matches1[0].replace('t6_', 't7_')
            
            # 策略2: 匹配 JSON 中的转义格式 (\u002F 是转义的 /)
            # 先解码转义字符
            decoded_html = html.replace('\\u002F', '/')
            pattern2 = r'https://cdn\.weread\.qq\.com/weread/cover/\d+/[^"]+_' + re.escape(str(book_id)) + r'/s_[^"]+\.jpg'
            matches2 = re.findall(pattern2, decoded_html)
            if matches2:
                # s_ 是小图，构造 t7 高清版 URL
                return matches2[0].replace('s_', 't7_')
            
            # 策略3: 也尝试匹配 t7 版本
            pattern3 = r'https://cdn\.weread\.qq\.com/weread/cover/\d+/[^"]+_' + re.escape(str(book_id)) + r'/t7_[^"]+\.jpg'
            matches3 = re.findall(pattern3, html)
            if matches3:
                return matches3[0]
    except Exception as e:
        print(f"[weread] 从网页获取高清封面失败: {e}")
    
    return None


def _download_cover(cover_url, book_id, book_title=None):
    """下载书籍封面到 /tmp/weread_covers/"""
    if not cover_url:
        return None
    
    ext = '.jpg'
    if '.' in cover_url.split('/')[-1]:
        ext = '.' + cover_url.split('.')[-1].split('?')[0]
    
    local_path = os.path.join(COVER_CACHE_DIR, f"{book_id}{ext}")
    
    if os.path.exists(local_path):
        return f"/api/weread/cover/{book_id}{ext}"
    
    try:
        # 策略1: 尝试从网页搜索获取真实高清封面 URL（传入书名提高成功率）
        web_hd_url = _fetch_hd_cover_from_web(book_id, book_title)
        if web_hd_url:
            try:
                response = requests.get(web_hd_url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' in content_type:
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        print(f"[weread] 从网页获取高清封面成功: {web_hd_url} ({len(response.content)} bytes)")
                        return f"/api/weread/cover/{book_id}{ext}"
            except Exception as e:
                print(f"[weread] 网页高清封面下载失败: {e}")
        
        # 策略2: 尝试构造 CDN 高清 URL
        hd_url = _get_hd_cover_url(cover_url)
        if hd_url:
            try:
                response = requests.get(hd_url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' in content_type:
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        print(f"[weread] 下载 CDN 高清封面成功: {hd_url} ({len(response.content)} bytes)")
                        return f"/api/weread/cover/{book_id}{ext}"
            except Exception as e:
                print(f"[weread] CDN 高清封面下载失败: {e}")
        
        # 策略3: 回退到原图 URL
        if cover_url.startswith('/'):
            cover_url = f"https://weread.qq.com{cover_url}"
        elif not cover_url.startswith('http'):
            cover_url = f"https://weread.qq.com/{cover_url}"
        
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"[weread] 下载原图封面成功: {cover_url} ({len(response.content)} bytes)")
        return f"/api/weread/cover/{book_id}{ext}"
    except Exception as e:
        print(f"[weread] 下载封面失败: {cover_url}, error: {e}")
        return None


@bp.route('/weread/cover/<path:filename>')
def serve_cover(filename):
    """提供封面图片"""
    file_path = os.path.join(COVER_CACHE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': '封面不存在'}), 404


@bp.route('/weread/test', methods=['POST'])
def test_api():
    """测试 API 连通性"""
    data = request.get_json()
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({'error': 'API Key 不能为空'}), 400
    
    try:
        result = _make_api_call({
            "api_name": "/store/search",
            "keyword": "三体",
            "scope": 10,
            "count": 1,
            "skill_version": SKILL_VERSION
        }, api_key)
        
        return jsonify({
            'status': 'ok',
            'response_keys': list(result.keys()),
            'has_error': result.get('errcode') is not None and result.get('errcode') != 0,
            'errcode': result.get('errcode'),
            'errmsg': result.get('errmsg'),
            'sample': str(result)[:500] if result else None
        })
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@bp.route('/weread/search', methods=['POST'])
def search_books():
    """搜索书籍"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    api_key = data.get('api_key', '')

    if not keyword:
        return jsonify({'error': '关键词不能为空'}), 400
    if not api_key:
        return jsonify({'error': 'API Key 不能为空'}), 400

    payload = {
        "api_name": "/store/search",
        "keyword": keyword,
        "scope": 10,
        "count": 10,
        "skill_version": SKILL_VERSION
    }

    try:
        result = _make_api_call(payload, api_key)
        
        if result.get("errcode") is not None and result.get("errcode") != 0:
            return jsonify({
                'error': result.get('errmsg', '未知错误'),
                'errcode': result.get('errcode', -1)
            }), 400

        books = []
        for result_group in result.get("results", []):
            group_title = result_group.get("title", "")
            group_scope = result_group.get("scope", 0)

            if group_title == "电子书" or group_scope in [10, 17]:
                for book in result_group.get("books", []):
                    book_info = book.get("bookInfo", {})
                    if not book_info:
                        book_info = book
                    
                    raw_rating = book_info.get("newRating", book.get("newRating", 0))
                    rating_count = book_info.get("newRatingCount", book.get("newRatingCount", 0))
                    reading_count = book.get("readingCount", 0)
                    book_id = book_info.get("bookId") or book.get("bookId", "")
                    cover_url = book_info.get("cover", book.get("cover", ""))
                    
                    # 下载封面（传入书名以便获取高清版）
                    book_title = book_info.get("title", book.get("title", ""))
                    local_cover = _download_cover(cover_url, book_id, book_title) if cover_url else None

                    books.append({
                        "bookId": book_id,
                        "title": book_title or "未知书名",
                        "author": book_info.get("author", book.get("author", "未知作者")),
                        "intro": book_info.get("intro", book.get("intro", "")),
                        "cover": local_cover or cover_url,
                        "rating": raw_rating // 10 if raw_rating > 100 else raw_rating,
                        "ratingCount": rating_count,
                        "readingCount": reading_count
                    })

        return jsonify({'books': books})

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'网络请求错误: {str(e)}'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/weread/detail', methods=['POST'])
def get_book_detail():
    """获取书籍详情（点评和热门划线）"""
    data = request.get_json()
    book_id = data.get('bookId', '')
    api_key = data.get('api_key', '')

    if not book_id:
        return jsonify({'error': 'bookId 不能为空'}), 400
    if not api_key:
        return jsonify({'error': 'API Key 不能为空'}), 400

    try:
        # 获取点评
        reviews_payload = {
            "api_name": "/review/list",
            "bookId": book_id,
            "reviewListType": 1,
            "count": 5,
            "skill_version": SKILL_VERSION
        }
        reviews_result = _make_api_call(reviews_payload, api_key)

        reviews = []
        if reviews_result.get("errcode") is None or reviews_result.get("errcode") == 0:
            for item in reviews_result.get("reviews", []):
                review_wrapper = item.get("review", {})
                review = review_wrapper.get("review", review_wrapper)

                star = int(review.get("star", 0))
                star_display = "⭐" * (star // 20) if star else ""

                author_info = review.get("author", {})
                author_name = author_info.get("name", "匿名用户")

                create_time = review.get("createTime", 0)
                create_time_str = ""
                if create_time > 0:
                    from datetime import datetime
                    try:
                        create_time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        create_time_str = str(create_time)

                reviews.append({
                    "reviewId": review_wrapper.get("reviewId", review.get("reviewId", "")),
                    "author": author_name,
                    "star": star_display,
                    "content": review.get("content", ""),
                    "createTime": create_time_str,
                    "likesCount": review_wrapper.get("likesCount", review.get("likesCount", ""))
                })

        # 获取热门划线
        highlights_payload = {
            "api_name": "/book/bestbookmarks",
            "bookId": book_id,
            "chapterUid": 0,
            "skill_version": SKILL_VERSION
        }
        highlights_result = _make_api_call(highlights_payload, api_key)

        highlights = []
        if highlights_result.get("errcode") is None or highlights_result.get("errcode") == 0:
            chapters_map = {}
            for chapter in highlights_result.get("chapters", []):
                chapters_map[chapter.get("chapterUid")] = chapter.get("title", "未知章节")

            for idx, item in enumerate(highlights_result.get("items", [])[:10], 1):
                chapter_uid = item.get("chapterUid", 0)
                chapter_title = chapters_map.get(chapter_uid, f"章节 {chapter_uid}")
                range_str = item.get("range", "")

                highlight_data = {
                    "bookmarkId": item.get("bookmarkId", ""),
                    "bookId": item.get("bookId", book_id),
                    "chapterUid": chapter_uid,
                    "chapterTitle": chapter_title,
                    "text": item.get("markText", ""),
                    "totalCount": item.get("totalCount", 0),
                    "range": range_str,
                    "top2Thoughts": []
                }

                # 获取划线的想法
                if range_str:
                    try:
                        thoughts_payload = {
                            "api_name": "/book/readreviews",
                            "bookId": book_id,
                            "chapterUid": chapter_uid,
                            "reviews": [{
                                "range": range_str,
                                "count": 2,
                                "maxIdx": 0
                            }],
                            "skill_version": SKILL_VERSION
                        }
                        thoughts_result = _make_api_call(thoughts_payload, api_key)

                        if thoughts_result.get("errcode") is None or thoughts_result.get("errcode") == 0:
                            thoughts = []
                            for review_group in thoughts_result.get("reviews", []):
                                for thought in review_group.get("pageReviews", []):
                                    thought_info = thought.get("review", {})

                                    create_time = thought_info.get("createTime", 0)
                                    create_time_str = ""
                                    if create_time > 0:
                                        from datetime import datetime
                                        try:
                                            create_time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                                        except:
                                            create_time_str = str(create_time)

                                    thoughts.append({
                                        "reviewId": thought_info.get("reviewId", ""),
                                        "author": thought_info.get("author", {}).get("name", "匿名用户"),
                                        "content": thought_info.get("content", ""),
                                        "createTime": create_time_str,
                                        "likesCount": thought.get("likesCount", thought_info.get("likesCount", 0))
                                    })

                            thoughts.sort(key=lambda x: x.get("likesCount", 0), reverse=True)
                            highlight_data["top2Thoughts"] = thoughts[:2]
                    except:
                        pass

                highlights.append(highlight_data)

        return jsonify({
            'reviews': reviews,
            'highlights': highlights
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'网络请求错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500