from __future__ import annotations

import datetime as dt
import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .constants import COST_CENTER_ALIASES


def ascii_upper(value: object) -> str:
    return (
        unicodedata.normalize("NFKD", str(value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .upper()
    )


def compact(value: object, *, remove_labels: bool = False) -> str:
    text = ascii_upper(value)
    if remove_labels:
        text = re.sub(r"^\s*BENEFICIARIO\s*:?\s*", "", text)
        text = re.sub(r"^\s*N[Oº°]?\s*DOC\.?\s*:?\s*", "", text)
    text = re.sub(r"[^A-Z0-9]", "", text)

    # Some bank exports repeat a value in the same cell (NAME+NAME or DOC+DOC).
    if (
        len(text) >= 2
        and len(text) % 2 == 0
        and text[: len(text) // 2] == text[len(text) // 2 :]
    ):
        text = text[: len(text) // 2]
    return text


def document_ids(value: object) -> set[str]:
    text = ascii_upper(value)
    text = re.sub(r"^\s*N[Oº°]?\s*DOC\.?\s*:?\s*", "", text)
    identifiers: set[str] = set()

    def add_identifier(token: str) -> None:
        if len(token) < 4:
            return
        identifiers.add(token.lstrip("0") or "0")
        if (
            len(token) % 2 == 0
            and token[: len(token) // 2] == token[len(token) // 2 :]
        ):
            half = token[: len(token) // 2]
            identifiers.add(half.lstrip("0") or "0")

    for token in re.findall(r"\d+", text):
        add_identifier(token)
    for token in re.findall(r"\d+", compact(text, remove_labels=True)):
        add_identifier(token)
    return identifiers


def normalize_cost_center(value: object) -> str:
    text = ascii_upper(value).strip()
    text = re.sub(r"^\s*\d+\s*-\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return COST_CENTER_ALIASES.get(text, text)


def parse_date_br(value: object) -> dt.date:
    text = str(value).strip()
    day, month, year = map(int, text.split("/"))
    return dt.date(year, month, day)


def excel_date(value: object) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid spreadsheet date: {value!r}")


def money_to_cents(value: object, *, brazilian_text: bool = False) -> int:
    if value is None or value == "":
        raise ValueError("Empty monetary value")
    text = str(value).strip().replace("R$", "").replace(" ", "")
    if brazilian_text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        amount = Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary value: {value!r}") from exc
    return int(amount * 100)


def cents_to_float(cents: int) -> float:
    return float(Decimal(cents) / Decimal(100))
