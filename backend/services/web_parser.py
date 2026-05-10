import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class UniversalWebParser:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_html(self, url: str) -> Tuple[str, str]:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return resp.text, str(resp.url)
        except Exception as e:
            logger.error(f"获取网页失败: {e}")
            raise

    def extract_with_trafilatura(self, html: str, url: str) -> Dict:
        try:
            import trafilatura
            result = {}
            extracted = trafilatura.extract(
                html,
                url=url,
                output_format='json',
                include_images=True,
                include_links=True
            )
            if extracted:
                import json
                data = json.loads(extracted)
                result['title'] = data.get('title', '')
                result['author'] = data.get('author', '')
                result['date'] = data.get('date', '')
                result['text'] = data.get('text', '')
                result['html'] = data.get('html', '')
                result['plain_text'] = True
            return result
        except ImportError:
            logger.warning("trafilatura未安装")
            return {}
        except Exception as e:
            logger.warning(f"trafilatura提取失败: {e}")
            return {}

    def extract_with_readability(self, html: str) -> Dict:
        try:
            from readability import Document
            doc = Document(html)
            result = {}
            result['title'] = doc.short_title()
            result['html'] = doc.summary()
            result['text'] = BeautifulSoup(result['html'], 'lxml').get_text(strip=False, separator='\n')
            return result
        except ImportError:
            logger.warning("readability-lxml未安装")
            return {}
        except Exception as e:
            logger.warning(f"readability提取失败: {e}")
            return {}

    def extract_with_newspaper(self, url: str) -> Dict:
        try:
            from newspaper import Article
            article = Article(url)
            article.download()
            article.parse()
            result = {
                'title': article.title,
                'author': ', '.join(article.authors),
                'publish_date': str(article.publish_date) if article.publish_date else '',
                'text': article.text,
                'top_image': article.top_image,
                'images': list(article.images)
            }
            if article.meta_description:
                result['summary'] = article.meta_description
            return result
        except ImportError:
            logger.warning("newspaper3k未安装")
            return {}
        except Exception as e:
            logger.warning(f"newspaper提取失败: {e}")
            return {}

    def extract_with_bs4(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'lxml')
        result = {}
        title_tag = soup.find('title')
        result['title'] = title_tag.get_text(strip=True) if title_tag else ''
        
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()
        
        paragraphs = soup.find_all('p')
        main_text = '\n\n'.join([p.get_text(strip=False) for p in paragraphs if len(p.get_text(strip=True)) > 50])
        result['text'] = main_text
        result['plain_text'] = True
        return result

    def extract_article(self, url: str, preferred_method: str = 'auto') -> Dict:
        final_result = {
            'url': url,
            'success': False,
            'methods_used': []
        }

        try:
            html, final_url = self.fetch_html(url)
            final_result['resolved_url'] = final_url
            final_result['raw_html_length'] = len(html)

            methods = []
            if preferred_method == 'auto':
                methods = ['trafilatura', 'readability', 'newspaper', 'bs4']
            else:
                methods = [preferred_method, 'trafilatura', 'readability', 'bs4']

            best_text = ''
            best_title = ''
            best_method = ''

            for method in methods:
                current_result = {}
                try:
                    if method == 'trafilatura':
                        current_result = self.extract_with_trafilatura(html, final_url)
                    elif method == 'readability':
                        current_result = self.extract_with_readability(html)
                    elif method == 'newspaper':
                        current_result = self.extract_with_newspaper(final_url)
                    elif method == 'bs4':
                        current_result = self.extract_with_bs4(html)

                    if current_result.get('text') and len(current_result['text']) > len(best_text):
                        best_text = current_result['text']
                        best_title = current_result.get('title', '')
                        best_method = method
                        final_result.update(current_result)

                    final_result['methods_used'].append(method)
                except Exception as e:
                    logger.warning(f"方法 {method} 出错: {e}")
                    continue

            final_result['text'] = best_text
            final_result['title'] = best_title
            final_result['best_method'] = best_method
            final_result['success'] = len(best_text) > 0
            final_result['text_length'] = len(best_text)

            return final_result

        except Exception as e:
            logger.error(f"提取网页正文完全失败: {e}")
            final_result['error'] = str(e)
            return final_result

    def save_complete_page(self, url: str, output_dir: Path) -> Dict:
        result = {
            'url': url,
            'success': False
        }
        try:
            html, _ = self.fetch_html(url)
            output_dir.mkdir(parents=True, exist_ok=True)
            parsed = urllib.parse.urlparse(url)
            safe_name = re.sub(r'[^\w\-.]', '_', parsed.netloc + parsed.path)
            if not safe_name.endswith('.html'):
                safe_name += '.html'
            html_path = output_dir / safe_name

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)

            result['saved_path'] = str(html_path)
            result['size_bytes'] = len(html.encode('utf-8'))
            result['success'] = True
            return result
        except Exception as e:
            logger.error(f"保存网页失败: {e}")
            result['error'] = str(e)
            return result
