from __future__ import annotations

from copy import copy
from typing import Iterable

from .constants import AUDIT_HEADERS, FILL_ERROR, FILL_HIGH, FILL_MEDIUM
from .models import Candidate, DdaRecord
from .normalization import ascii_upper, cents_to_float, excel_date, money_to_cents


def find_header(sheet) -> int:
    for row_number in range(1, min(sheet.max_row, 30) + 1):
        values = [
            ascii_upper(sheet.cell(row_number, column).value)
            for column in range(1, sheet.max_column + 1)
        ]
        joined = " ".join(values)
        if "BANCO" in joined and "VENCIMENTO" in joined and "PAGAR" in joined:
            return row_number
    raise ValueError("DDA spreadsheet header not found")


def find_column(
    sheet,
    header_row: int,
    aliases: Iterable[str],
    *,
    required: bool = True,
) -> int | None:
    normalized_aliases = tuple(ascii_upper(alias) for alias in aliases)
    headers = {
        column: ascii_upper(sheet.cell(header_row, column).value)
        for column in range(1, sheet.max_column + 1)
    }
    for column, value in headers.items():
        if value in normalized_aliases:
            return column
    for column, value in headers.items():
        if any(alias in value for alias in normalized_aliases):
            return column
    if required:
        raise ValueError(f"Column not found: {' / '.join(aliases)}")
    return None


def read_dda_records(
    sheet, header_row: int, columns: dict[str, int]
) -> list[DdaRecord]:
    records: list[DdaRecord] = []
    for row_number in range(header_row + 1, sheet.max_row + 1):
        due_value = sheet.cell(row_number, columns["date"]).value
        amount_value = sheet.cell(row_number, columns["value"]).value
        if due_value in (None, "") or amount_value in (None, ""):
            continue
        records.append(
            DdaRecord(
                row=row_number,
                beneficiary=str(
                    sheet.cell(row_number, columns["beneficiary"]).value or ""
                ),
                document=str(sheet.cell(row_number, columns["document"]).value or ""),
                due_date=excel_date(due_value),
                cents=money_to_cents(amount_value),
            )
        )
    return records


def copy_cell_style(source, target) -> None:
    if source.has_style:
        target._style = copy(source._style)
    if source.number_format:
        target.number_format = source.number_format
    target.alignment = copy(source.alignment)
    target.protection = copy(source.protection)


def add_audit_columns(sheet, header_row: int, status_column: int) -> dict[str, int]:
    existing_headers = {
        str(sheet.cell(header_row, column).value or "").strip(): column
        for column in range(1, sheet.max_column + 1)
    }
    if all(header in existing_headers for header in AUDIT_HEADERS):
        result = {header: existing_headers[header] for header in AUDIT_HEADERS}
        for column in result.values():
            for row_number in range(header_row + 1, sheet.max_row + 1):
                sheet.cell(row_number, column).value = None
        return result

    last_header_column = max(
        (
            column
            for column in range(1, sheet.max_column + 1)
            if sheet.cell(header_row, column).value not in (None, "")
        ),
        default=sheet.max_column,
    )
    start_column = last_header_column + 1
    result: dict[str, int] = {}
    header_source = sheet.cell(header_row, status_column)
    body_source = sheet.cell(header_row + 1, status_column)
    widths = {
        "CRITÉRIO": 48,
        "CONFIANÇA": 14,
        "PÁGINA PDF": 12,
        "CREDOR ERP": 46,
        "DOCUMENTO ERP": 24,
        "LANÇAMENTO ERP": 20,
        "VENCIMENTO ERP": 20,
        "VALOR ERP": 18,
    }

    for offset, header in enumerate(AUDIT_HEADERS):
        column = start_column + offset
        result[header] = column
        cell = sheet.cell(header_row, column, header)
        copy_cell_style(header_source, cell)
        sheet.column_dimensions[cell.column_letter].width = widths[header]
        for row_number in range(header_row + 1, sheet.max_row + 1):
            copy_cell_style(body_source, sheet.cell(row_number, column))

    sheet.auto_filter.ref = (
        f"{sheet.cell(header_row, 1).coordinate}:"
        f"{sheet.cell(sheet.max_row, start_column + len(AUDIT_HEADERS) - 1).coordinate}"
    )
    return result


def write_match(
    sheet,
    dda: DdaRecord,
    candidate: Candidate,
    columns: dict[str, int],
    audit_columns: dict[str, int],
) -> None:
    pdf = candidate.pdf
    sheet.cell(dda.row, columns["cost_center"]).value = pdf.cost_center
    if candidate.confidence == "MÉDIA":
        status = "REVISAR"
    else:
        status = "PPC" if pdf.ppc else "LANÇADO"
    sheet.cell(dda.row, columns["status"]).value = status
    sheet.cell(dda.row, audit_columns["CRITÉRIO"]).value = candidate.criterion
    confidence_cell = sheet.cell(dda.row, audit_columns["CONFIANÇA"])
    confidence_cell.value = candidate.confidence
    confidence_cell.fill = FILL_HIGH if candidate.confidence == "ALTA" else FILL_MEDIUM
    sheet.cell(dda.row, audit_columns["PÁGINA PDF"]).value = pdf.page
    sheet.cell(dda.row, audit_columns["CREDOR ERP"]).value = pdf.creditor
    sheet.cell(dda.row, audit_columns["DOCUMENTO ERP"]).value = pdf.document
    sheet.cell(dda.row, audit_columns["LANÇAMENTO ERP"]).value = pdf.launch
    due_cell = sheet.cell(dda.row, audit_columns["VENCIMENTO ERP"])
    due_cell.value = pdf.due_date
    due_cell.number_format = "dd/mm/yyyy"
    value_cell = sheet.cell(dda.row, audit_columns["VALOR ERP"])
    value_cell.value = cents_to_float(pdf.cents)
    value_cell.number_format = 'R$ #,##0.00'


def write_unmatched(
    sheet,
    dda: DdaRecord,
    reason: str,
    columns: dict[str, int],
    audit_columns: dict[str, int],
) -> None:
    sheet.cell(dda.row, columns["cost_center"]).value = "X"
    sheet.cell(dda.row, columns["status"]).value = "X"
    sheet.cell(dda.row, audit_columns["CRITÉRIO"]).value = reason
    confidence_cell = sheet.cell(dda.row, audit_columns["CONFIANÇA"])
    confidence_cell.value = "NÃO CONCILIADO"
    confidence_cell.fill = FILL_ERROR
