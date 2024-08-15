import os


def set_file_path(filename: str, base_dir: str) -> str:
    """设置文件路径"""
    return os.path.join(os.path.dirname(__file__), base_dir, filename)


class UrlManager:
    """URL管理类，用于管理已爬取、未爬取、已下载、未下载的URL"""

    def __init__(self, base_dir: str, continue_crawl: bool):
        self.CRAWLED_URLS_FILE = set_file_path('crawled_urls.txt', base_dir=base_dir)
        self.DOWNLOADED_URLS_FILE = set_file_path('downloaded_urls.txt', base_dir=base_dir)
        self.UNCRAWLED_URLS_FILE = set_file_path('uncrawled_urls.txt', base_dir=base_dir)
        self.UNDOWNLOADED_URLS_FILE = set_file_path('undownloaded_urls.txt', base_dir=base_dir)
        self.continue_crawl = continue_crawl
        self.already_crawled = self._initialize_state(self.CRAWLED_URLS_FILE)
        self.already_downloaded = self._initialize_state(self.DOWNLOADED_URLS_FILE)
        self.uncrawled_urls = self._initialize_state(self.UNCRAWLED_URLS_FILE)
        self.undownloaded_urls = self._initialize_state(self.UNDOWNLOADED_URLS_FILE)

    def _initialize_state(self, file_path: str) -> set:
        """初始化URL集合"""
        if self.continue_crawl:
            if not os.path.exists(file_path):
                return set()
            with open(file_path, 'r') as f:
                return set(line.strip() for line in f)
        return set()

    def save_state(self) -> None:
        """保存URL状态"""
        self._save_url(self.already_crawled, self.CRAWLED_URLS_FILE)
        self._save_url(self.already_downloaded, self.DOWNLOADED_URLS_FILE)
        self._save_url(self.uncrawled_urls, self.UNCRAWLED_URLS_FILE)
        self._save_url(self.undownloaded_urls, self.UNDOWNLOADED_URLS_FILE)

    def _save_url(self, urls: set, file_path: str) -> None:
        """将URL集合保存到文件"""
        with open(file_path, 'w') as f:
            for url in urls:
                f.write(f'{url}\n')
