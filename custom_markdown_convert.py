from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from markdownify import MarkdownConverter, abstract_inline_conversion, chomp


class CustomMarkdownConverter(MarkdownConverter):
    def __init__(self, current_url, **kwargs):
        super().__init__(**kwargs)
        self.current_url = current_url
        self.convert_to_absolute = kwargs.get('convert_to_absolute', False)

    def convert_img(self, element, text, convert_as_inline):
        alt_text = element.attrs.get('alt', '') or ''
        src_url = element.attrs.get('src', '') or ''
        title_text = element.attrs.get('title', '') or ''

        if title_text:
            escaped_title = title_text.replace('"', r'\"')
            title_part = f' "{escaped_title}"'
        else:
            title_part = ''

        if self.convert_to_absolute:
            src_url = urljoin(self.current_url, src_url)

        if convert_as_inline and element.parent.name not in self.options['keep_inline_images_in']:
            return alt_text

        return f'![{alt_text}]({src_url}{title_part})'

    def _process_table_element(self, element):
        soup = BeautifulSoup(str(element), 'html.parser')
        for tag in soup.find_all(True):
            attrs_to_keep = ['colspan', 'rowspan']
            tag.attrs = {key: value for key, value in tag.attrs.items() if key in attrs_to_keep}
        return str(soup)

    def convert_table(self, element, text, convert_as_inline):
        soup = BeautifulSoup(str(element), 'html.parser')
        has_colspan_or_rowspan = any(
            tag.has_attr('colspan') or tag.has_attr('rowspan') for tag in soup.find_all(['td', 'th']))

        if has_colspan_or_rowspan:
            return self._process_table_element(element)
        else:
            return super().convert_table(element, text, convert_as_inline)

    def convert_a(self, element, text, convert_as_inline):
        prefix, suffix, text = chomp(text)
        if not text:
            return ''
        href_url = element.get('href')
        title_text = element.get('title')

        if self.convert_to_absolute:
            href_url = urljoin(self.current_url, href_url)

        if (self.options['autolinks']
                and text.replace(r'\_', '_') == href_url
                and not title_text
                and not self.options['default_title']):
            return f'<{href_url}>'
        if self.options['default_title'] and not title_text:
            title_text = href_url

        if title_text:
            escaped_title = title_text.replace('"', r'\"')
            title_part = f' "{escaped_title}"'
        else:
            title_part = ''

        return f'{prefix}[{text}]({href_url}{title_part}){suffix}' if href_url else text

    convert_b = abstract_inline_conversion(lambda self: 2 * self.options['strong_em_symbol'])


def html2md(html_content, current_url, **options):
    options['current_url'] = current_url
    return CustomMarkdownConverter(**options).convert(html_content)


# 示例用法
html_content = """
<html>
<body>
<img src="/path/to/image.jpg" alt="示例图片">
<a href="/path/to/page">示例链接</a>
<table>
    <tr>
        <td colspan="2">Cell with colspan</td>
    </tr>
    <tr>
        <td>Cell 1</td>
        <td>Cell 2</td>
    </tr>
</table>
</body>
</html>
"""

# 假设这是当前页面的完整 URL
current_url = "https://example.com/some/page.html"

# 将 HTML 转换为 Markdown
markdown_content = html2md(html_content, current_url=current_url, convert_to_absolute=True)

print(markdown_content)
