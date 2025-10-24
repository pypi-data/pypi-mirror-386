
import os
import re

from django.contrib.staticfiles import finders
from reportlab.lib import units
from reportlab.platypus import Image
from testy.core.models import Attachment

from test_plan_megaexporter.report.common import FontManager

FILE_LINK_REGISTRY = []

class LinkFile(Image):
    _default =  'test_plan_megaexporter/img/default.png'
    _max_width: int = 140 * units.mm
    _max_height: int = 180 * units.mm

    def __init__(self, filename: str, attachment_id: int):
        super(LinkFile, self).__init__(filename, hAlign='LEFT')
        self.attachment_id = int(attachment_id)
        FILE_LINK_REGISTRY.append(self)


    def make_real_path(self, attachment_map: dict[int, Attachment]):
        attachment = attachment_map.get(self.attachment_id)
        if attachment:
            if attachment.file_extension.startswith('image/'):
                self.filename = attachment.file.path

        if not os.path.exists(self.filename):
            self.filename = finders.find(self._default)

        super(LinkFile, self).__init__(self.filename, hAlign='LEFT')

        if hasattr(self, 'imageWidth') and self.imageWidth > self._max_width:
            self.drawWidth = self._max_width
            self.drawHeight = self.imageHeight * (self._max_width / self.imageWidth)


def format_inline_text(text : str) -> str :
    if not text:
        return ''

    parts = re.split(r'(<font[^>]*>|</font>)', text)
    for i in range(len(parts)):
        if not parts[i].startswith('<font') and parts[i] != '</font>':
            parts[i]  = re.sub(r'"([^"]*)"', convert_special_chars_in_quotes, parts[i] )
    text = ''.join(parts)

    # bold (**text** or __text__)
    text=re.sub(r'\*\*(.*?)\*\*',rf'<font name="{FontManager.bold}" >\1</font>',text)

    # italic (*text* or _text_)
    text=re.sub(r'\*(.*?)\*',rf'<font name="{FontManager.italic}" >\1</font>',text)

    # inline code (`code`)
    text=re.sub(r'`([^`]+)`',rf'<font name="{FontManager.regular}" backColor="lightgrey">\1</font>',text)

    # Links [text](url)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<link href="\2" color="blue">\1</link>',text)

    # strikethrough (~~text~~)
    text=re.sub(r'~~(.*?)~~',r'<strike>\1</strike>',text)

    # emoji
    emoji_pattern = r'([\U0001F000-\U0001FAFF\U00002700-\U000027BF\U0000FE00-\U0000FE0F\U0001F900-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U0000E000-\U0000F8FF])'
    text = re.sub(emoji_pattern,rf'<font name="{FontManager.emoji}">\1</font>', text)

    return text


def escape(text) -> str:
    if not text:
        return text

    special_chars = {
        '#': '&num;',
        '*': '&ast;',
        '<': '&lt;',
        '>': '&gt;'
    }

    for char, entity in special_chars.items():
        text = text.replace(char, entity)

    return text

def convert_special_chars_in_quotes(match: re.Match) -> str:
    quoted_content = match.group(1)
    quoted_content = escape(quoted_content)
    return f'"{quoted_content}"'
