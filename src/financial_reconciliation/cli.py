from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .constants import VERSION
from .models import MatchingPolicy
from .service import process, summary_text


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile a DDA spreadsheet with an ERP PDF export."
    )
    parser.add_argument("--dda", type=Path, help="DDA spreadsheet (.xlsx)")
    parser.add_argument("--pdf", type=Path, help="ERP report (.pdf)")
    parser.add_argument("--out", type=Path, help="Output spreadsheet (.xlsx)")
    parser.add_argument(
        "--max-date-delta",
        type=int,
        default=31,
        help="Maximum due-date difference for document-based review matches",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    if args.dda or args.pdf or args.out:
        if not args.dda or not args.pdf:
            print("Error: use --dda and --pdf together.", file=sys.stderr)
            return 2
        if args.max_date_delta < 0:
            print("Error: --max-date-delta must be non-negative.", file=sys.stderr)
            return 2
        output_path = args.out or args.dda.with_name(
            f"{args.dda.stem}_RECONCILIADO.xlsx"
        )
        policy = MatchingPolicy(
            max_document_date_delta_days=args.max_date_delta
        )
        try:
            summary = process(args.dda, args.pdf, output_path, policy)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(summary_text(summary))
        return 0

    from .gui import run_gui

    run_gui()
    return 0
