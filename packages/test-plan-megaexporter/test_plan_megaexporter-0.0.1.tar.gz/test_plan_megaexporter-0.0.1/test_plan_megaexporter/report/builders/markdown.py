
import re
from typing import List, Tuple

from reportlab.platypus import Flowable

from test_plan_megaexporter.report.builders.table import TableOfContentBuilder
from test_plan_megaexporter.report.builders.base_builders import (
    BoldTextBuilder,
    CodeBlockBuilder,
    ImageBuilder,
    SpacerBuilder,
    TextBuilder,
    FilenameTextBuilder,
)
from test_plan_megaexporter.report.builders.utils import LinkFile, format_inline_text

class MarkdownConverter:

    def __init__(
            self,
            text_builder_class=TextBuilder,
            image_builder_class=ImageBuilder,
            code_block_builder_class=CodeBlockBuilder,
            spacer_builder_class=SpacerBuilder,
            bold_text_builder_class=BoldTextBuilder,
            filename_text_builder_class=FilenameTextBuilder,
            table_builder_class=TableOfContentBuilder,
            format_text_func=format_inline_text,

    ):
        self.text_builder_class = text_builder_class
        self.image_builder_class = image_builder_class
        self.code_block_builder_class = code_block_builder_class
        self.spacer_builder_class = spacer_builder_class
        self.bold_text_builder_class = bold_text_builder_class
        self.filename_text_builder_class = filename_text_builder_class
        self.table_builder_class = table_builder_class
        self._format_text = format_text_func


    def convert(self, markdown_text) -> list[Flowable]:
        elements = self._parse_markdown(markdown_text)
        return elements

    def _parse_markdown(self, markdown_text):
        if not markdown_text:
            return []

        elements = []
        lines = markdown_text.replace('<br>', '\n').replace('<br/>', '\n').split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip(' \\')

            if not line:
                elements.append(self.spacer_builder_class.build(1, 6))
                i += 1
            elif line.startswith('#'):
                elements.append(self._header(line))
                i += 1
            elif line.startswith('```'):
                code, consumed = self._code_block(lines, i)
                elements.append(code)
                i += consumed

            elif '.. command-example::' in line:
                code, consumed = self._re_st_command(lines, i)
                elements.append(code)
                i += consumed
            elif re.match(r'(.*)!?\[.*\]\(.*\)', line):
                img = self._image(line)
                if img: elements.extend(img)
                i += 1
            elif '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
                table_elements, consumed = self._parse_table(lines,i)
                elements.extend(table_elements)
                i += consumed
            elif self._is_list_item(line):
                list_items, consumed = self._list(lines, i)
                elements.extend(list_items)
                i += consumed
            else:
                para_elements, consumed = self._paragraph(lines, i)
                if para_elements:
                    elements.extend(para_elements)
                i += consumed

        return elements

    def _header(self, line):
        text = line.lstrip('#. ').strip()
        return self.bold_text_builder_class.build(self._format_text(text))

    def _code_block(self, lines, start):
        i = start + 1
        code_lines = []

        while i < len(lines) and not lines[i].startswith('```'):
            code_lines.append(lines[i])
            i += 1
        code = '<br/>'.join([self._format_text(line) for line in code_lines])
        return self.code_block_builder_class.build(code), i + 1 - start

    def _re_st_command(self, lines, start):
        i = start + 1
        code_lines = []

        # skip leading empty lines
        while i < len(lines) and not lines[i].strip():
            i += 1

        while i < len(lines) and lines[i].strip():
            code_lines.append(lines[i])
            i += 1

        code = '<br/>'.join([self._format_text(line) for line in code_lines])
        return self.code_block_builder_class.build(code), i + 1 - start


    def _image(self, line):
        match = re.match(r'(.*?)!?\[(.*?)\]\((.*?)\)(.*)', line)
        if not match:
            return None
        text_before, alt, src, text_after = match.groups()

        elements = []
        if text_before:
            text_before = self._format_text(text_before)
            elements.append(self.text_builder_class.build(text_before))

        match = re.search(r'/attachments/(\d+)/?$', src)
        if match:
            attachment_id = match.groups()
            elements.append(LinkFile(src, attachment_id=attachment_id[0]))
            elements.append(self.filename_text_builder_class.build(f'File: {src}'))
        else:
            elements.extend(self.image_builder_class.build(src))

        if text_after:
            text_after = self._format_text(text_after)
            elements.append(self.text_builder_class.build(text_after))

        elements.append(self.spacer_builder_class.build(50, 5))

        return elements

    def _is_list_item(self, line):
        if re.match(r'^[\s]*[-*+]\s+', line):
            return True
        if re.match(r'^[\s]*\d+\.\s+', line):
            return True
        return False

    def _list(self, lines, start):
        elements = []
        i = start
        current_list_type = None
        list_items = []

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if self._is_list_item(line):
                is_numbered = re.match(r'^[\s]*\d+\.\s+', line)
                list_type = 'numbered' if is_numbered else 'bullet'

                if current_list_type and current_list_type != list_type:
                    elements.extend(self._format_list_items(list_items, current_list_type))
                    list_items = []

                current_list_type = list_type

                if is_numbered:
                    item_text = re.sub(r'^[\s]*\d+\.\s+', '', line)
                else:
                    item_text = re.sub(r'^[\s]*[-*+]\s+', '', line)

                list_items.append(self._format_text(item_text))
                i += 1
            else:
                break

        if list_items and current_list_type:
            elements.extend(self._format_list_items(list_items, current_list_type))

        return elements, i - start

    def _format_list_items(self, items, list_type):
        elements = []
        for i, item in enumerate(items, 1):
            if list_type == 'numbered':
                formatted_item = f"{i}. {item}"
            else:
                formatted_item = f"• {item}"

            elements.append(self.text_builder_class.build(formatted_item))

        elements.append(self.spacer_builder_class.build(1, 6))
        return elements

    def _parse_table(self, lines: List[str], index: int) -> Tuple[list[Flowable], int]:
        table_lines = []
        elements = []
        i = index

        # collect table lines
        while i < len(lines) and '|' in lines[i]:
            if not re.match(r'^\s*\|[\s\-:]*\|\s*$', lines[i]) and not re.search(r'^(\|-*)+$', lines[i]):
                table_lines.append(lines[i])
            i += 1

        if len(table_lines) > 1:  # at least header + one row
            table_data = []
            for line in table_lines:
                # split by | and clean up
                cells = [self.text_builder_class.build(cell.strip()) for cell in line.split('|')[1:-1]]
                if cells:  # skip empty rows
                    table_data.append(cells)

            if table_data:
                table = self.table_builder_class.build(table_data[0], table_data[1:])
                elements.append(table)
                elements.append(self.spacer_builder_class.build(1, 20))

        return elements, i


    def _paragraph(self, lines, start):
        elements = []
        para_lines = []
        i = start

        while i < len(lines):
            line = lines[i].strip()
            if not line or any(symb in line for symb in ['#', '```', '!', '[', '|']) or self._is_list_item(line):
                break
            para_lines.append(line)
            i += 1

        if not para_lines:
            return None, 1

        for line in para_lines:
            formatted_text = self._format_text(line)
            elements.append(self.text_builder_class.build(formatted_text, need_escape=False))

        if len(elements) > 1:
            elements.append(self.spacer_builder_class.build(1, 10))

        return elements, i - start
