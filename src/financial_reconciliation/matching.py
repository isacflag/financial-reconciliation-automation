from __future__ import annotations

import datetime as dt
from collections import defaultdict
from difflib import SequenceMatcher

from .models import Candidate, DdaRecord, MatchingPolicy, PdfRecord
from .normalization import compact, document_ids


def vendor_similarity(left: object, right: object) -> float:
    left_compact = compact(left, remove_labels=True)
    right_compact = compact(right, remove_labels=True)
    if not left_compact or not right_compact:
        return 0.0
    if left_compact in right_compact or right_compact in left_compact:
        return min(len(left_compact), len(right_compact)) / max(
            len(left_compact), len(right_compact)
        )
    return SequenceMatcher(None, left_compact, right_compact).ratio()


def has_strong_document_match(
    dda: DdaRecord, pdf: PdfRecord, name_similarity: float
) -> bool:
    overlap = document_ids(dda.document) & document_ids(pdf.document)
    if any(len(identifier) >= 5 for identifier in overlap):
        return True
    return name_similarity >= 0.75 and any(
        len(identifier) == 4 for identifier in overlap
    )


def build_candidates(
    dda_records: list[DdaRecord],
    pdf_records: list[PdfRecord],
    policy: MatchingPolicy,
) -> tuple[list[Candidate], dict[int, list[Candidate]]]:
    dda_by_key: dict[tuple[dt.date, int], list[DdaRecord]] = defaultdict(list)
    pdf_by_key: dict[tuple[dt.date, int], list[PdfRecord]] = defaultdict(list)
    for dda in dda_records:
        dda_by_key[(dda.due_date, dda.cents)].append(dda)
    for pdf in pdf_records:
        pdf_by_key[(pdf.due_date, pdf.cents)].append(pdf)

    candidates: list[Candidate] = []
    by_dda: dict[int, list[Candidate]] = defaultdict(list)

    for dda in dda_records:
        for pdf in pdf_records:
            amount_delta = abs(dda.cents - pdf.cents)
            date_delta = abs((dda.due_date - pdf.due_date).days)
            same_key = dda.due_date == pdf.due_date and dda.cents == pdf.cents
            similarity = vendor_similarity(dda.beneficiary, pdf.creditor)
            strong_document = has_strong_document_match(dda, pdf, similarity)

            criterion: str | None = None
            confidence: str | None = None
            score: float | None = None

            if strong_document and amount_delta <= policy.money_tolerance_cents:
                if date_delta == 0:
                    score = 120.0 + similarity * 5.0
                    confidence = "ALTA"
                    criterion = (
                        "DOCUMENTO + DATA + VALOR"
                        if amount_delta == 0
                        else "DOCUMENTO + DATA + DIFERENÇA DE R$ 0,01"
                    )
                elif (
                    date_delta <= policy.max_document_date_delta_days
                    and similarity
                    >= policy.min_vendor_similarity_for_date_divergence
                ):
                    score = 105.0 + similarity * 5.0 - date_delta * 0.1
                    confidence = "MÉDIA"
                    signed_delta = (dda.due_date - pdf.due_date).days
                    criterion = (
                        "DOCUMENTO + BENEFICIÁRIO + VALOR "
                        f"(DATA DDA {signed_delta:+d} DIA(S) DO ERP)"
                    )

            elif same_key:
                key = (dda.due_date, dda.cents)
                dda_group = dda_by_key[key]
                pdf_group = pdf_by_key[key]

                matching_pdfs = [
                    item
                    for item in pdf_group
                    if vendor_similarity(dda.beneficiary, item.creditor)
                    >= policy.min_vendor_similarity_for_mutual_match
                ]
                matching_ddas = [
                    item
                    for item in dda_group
                    if vendor_similarity(item.beneficiary, pdf.creditor)
                    >= policy.min_vendor_similarity_for_mutual_match
                ]
                mutual_name_match = (
                    len(matching_pdfs) == 1 and len(matching_ddas) == 1
                )

                if mutual_name_match:
                    score = 100.0 + similarity * 5.0
                    confidence = "ALTA"
                    criterion = "BENEFICIÁRIO + DATA + VALOR"
                elif len(dda_group) == 1 and len(pdf_group) == 1:
                    score = 70.0 + similarity * 5.0
                    confidence = "MÉDIA"
                    criterion = "DATA + VALOR (PAR ÚNICO — REVISAR)"

            if score is None or criterion is None or confidence is None:
                continue

            candidate = Candidate(
                score=score,
                dda=dda,
                pdf=pdf,
                criterion=criterion,
                confidence=confidence,
            )
            candidates.append(candidate)
            by_dda[dda.row].append(candidate)

    return candidates, by_dda


def match_records(
    dda_records: list[DdaRecord],
    pdf_records: list[PdfRecord],
    policy: MatchingPolicy | None = None,
) -> tuple[dict[int, Candidate], dict[int, list[Candidate]], set[int]]:
    effective_policy = policy or MatchingPolicy()
    candidates, candidates_by_dda = build_candidates(
        dda_records, pdf_records, effective_policy
    )
    candidates.sort(key=lambda item: (-item.score, item.dda.row, item.pdf.record_id))

    matches: dict[int, Candidate] = {}
    used_pdf_ids: set[int] = set()
    for candidate in candidates:
        if candidate.dda.row in matches:
            continue
        if candidate.pdf.record_id in used_pdf_ids:
            continue
        matches[candidate.dda.row] = candidate
        used_pdf_ids.add(candidate.pdf.record_id)

    return matches, candidates_by_dda, used_pdf_ids
