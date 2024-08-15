# 项目名称

当前版本: v0.0.1

## 简介

这是一个递归爬取网页的项目，思路是从一个主页开始，开始递归爬取所有的二级域名，获取到网站的所有的二级域名之后，我们开始递归爬取所有域名下的url，每个带有html内容的url，会先将html转换成markdown格式，然后再将markdown格式的内容保存到本地。如果html上有文件的链接也可以下载下来。

爬取效果：
![75d3b569b940ec86c4e109bba7d28f0e.png](img-source/75d3b569b940ec86c4e109bba7d28f0e.png)
![c494d1df26fb537a1ac813a2e41d27d5.png](img-source/c494d1df26fb537a1ac813a2e41d27d5.png)