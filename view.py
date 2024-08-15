from requests import Session

session = Session()

# API的URL，假设运行在本地的8000端口
url = "https://www.nepu.edu.cn"

# 发送GET请求
response = session.get(url)
