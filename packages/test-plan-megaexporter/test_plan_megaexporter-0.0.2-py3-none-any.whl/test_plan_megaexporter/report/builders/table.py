
from reportlab.lib import colors, units
from reportlab.platypus import TableStyle, Flowable, LongTable

from test_plan_megaexporter.report.builders.base_builders import PDFElementBuilder
from test_plan_megaexporter.report.common import FontManager


class TableOfContentBuilder(PDFElementBuilder):
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (1, 1), (-1, -1), FontManager.regular),
        ('FONTNAME', (0, 0), (-1, 1), FontManager.bold),
    ])
    max_width = 7

    @classmethod
    def build(cls, headers: list[str], data_rows: list[list[str]], col_widths: list[int] = None) -> Flowable:
        data = [headers] + data_rows
        if not col_widths:
            col_widths = [cls.max_width / len(headers)] * len(headers)
        col_widths_calculated = [w * units.inch for w in col_widths]
        table = LongTable(data, colWidths=col_widths_calculated, repeatRows=1)
        table.setStyle(cls.style)
        return table
