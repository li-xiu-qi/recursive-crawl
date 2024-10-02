import json
import logging
import os
from copy import deepcopy
from datetime import datetime
from json import JSONDecodeError
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from custom_markdown_convert import html2md

logger = logging.getLogger(__name__)

# 定义日志文件路径
log_file_path = 'file_handlers_log.log'

# 配置日志记录器
logging.basicConfig(
    level=logging.ERROR,  # 设置日志级别，这里是DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.FileHandler(log_file_path),  # 将日志输出到文件
        logging.StreamHandler()  # 同时保留控制台输出
    ]
)
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}


def fetch_page(url: str) -> Optional[str]:
    """获取页面内容"""
    try:
        logger.debug(f'正在爬取: {url}')
        response = session.get(url, headers=headers, timeout=2)
        response.encoding = response.apparent_encoding
        if 'text/html' in response.headers.get('Content-Type', ''):
            return response.text
        else:
            logger.info(f'❌ 内容不是 text/html: {url}')
            return None
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        logger.error(f'❌ 请求错误: {url}: {e}')
        return None


def extract_content(soup: BeautifulSoup, target_area_content_tags: List[str]) -> str:
    """
    提取BeautifulSoup对象中多个特定标签的内容，并拼接成一个新的HTML字符串

    :param soup: BeautifulSoup, 原始的BeautifulSoup对象
    :param target_tags: List[str], 目标标签名称列表
    :return: str, 包含提取内容的新的HTML字符串
    """
    if not target_area_content_tags:
        return str(soup)
    new_soup = BeautifulSoup('<html><head><meta charset="utf-8"></head><body></body></html>', 'html.parser')
    soup_copy = deepcopy(soup)
    extracted_tags = set()
    for tag_name in target_area_content_tags:
        if tag_name not in extracted_tags:
            tags = soup_copy.find_all(tag_name)
            for tag in tags:
                new_soup.body.append(tag)
            extracted_tags.add(tag_name)
    return str(new_soup)


def extract_common_file_urls(links: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """提取常见文件链接"""
    common_file_extensions = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.7z',
        '.txt', '.rtf', '.md', '.xml', '.csv', '.json', '.log', '.ini', '.cfg', '.yaml', '.yml'
    ]
    return [(link, title) for link, title in links if any(link.lower().endswith(ext) for ext in common_file_extensions)]


def record_page_info(url: str, file_path: str, file_links: dict, output_json_file: str) -> None:
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    """记录页面信息到JSON文件，避免重复URL，如存在则更新信息"""

    page_info = {
        'url': url,
        'file_path': file_path,
        'file_links': file_links,
        "date": date,
    }

    if os.path.exists(output_json_file):
        try:
            with open(output_json_file, 'r') as json_file:
                existing_data = json.load(json_file)
        except JSONDecodeError:
            existing_data = []

        updated = False
        for index, entry in enumerate(existing_data):
            if entry['url'] == url:
                existing_data[index].update(page_info)
                updated = True
                break
        if not updated:
            existing_data.append(page_info)

        with open(output_json_file, 'w') as json_file:
            json.dump(existing_data, json_file, indent=2, ensure_ascii=False)
    else:
        with open(output_json_file, 'w') as json_file:
            json.dump([page_info], json_file, indent=2, ensure_ascii=False)


# 全局变量存储文件类型
FILE_TYPES = {}


def load_file_types():
    """加载文件类型"""
    global FILE_TYPES
    if FILE_TYPES:
        return
    with open('file_types.json', 'r') as file:
        FILE_TYPES = json.load(file)


def download_files(file_urls: List[Tuple[str, str]], download_dir: str, already_downloaded: set) -> None:
    """下载文件并分类"""
    load_file_types()
    dir_path = os.path.join(os.path.dirname(__file__), download_dir)
    os.makedirs(dir_path, exist_ok=True)

    for file_url, file_name in file_urls:
        if file_url not in already_downloaded:
            # 从 URL 中提取文件后缀
            file_ext = file_url.split('.')[-1].split('?')[0].lower()
            file_category = FILE_TYPES.get(file_ext, '其他文件')
            file_path = os.path.join(download_dir, file_category, f"{file_name}.{file_ext}")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            try:
                response = session.get(file_url, headers=headers)
                response.raise_for_status()
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                logger.info(f'📥 下载文件: {file_name}.{file_ext}')
            except requests.RequestException as e:
                logger.error(f'❌ 文件下载失败: {file_name}.{file_ext} - {e}')


def extract_url_title_name(url: str, soup: BeautifulSoup) -> str:
    """
    优化地从URL和页面标题中提取更规范的文件名。

    1. 使用URL的路径部分来推测文件名，如果存在。
    2. 如果没有路径或路径不包含有意义的文件名信息，则使用页面标题。
    3. 清理标题，移除特殊字符并转换为空格，然后替换空格为短横线。
    4. 确保文件名不以短横线开头或结尾。
    """

    # 获取页面标题并清理
    title = soup.title.string.strip("/") if soup.title else "Untitled"

    parsed_url = urlparse(url)
    path = parsed_url.path

    if path:

        filename_from_path = path.replace("/", "_")
        file_name = f"{title}-{filename_from_path}"
    else:
        file_name = title

    file_name = file_name.strip('/')

    return file_name


def save_content(file_path: str, content: str, filter_tags: List[str]) -> None:
    """保存内容到Markdown文件"""
    if content:
        strip_elements = ['img']
        strip_elements.extend(filter_tags)
        output = html2md(content, strip=strip_elements)
        logger.info(f'创建 📝 {file_path.split("/")[-1]}')

        with open(file_path, 'w') as f:
            f.write(output)
    else:
        logger.error(f'❌ 空内容: {file_path}. 请检查目标元素，跳过。')
