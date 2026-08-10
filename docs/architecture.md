# Architecture and matching policy

## Data flow

1. `pdf_io` extracts structured payable records from a text-based ERP PDF.
2. `excel_io` reads the DDA spreadsheet and locates required columns.
3. `matching` creates conservative candidates and prevents reuse of a PDF row.
4. `service` classifies unmatched rows and writes an auditable workbook.
5. `cli` and `gui` expose the same processing service.

## Safety rules

- A PDF record can be assigned only once.
- A one-cent difference is accepted only with a strong document match.
- A document match with a different date is limited to 31 days by default and
  also requires beneficiary similarity.
- Duplicate date/value groups are never paired merely because both sides have
  the same number of rows.
- Medium-confidence candidates are marked `REVISAR`, not `LANÇADO`.
- The source spreadsheet cannot be overwritten through the processing API.

## Known limitations

- Scanned/image-only PDFs require OCR before processing.
- PDF layouts vary; new ERP layouts may require parser adapters.
- Matching rules must be validated by a domain owner before production use.
- This project supports reconciliation; it does not post financial entries to
  an ERP or bank.
