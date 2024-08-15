import asyncio
import json
import logging
import os
from collections import deque
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

from utils import is_valid_url

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def fetch(session, url):
    """
    异步获取URL的内容。

    :param session: aiohttp.ClientSession 对象
    :param url: 目标URL
    :return: 返回的文本内容或None
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            # 尝试检测编码并使用正确的编码进行解码
            encoding = response.charset or 'utf-8'
            return await response.text(encoding=encoding, errors='ignore')
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching {url}: {e}")
        return None


async def get_links(session, url):
    """
    异步获取指定URL页面上的所有链接和标题。

    :param session: aiohttp.ClientSession 对象
    :param url: 目标URL
    :return: 包含链接和标题的字典列表
    """
    html_content = await fetch(session, url)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)
        parsed_url = urlparse(full_url)
        if parsed_url.netloc:
            title = a_tag.get_text(strip=True) or parsed_url.netloc
            links.append({
                'url': full_url,
                'title': title
            })
    return links


def save_results_to_json(results, dir_name, file_name):
    """
    保存爬取结果到JSON文件。

    :param results: 包含结果的列表
    :param dir_name: 目录名
    :param file_name: 文件名
    """
    if not os.path.exists(os.path.join(os.path.dirname(__file__), dir_name)):
        os.makedirs(os.path.join(os.path.dirname(__file__), dir_name), exist_ok=True)
    file_path = os.path.join(os.path.dirname(__file__), dir_name, file_name)
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logging.info(f"Results saved to {file_path}")


def is_within_domain(base_domain, url, domain_parts_count):
    """
    检查URL是否在指定域名内。

    :param base_domain: 基础域名
    :param url: 检查的URL
    :param domain_parts_count: 基础域名的组成部分数量
    :return: 布尔值
    """
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    domain_parts = netloc.split('.')[-domain_parts_count:]
    return base_domain == '.'.join(domain_parts)


async def crawl_domain(base_url, max_level=3, domain_parts_count=3, domains_json_path="domains.json", dir_name="data"):
    """
    异步递归爬取指定域名下的所有链接，并记录域名、级别和标题。

    :param base_url: 基础URL
    :param max_level: 最大递归级别
    :param domain_parts_count: 基础域名的组成部分数量
    :return: 包含域名、级别和标题的字典列表
    """
    visited = set()
    results = []
    base_domain = '.'.join(urlparse(base_url).netloc.split('.')[-domain_parts_count:])
    queue = deque([(base_url, 1)])

    async with aiohttp.ClientSession() as session:
        while queue:
            url, level = queue.popleft()
            url = url.rstrip('/')
            if url in visited or level > max_level:
                continue
            visited.add(url)
            logging.info(f"Crawling {url} at level {level}")

            links = await get_links(session, url)
            for link in links:
                if not is_within_domain(base_domain, link['url'], domain_parts_count):
                    continue
                full_url = str(link['url']).rstrip('/')
                if not is_valid_url(full_url):
                    continue
                if full_url in visited:
                    continue
                queue.append((full_url, level + 1))
                if is_within_domain(base_domain, full_url, domain_parts_count):
                    existing_result = next((result for result in results if result['url'] == full_url), None)
                    if existing_result:
                        if link['title'] and not link['title'].isascii() and existing_result['title'].isascii():
                            existing_result['title'] = link['title']
                    else:
                        if full_url in visited:
                            continue
                        parsed_url = urlparse(full_url)
                        if parsed_url.path or parsed_url.params or parsed_url.query or parsed_url.fragment:
                            continue
                        logging.info(f"Adding {full_url}")
                        results.append({
                            'id': len(results) + 1,
                            'url': full_url,
                            'level': level,
                            'title': link['title']
                        })
    save_results_to_json(results, dir_name, domains_json_path)
    return results


def get_domain_urls(base_url, max_level, domain_parts_count):
    results = asyncio.run(crawl_domain(base_url, max_level, domain_parts_count))
    return results


if __name__ == "__main__":
    base_url = "https://www.nepu.edu.cn"
    results = get_domain_urls(base_url, 3, 3)
    for result in results:
        print(result)
