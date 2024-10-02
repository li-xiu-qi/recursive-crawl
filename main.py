import json
import logging
import os

from crawler import md_crawl, set_file_path, Config
from get_domains import get_domain_urls

DEFAULT_MAX_DEPTH = 10
DEFAULT_NUM_THREADS = 2
DEFAULT_TARGET_AREA_CONTENT_TAGS = ['article', 'div', 'main', 'p']
DEFAULT_TARGET_AREA_LINKS_TAGS = ['body']
DEFAULT_DOMAIN_MATCH = True
DEFAULT_BASE_PATH_MATCH = False

CONTINUE_CRAWL = True
SLEEP_TIME = 2.0
logger = logging.getLogger(__name__)

log_file_path = 'main_log.log'

# 配置日志记录器
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.FileHandler(log_file_path),  # 将日志输出到文件
        logging.StreamHandler()  # 同时保留控制台输出
    ]
)


def prepare_params(result):
    try:
        config = Config(base_url=result['url'])
        config.BASE_DIR = os.path.join("data", result['title'])
        dir_name = os.path.join("data", result['title'])
        config.DEFAULT_BASE_MD_PATH = set_file_path('markdown', dir_name=dir_name)
        config.DEFAULT_RECORD_JSON_DIR = set_file_path("record_json_file.json", dir_name=dir_name)
        config.DEFAULT_DOMAIN_MATCH = True
        config.DEFAULT_BASE_PATH_MATCH = True
        config.DEFAULT_FILE_DOWNLOAD_DIR = set_file_path("download", dir_name=dir_name)
        config.SLEEP_TIME = SLEEP_TIME

        crawl_config = {
            'base_url': config.base_url,
            'max_depth': DEFAULT_MAX_DEPTH,
            'num_threads': DEFAULT_NUM_THREADS,
            'base_md_dir': config.DEFAULT_BASE_MD_PATH,
            'target_area_content_tags': DEFAULT_TARGET_AREA_CONTENT_TAGS,
            'target_area_links_tags': DEFAULT_TARGET_AREA_LINKS_TAGS,
            'is_domain_match': DEFAULT_DOMAIN_MATCH,
            'is_base_path_match': DEFAULT_BASE_PATH_MATCH,
            'file_download_dir': config.DEFAULT_FILE_DOWNLOAD_DIR,
            'output_json': config.DEFAULT_RECORD_JSON_DIR,
            'md_with_links': False,
            'exclude_image_urls': True,
            'is_debug': True,
            'continue_crawl': CONTINUE_CRAWL,
            'base_dir': config.BASE_DIR,
            'sleep_time': config.SLEEP_TIME
        }
        return crawl_config
    except Exception as e:
        logging.error(f"Error in prepare_params: {e}")
        return None


def main():
    try:
        base_url = 'https://www.nepu.edu.cn'
        results = []
        if os.path.exists("data/domains.json"):
            with open("data/domains.json", "r") as f:
                results = json.load(f)
        if not results:
            results = get_domain_urls(base_url, max_level=3, domain_parts_count=3)

        for result in results:
            try:
                if os.path.exists("data/urls.txt"):
                    with open("data/urls.txt", "r") as f:
                        urls = f.readlines()
                        urls = [url.strip() for url in urls]
                        if result['url'] in urls:
                            continue
                crawl_config = prepare_params(result)
                if crawl_config:
                    md_crawl(crawl_config)
                with open("data/urls.txt", "a") as f:
                    f.write(result['url'] + '\n')
            except Exception as e:
                logging.error(f"Error processing result: {e}")
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")


if __name__ == "__main__":
    main()
