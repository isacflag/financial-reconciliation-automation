"""Generate fictional DDA and ERP files for the public demo."""

from __future__ import annotations

import datetime as dt
from copy import copy
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def generate_spreadsheet() -> Path:
    output = EXAMPLES / "dda_demo.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "DDA"
    sheet.append(
        [
            "BANCO",
            "NOME",
            "Nº DOC",
            "VENCIMENTO",
            "A PAGAR",
            "CENTRO DE CUSTO",
            "LANÇADO",
        ]
    )
    sheet.append(
        [
            "001",
            "ACME SUPRIMENTOS",
            "123456",
            dt.date(2026, 8, 10),
            100.01,
            "",
            "",
        ]
    )
    sheet.append(
        [
            "001",
            "FORNECEDOR DESCONHECIDO",
            "",
            dt.date(2026, 8, 10),
            200.00,
            "",
            "",
        ]
    )
    sheet.append(
        [
            "001",
            "GAMMA SERVIÇOS",
            "999999",
            dt.date(2026, 9, 10),
            300.00,
            "",
            "",
        ]
    )
    for cell in sheet[1]:
        font = copy(cell.font)
        font.bold = True
        cell.font = font
    sheet.freeze_panes = "A2"
    workbook.save(output)
    return output


def generate_pdf() -> Path:
    output = EXAMPLES / "erp_report_demo.pdf"
    document = SimpleDocTemplate(str(output), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ERP Accounts Payable Report — Fictional Demo", styles["Title"]),
        Spacer(1, 18),
    ]
    data = [
        ["Centro de Custo:", "001 - PROJETO ALFA", "", "", ""],
        ["CREDOR", "DOCUMENTO", "LANCAMENTO", "DATA VENCTO", "TOTAL"],
        ["ACME SUPRIMENTOS LTDA", "NF 123456", "L-001", "10/08/2026", "100,00"],
        ["BETA SERVICOS LTDA", "NF 888888", "L-002", "10/08/2026", "200,00"],
    ]
    table = Table(data, colWidths=[130, 100, 85, 90, 70])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    document.build(story)
    return output


if __name__ == "__main__":
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    print(generate_spreadsheet())
    print(generate_pdf())
