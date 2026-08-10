from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .models import PdfRecord
from .normalization import (
    ascii_upper,
    money_to_cents,
    normalize_cost_center,
    parse_date_br,
)


def _exact_index(cells: list[str], *aliases: str) -> int | None:
    normalized = {ascii_upper(alias) for alias in aliases}
    for index, cell in enumerate(cells):
        if cell in normalized:
            return index
    return None


def _contains_index(cells: list[str], *fragments: str) -> int | None:
    normalized = tuple(ascii_upper(fragment) for fragment in fragments)
    for index, cell in enumerate(cells):
        if any(fragment in cell for fragment in normalized):
            return index
    return None


def parse_table_records(
    table: list[list[object]], page_number: int, start_id: int = 0
) -> list[PdfRecord]:
    """Parse records from one table extracted by pdfplumber."""

    records: list[PdfRecord] = []
    current_cost_center: str | None = None
    header_map: dict[str, int | None] | None = None

    for row in table or []:
        if not row:
            continue
        normalized_row = [str(cell or "").strip() for cell in row]
        first_cell = normalized_row[0]
        first_upper = ascii_upper(first_cell)

        if first_upper.startswith("CENTRO DE CUSTO"):
            inline_center = first_cell.partition(":")[2].strip()
            second_cell = normalized_row[1] if len(normalized_row) > 1 else ""
            current_cost_center = normalize_cost_center(inline_center or second_cell)
            header_map = None
            continue

        upper_cells = [ascii_upper(cell) for cell in normalized_row]
        creditor_index = _exact_index(upper_cells, "CREDOR", "BENEFICIÁRIO")
        document_index = _exact_index(upper_cells, "DOCUMENTO", "Nº DOCUMENTO")
        date_index = _contains_index(upper_cells, "DATA VENCTO", "VENCIMENTO")
        total_index = _exact_index(upper_cells, "TOTAL", "VALOR TOTAL")

        if all(
            index is not None
            for index in (creditor_index, document_index, date_index, total_index)
        ):
            header_map = {
                "creditor": creditor_index,
                "document": document_index,
                "launch": _contains_index(upper_cells, "LANCAMENTO"),
                "date": date_index,
                "total": total_index,
            }
            continue

        if not current_cost_center or not header_map:
            continue

        required_indices = [
            index
            for key, index in header_map.items()
            if key != "launch" and index is not None
        ]
        if not required_indices or len(normalized_row) <= max(required_indices):
            continue

        date_index = header_map["date"]
        total_index = header_map["total"]
        creditor_index = header_map["creditor"]
        document_index = header_map["document"]
        assert date_index is not None
        assert total_index is not None
        assert creditor_index is not None
        assert document_index is not None

        date_text = normalized_row[date_index]
        total_text = normalized_row[total_index]
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_text):
            continue
        if not re.fullmatch(r"-?\d{1,3}(?:\.\d{3})*,\d{2}", total_text):
            continue

        launch_index = header_map["launch"]
        launch = (
            normalized_row[launch_index]
            if launch_index is not None and launch_index < len(normalized_row)
            else ""
        )
        document = normalized_row[document_index]
        records.append(
            PdfRecord(
                record_id=start_id + len(records),
                page=page_number,
                cost_center=current_cost_center,
                creditor=normalized_row[creditor_index],
                document=document,
                launch=launch,
                due_date=parse_date_br(date_text),
                cents=money_to_cents(total_text, brazilian_text=True),
                ppc="PPC" in ascii_upper(document),
            )
        )

    return records


def parse_pdf_tables(pdf_path: Path) -> list[PdfRecord]:
    records: list[PdfRecord] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables():
                records.extend(parse_table_records(table, page_number, len(records)))

    if not records:
        raise ValueError(
            "No payable records were found in the PDF. Confirm that it is a "
            "text-based ERP report with cost center, creditor, document, due "
            "date and total columns."
        )
    return records
