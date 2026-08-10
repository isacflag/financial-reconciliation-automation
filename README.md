# Financial Reconciliation Automation

Python application that reconciles a DDA spreadsheet with an accounts-payable
report exported from an ERP. It combines document number, beneficiary, due date
and value, prevents duplicate use of source records, and produces an Excel file
with confidence levels and an audit trail.

> **Portfolio status:** beta. Use the fictional demo files for evaluation. Do
> not use the project in production without validating the input layout and the
> organization's matching policy.

## Why this project exists

Financial teams often compare bank DDA spreadsheets with ERP exports manually.
That process is repetitive and risky when documents, dates or vendor names are
slightly different. This project converts the comparison into a traceable
workflow while sending uncertain matches to manual review.

## Features

- Reads `.xlsx` DDA spreadsheets and text-based ERP PDF tables.
- Normalizes accents, labels, repeated values and Brazilian currency formats.
- Matches by document, beneficiary, due date and amount.
- Allows a one-cent tolerance only when a document match exists.
- Prevents one ERP record from being assigned to multiple DDA rows.
- Marks medium-confidence candidates as `REVISAR`.
- Adds source page, creditor, document, launch, date, value and criterion to the
  output workbook.
- Works through a desktop interface or command line.
- Includes automated tests and fictional demonstration data.

## Tech stack

- Python 3.10+
- `pdfplumber` for PDF table extraction
- `openpyxl` for Excel processing
- Tkinter for the optional desktop interface
- `unittest` for automated tests

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
```

Run the fictional demo:

```bash
financial-reconciliation \
  --dda examples/dda_demo.xlsx \
  --pdf examples/erp_report_demo.pdf \
  --out examples/dda_demo_RECONCILIADO.xlsx
```

Run without arguments to open the desktop interface:

```bash
financial-reconciliation
```

## Tests

```bash
python -m unittest discover -s tests -v
```

The test suite includes document/amount tolerance, duplicate prevention,
ambiguous groups, distant dates, PDF table parsing and an end-to-end workbook
test.

## Matching policy

The public version is intentionally conservative:

- document/date/value matches can be automatic;
- different dates require beneficiary similarity and are limited to 31 days;
- unique date/value pairs without supporting identity are marked for review;
- ambiguous duplicate groups are not guessed.

See [the architecture notes](docs/architecture.md) for details.

## Privacy and anonymization

The public repository contains no employer files, customer data, banking data,
credentials or organization-specific cost centers. All examples are fictional.
Keep production aliases and input files outside source control.

## AI-assisted development

AI tools assisted with code generation, refactoring and review. The repository
does not present AI-generated output as proof by itself: the matching behavior
is documented, covered by tests and designed for human review when confidence
is not high. A domain owner must still validate the rules before production use.

## Background / Resumo em português

Projeto de portfólio para automatizar a conciliação entre uma planilha DDA e um
relatório de contas a pagar exportado de um ERP. A aplicação lê PDF e Excel,
aplica regras de negócio, bloqueia duplicidades e gera uma planilha auditável.
Casos de confiança média são marcados como `REVISAR`.

## License

MIT — see [LICENSE](LICENSE).
