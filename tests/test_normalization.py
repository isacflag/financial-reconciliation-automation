import datetime as dt
import unittest

from financial_reconciliation.normalization import (
    compact,
    document_ids,
    excel_date,
    money_to_cents,
)


class NormalizationTests(unittest.TestCase):
    def test_removes_labels_accents_and_spaces(self):
        self.assertEqual(
            compact("Beneficiário: Açúcar & Cia", remove_labels=True),
            "ACUCARCIA",
        )

    def test_repeated_document_is_reduced(self):
        self.assertIn("123456", document_ids("Nº Doc.: 123456123456"))

    def test_brazilian_money(self):
        self.assertEqual(
            money_to_cents("R$ 1.234,56", brazilian_text=True), 123456
        )

    def test_excel_date_formats(self):
        expected = dt.date(2026, 8, 10)
        self.assertEqual(excel_date("10/08/2026"), expected)
        self.assertEqual(excel_date("2026-08-10"), expected)


if __name__ == "__main__":
    unittest.main()
