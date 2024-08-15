import logging

import requests
import validators

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)






def is_valid_url(url: str) -> bool:
    """
       判断URL是否有效且能正常使用（非404）
       :param url: 需要检查的URL
       :return: 如果URL有效且非404则返回True，否则返回False
       """
    # 使用validators库验证URL格式
    if not validators.url(url):
        logger.debug(f'❌ URL格式无效: {url}')
        return False

    # 尝试发送HEAD请求以检查URL
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 404:
            logger.debug(f'❌ URL不可访问: {url} (404 Not Found)')
            return False
        elif response.status_code >= 400:
            logger.debug(f'⚠️ URL请求返回错误状态码: {url} ({response.status_code})')
            return _retry_with_get(url)
        return True
    except requests.exceptions.RequestException as e:
        logger.debug(f'❌ HEAD请求失败: {url}, 错误: {str(e)}')


def _retry_with_get(url: str) -> bool:
    """
    使用GET请求重新尝试访问URL
    :param url: 需要检查的URL
    :return: 如果URL有效且非404则返回True，否则返回False
    """
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        if response.status_code == 404:
            logger.debug(f'❌ URL不可访问: {url} (404 Not Found)')
            return False
        elif response.status_code >= 400:
            logger.debug(f'⚠️ URL请求返回错误状态码: {url} ({response.status_code})')
            return False
        return True
    except requests.exceptions.RequestException as e:
        logger.debug(f'❌ GET请求失败: {url}, 错误: {str(e)}')
        return False


if __name__ == "__main__":
    url = "https://chat.deepseek.com/coder"
    print(is_valid_url(url))
