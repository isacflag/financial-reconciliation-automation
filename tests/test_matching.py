import datetime as dt
import unittest

from financial_reconciliation.matching import match_records
from financial_reconciliation.models import DdaRecord, PdfRecord


BASE_DATE = dt.date(2026, 8, 10)


def pdf_record(
    record_id: int,
    creditor: str,
    document: str,
    cents: int,
    *,
    due_date: dt.date = BASE_DATE,
) -> PdfRecord:
    return PdfRecord(
        record_id=record_id,
        page=1,
        cost_center="PROJECT ALPHA",
        creditor=creditor,
        document=document,
        launch=f"L-{record_id}",
        due_date=due_date,
        cents=cents,
        ppc=False,
    )


class MatchingTests(unittest.TestCase):
    def test_document_allows_one_cent_difference(self):
        dda = DdaRecord(2, "ACME", "123456", BASE_DATE, 10001)
        matches, _, _ = match_records(
            [dda], [pdf_record(0, "ACME LTDA", "NF 123456", 10000)]
        )
        self.assertEqual(matches[2].confidence, "ALTA")

    def test_one_pdf_cannot_be_reused(self):
        ddas = [
            DdaRecord(2, "ACME", "123456", BASE_DATE, 10000),
            DdaRecord(3, "ACME", "123456", BASE_DATE, 10000),
        ]
        matches, _, used = match_records(
            ddas, [pdf_record(0, "ACME", "123456", 10000)]
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(used), 1)

    def test_far_date_and_different_vendor_are_not_matched(self):
        dda = DdaRecord(2, "DIFFERENT VENDOR", "123456", BASE_DATE, 10000)
        old_date = dt.date(2024, 1, 1)
        matches, _, _ = match_records(
            [dda],
            [pdf_record(0, "OTHER COMPANY", "123456", 10000, due_date=old_date)],
        )
        self.assertNotIn(2, matches)

    def test_ambiguous_duplicate_group_is_not_guessed(self):
        ddas = [
            DdaRecord(2, "VENDOR ONE", "", BASE_DATE, 10000),
            DdaRecord(3, "VENDOR TWO", "", BASE_DATE, 10000),
        ]
        pdfs = [
            pdf_record(0, "UNRELATED A", "", 10000),
            pdf_record(1, "UNRELATED B", "", 10000),
        ]
        matches, _, _ = match_records(ddas, pdfs)
        self.assertEqual(matches, {})

    def test_mutual_vendor_match_resolves_duplicate_group(self):
        ddas = [
            DdaRecord(2, "ALPHA SERVICES", "", BASE_DATE, 10000),
            DdaRecord(3, "BETA SUPPLIES", "", BASE_DATE, 10000),
        ]
        pdfs = [
            pdf_record(0, "BETA SUPPLIES LTDA", "", 10000),
            pdf_record(1, "ALPHA SERVICES LTDA", "", 10000),
        ]
        matches, _, _ = match_records(ddas, pdfs)
        self.assertEqual(matches[2].pdf.record_id, 1)
        self.assertEqual(matches[3].pdf.record_id, 0)


if __name__ == "__main__":
    unittest.main()
