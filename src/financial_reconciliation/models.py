from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PdfRecord:
    record_id: int
    page: int
    cost_center: str
    creditor: str
    document: str
    launch: str
    due_date: dt.date
    cents: int
    ppc: bool


@dataclass(frozen=True)
class DdaRecord:
    row: int
    beneficiary: str
    document: str
    due_date: dt.date
    cents: int


@dataclass(frozen=True)
class Candidate:
    score: float
    dda: DdaRecord
    pdf: PdfRecord
    criterion: str
    confidence: str


@dataclass(frozen=True)
class MatchingPolicy:
    """Conservative defaults for automatic financial reconciliation."""

    money_tolerance_cents: int = 1
    max_document_date_delta_days: int = 31
    min_vendor_similarity_for_date_divergence: float = 0.75
    min_vendor_similarity_for_mutual_match: float = 0.75

    def __post_init__(self) -> None:
        if self.money_tolerance_cents < 0:
            raise ValueError("money_tolerance_cents must be non-negative")
        if self.max_document_date_delta_days < 0:
            raise ValueError("max_document_date_delta_days must be non-negative")
        for value in (
            self.min_vendor_similarity_for_date_divergence,
            self.min_vendor_similarity_for_mutual_match,
        ):
            if not 0 <= value <= 1:
                raise ValueError("similarity thresholds must be between 0 and 1")


@dataclass
class ProcessSummary:
    dda_rows: int
    pdf_records: int
    matched: int
    auto_matched: int
    review_required: int
    launched: int
    ppc: int
    not_found: int
    outside_period: int
    conflicts: int
    unused_pdf_records: int
    output_path: Path
