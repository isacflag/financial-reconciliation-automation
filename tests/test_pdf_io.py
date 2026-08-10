import datetime as dt
import unittest

from financial_reconciliation.pdf_io import parse_table_records


class PdfParserTests(unittest.TestCase):
    def test_parses_table_without_launch_column(self):
        table = [
            ["Centro de Custo: 001 - Project Alpha", "", "", ""],
            ["Credor", "Documento", "Data Vencto", "Total"],
            ["ACME LTDA", "NF 123456", "10/08/2026", "1.234,56"],
        ]
        records = parse_table_records(table, page_number=2)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].page, 2)
        self.assertEqual(records[0].cost_center, "PROJECT ALPHA")
        self.assertEqual(records[0].due_date, dt.date(2026, 8, 10))
        self.assertEqual(records[0].cents, 123456)
        self.assertEqual(records[0].launch, "")


if __name__ == "__main__":
    unittest.main()
