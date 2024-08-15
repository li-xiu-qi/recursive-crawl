from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


class CustomMarkdownConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that strips images and keeps tables in HTML format without CSS styles,
    while preserving attributes like colspan and rowspan.
    """

    def convert_img(self, el, text, convert_as_inline):
        return ''

    def _process_element(self, el):
        soup = BeautifulSoup(str(el), 'html.parser')
        for tag in soup.find_all(True):
            attrs_to_keep = ['colspan', 'rowspan']
            tag.attrs = {key: value for key, value in tag.attrs.items() if key in attrs_to_keep}
        return str(soup)

    def convert_table(self, el, text, convert_as_inline):
        return self._process_element(el)


def html2md(html, **options):
    return CustomMarkdownConverter(**options).convert(html)
