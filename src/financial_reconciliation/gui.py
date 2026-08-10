from __future__ import annotations

import traceback
from pathlib import Path

from .constants import VERSION
from .service import process, summary_text


def run_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title(f"Financial Reconciliation v{VERSION}")
    root.geometry("540x280")
    root.resizable(False, False)

    tk.Label(
        root,
        text=f"Financial Reconciliation v{VERSION}",
        font=("Arial", 16, "bold"),
    ).pack(pady=(28, 8))
    tk.Label(
        root,
        text=(
            "Reconcile a DDA spreadsheet with a text-based ERP PDF.\n"
            "Medium-confidence matches are marked for manual review."
        ),
        font=("Arial", 10),
        justify="center",
    ).pack(pady=(0, 24))

    def choose_and_run() -> None:
        dda = filedialog.askopenfilename(
            title="Choose the DDA spreadsheet",
            filetypes=[("Excel spreadsheet", "*.xlsx")],
        )
        if not dda:
            return
        pdf = filedialog.askopenfilename(
            title="Choose the ERP PDF report",
            filetypes=[("PDF file", "*.pdf")],
        )
        if not pdf:
            return

        dda_path = Path(dda)
        output_path = dda_path.with_name(f"{dda_path.stem}_RECONCILIADO.xlsx")
        try:
            summary = process(dda_path, Path(pdf), output_path)
        except Exception as exc:  # GUI must show the error instead of closing.
            messagebox.showerror(
                "Reconciliation error",
                f"{exc}\n\nTechnical details:\n{traceback.format_exc(limit=3)}",
            )
            return
        messagebox.showinfo("Completed", summary_text(summary))

    tk.Button(
        root,
        text="Select files and run",
        font=("Arial", 12, "bold"),
        command=choose_and_run,
        padx=18,
        pady=10,
    ).pack()
    root.mainloop()
