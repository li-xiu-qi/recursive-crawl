import json
import logging
from typing import List, Tuple
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_TYPES = {}


def load_file_types():
    global FILE_TYPES
    if FILE_TYPES:
        return
    with open('file_types.json', 'r') as file:
        FILE_TYPES = json.load(file)


def extract_links(soup: BeautifulSoup, base_url: str, target_tags: List[str],
                  domain_matching: bool = False, path_matching: bool = False,
                  exclude_image_urls: bool = True) -> List[Tuple[str, str]]:
    base_parsed = urlparse(base_url)
    load_file_types()

    def is_relevant_link(href: str) -> bool:
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)

        if any(parsed_url.path.lower().endswith(f'.{ext}') for ext in FILE_TYPES):
            return True

        domain_matches = base_parsed.netloc == parsed_url.netloc if domain_matching else True
        path_matches = base_parsed.path in parsed_url.path if path_matching else True

        is_valid = all([parsed_url.scheme, parsed_url.netloc])
        if exclude_image_urls:
            is_valid = is_valid and not href.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))

        return domain_matches and path_matches and is_valid

    links = []
    for tag in target_tags:
        for element in soup.find_all(tag):
            for link in element.find_all('a', href=True):
                if is_relevant_link(link['href']):
                    full_link = urljoin(base_url, link['href'])
                    link_text = link.get_text(strip=True)
                    links.append((full_link, link_text))

    logger.info(f'📥 提取到的链接及其标题: {links}')

    return links


if __name__ == "__main__":
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div>
                <a href="https://example.com/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="https://otherdomain.com/page3">Page 3</a>
                <a href="image.png">Image</a>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    base_url = "https://example.com"
    target_tags = ['body']

    links = extract_links(soup, base_url, target_tags, domain_matching=True, exclude_image_urls=True)
    for link, text in links:
        print(f"Link: {link}, Text: {text}")
