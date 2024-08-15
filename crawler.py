import asyncio
import concurrent.futures
import logging
import os
import queue
from typing import List, Union, Dict, Any

from bs4 import BeautifulSoup

from extract_links import extract_links
from file_handlers import fetch_page, extract_content, extract_common_file_urls, record_page_info, download_files, \
    save_content, extract_url_title_name
from urlmanager import UrlManager

logger = logging.getLogger(__name__)

# 定义日志文件路径
log_file_path = 'crawler_log.log'

# 配置日志记录器
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)


def process_page(url: str, base_url: str, base_md_dir: str, target_area_content_tags: Union[str, List[str]],
                 md_with_links: bool, url_manager: UrlManager, target_area_links_tags=None,
                 is_domain_match=None, is_base_path_match=None, output_json_file: str = None,
                 file_download_dir: str = None, exclude_image_urls: bool = True, **kwargs) -> List[str]:
    """处理页面，提取内容和链接"""
    if url in url_manager.already_crawled:
        logger.debug(f'🔁 已爬取: {url}')
        return []
    page_content = fetch_page(url)
    if not page_content:
        logger.info(f'❌ 没有发现内容: {url}')
        with open("space_urls.txt", "a") as f:
            f.write(url + '\n')
        return []
    soup = BeautifulSoup(page_content, 'html.parser')
    for script in soup(['script', 'style']):
        script.decompose()
    content = extract_content(soup, target_area_content_tags)

    file_name = extract_url_title_name(url, soup)
    if "404" in file_name:
        logger.info(f'🚫 页面不存在: {url}')
        url_manager.already_crawled.add(url)
        return []
    file_path = os.path.join(base_md_dir.rstrip("/"), f'{file_name}.md')
    save_content(file_path, content, [] if md_with_links else ['a'])
    url_manager.already_crawled.add(url)
    extracted_links = extract_links(soup, base_url, target_area_links_tags, is_domain_match, is_base_path_match,
                                    exclude_image_urls)
    common_file_links = extract_common_file_urls(extracted_links)
    common_file_record = {link: title for link, title in common_file_links}
    record_page_info(url, file_path, common_file_record, output_json_file)

    download_files(common_file_links, file_download_dir, url_manager.already_downloaded)
    for link, _ in common_file_links:
        url_manager.already_downloaded.add(link)

    common_file_urls = [link for link, _ in common_file_links]
    extracted_urls = [link for link, _ in extracted_links]
    filtered_links = list(filter(lambda x: x not in common_file_urls, extracted_urls))
    url_manager.uncrawled_urls.update(filtered_links)
    return filtered_links if filtered_links else []


async def async_worker(q: queue.Queue, config: Dict[str, Any], url_manager: UrlManager) -> None:
    """异步工作线程"""
    while not q.empty():
        depth, url = q.get()
        # if depth > config['max_depth']:
        #     continue
        child_urls = await asyncio.to_thread(process_page, url=url, base_url=config['base_url'],
                                             base_md_dir=config['base_md_dir'],
                                             target_area_content_tags=config['target_area_content_tags'],
                                             md_with_links=config['md_with_links'],
                                             url_manager=url_manager,
                                             target_area_links_tags=config['target_area_links_tags'],
                                             is_domain_match=config['is_domain_match'],
                                             is_base_path_match=config['is_base_path_match'],
                                             output_json_file=config['output_json'],
                                             file_download_dir=config['file_download_dir'],
                                             exclude_image_urls=config['exclude_image_urls'])
        for child_url in child_urls:
            q.put((depth + 1, child_url))
        await asyncio.sleep(config.get('sleep_time', 0.05))
    url_manager.save_state()


def run_worker(q: queue.Queue, config: Dict[str, Any], url_manager: UrlManager):
    """运行工作线程"""
    asyncio.run(async_worker(q, config, url_manager))


def initialize_logging(is_debug: bool):
    """初始化日志"""
    logging.basicConfig(level=logging.DEBUG if is_debug else logging.INFO)
    logger.debug('🐞 调试模式启用' if is_debug else '🚀 启动爬虫')


def start_crawl_threads(q: queue.Queue, config: Dict[str, Any], url_manager: UrlManager):
    """启动爬虫线程"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=config['num_threads']) as executor:
        tasks = [executor.submit(run_worker, q, config, url_manager) for _ in range(config['num_threads'])]
        for task in concurrent.futures.as_completed(tasks):
            task.result()


def md_crawl(config: Dict[str, Any]) -> None:
    """Markdown爬虫主函数"""
    if config['is_domain_match'] is False and config['is_base_path_match'] is True:
        raise ValueError('❌ 如果设置为路径匹配，域名匹配必须为True')
    if not config['base_url']:
        raise ValueError('❌ 基础URL是必须的')
    if isinstance(config['target_area_links_tags'], str):
        config['target_area_links_tags'] = config['target_area_links_tags'].split(',') if ',' in config[
            'target_area_links_tags'] else [config['target_area_links_tags']]
    if isinstance(config['target_area_content_tags'], str):
        config['target_area_content_tags'] = config['target_area_content_tags'].split(',') if ',' in config[
            'target_area_content_tags'] else [config['target_area_content_tags']]
    if not os.path.exists(config['base_md_dir']):
        os.makedirs(config['base_md_dir'])

    initialize_logging(config['is_debug'])
    logger.info(f'🕸️ 爬取 {config["base_url"]} 深度 ⏬ {config["max_depth"]} 线程 🧵 {config["num_threads"]}')
    url_manager = UrlManager(base_dir=config.get("base_dir", "INFO"), continue_crawl=config['continue_crawl'])
    q = queue.Queue()

    if config['continue_crawl'] and url_manager.uncrawled_urls:
        for url in url_manager.uncrawled_urls:
            q.put((0, url))
    else:
        q.put((0, config['base_url']))

    start_crawl_threads(q, config, url_manager)
    url_manager.save_state()
    logger.info('🏁 所有线程已完成')


def set_file_path(filename: str, dir_name: str) -> str:
    """设置文件路径"""
    return os.path.join(os.path.dirname(__file__), dir_name, filename)


class Config:
    """配置类，定义默认配置"""
    BASE_DIR = "INFO"

    def __init__(self, base_url):
        self.base_url = base_url
        self.DEFAULT_BASE_MD_PATH = set_file_path('markdown', self.BASE_DIR)
        self.DEFAULT_MAX_DEPTH = 10
        self.DEFAULT_NUM_THREADS = 2
        self.DEFAULT_TARGET_AREA_CONTENT_TAGS = ['article', 'div', 'main', 'p']
        self.DEFAULT_TARGET_AREA_LINKS_TAGS = ['body']
        self.DEFAULT_DOMAIN_MATCH = True
        self.DEFAULT_BASE_PATH_MATCH = True
        self.DEFAULT_FILE_DOWNLOAD_DIR = set_file_path("download", self.BASE_DIR)
        self.DEFAULT_RECORD_JSON_DIR = set_file_path("record_json_file.json", self.BASE_DIR)
        self.CONTINUE_CRAWL = False
        self.SLEEP_TIME = 0.05

    def get_config(self):
        return {
            "base_dir": self.BASE_DIR,
            "base_url": self.base_url,
            "base_md_dir": self.DEFAULT_BASE_MD_PATH,
            "max_depth": self.DEFAULT_MAX_DEPTH,
            "num_threads": self.DEFAULT_NUM_THREADS,
            "target_area_content_tags": self.DEFAULT_TARGET_AREA_CONTENT_TAGS,
            "md_with_links": False,
            "target_area_links_tags": self.DEFAULT_TARGET_AREA_LINKS_TAGS,
            "is_domain_match": self.DEFAULT_DOMAIN_MATCH,
            "is_base_path_match": self.DEFAULT_BASE_PATH_MATCH,
            "output_json": self.DEFAULT_RECORD_JSON_DIR,
            "file_download_dir": self.DEFAULT_FILE_DOWNLOAD_DIR,
            "exclude_image_urls": True,
            "is_debug": True,
            "continue_crawl": self.CONTINUE_CRAWL,
            "sleep_time": self.SLEEP_TIME
        }


if __name__ == "__main__":
    # url = "https://www.nepu.edu.cn"
    url = "http://xxgk.nepu.edu.cn"
    config = Config(base_url=url)
    md_crawl(config.get_config())
