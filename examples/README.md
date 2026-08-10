# Fictional demo files

The files in this directory contain invented companies, documents and values.
They do not contain employer, customer, banking or production data.

After installing the project, run:

```bash
financial-reconciliation \
  --dda examples/dda_demo.xlsx \
  --pdf examples/erp_report_demo.pdf \
  --out examples/dda_demo_RECONCILIADO.xlsx
```

The output demonstrates:

- a high-confidence document/date/value match;
- a medium-confidence unique date/value pair marked `REVISAR`;
- a DDA row outside the PDF period.
