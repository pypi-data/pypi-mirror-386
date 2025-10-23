from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .core import sanitize, SanitizePolicy, EmojiPolicy, NormalizeForm


def _read_input(path: str) -> str:
    if path == "-" or path == "":
        return sys.stdin.read()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    return p.read_text(encoding="utf-8", errors="replace")


def _write_output(path: Optional[str], content: str) -> None:
    if not path or path == "-":
        sys.stdout.write(content)
        return
    Path(path).write_text(content, encoding="utf-8")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="unicode-sanity",
        description="Clean invisible/bidi Unicode characters, normalize text, and optionally handle emoji — with an explainable report.",
    )
    parser.add_argument("input", help="Input file path or '-' for stdin")
    parser.add_argument("--out", help="Output file path (default: stdout). Use '-' to print to stdout.", default="-")

    parser.add_argument(
        "--policy",
        choices=["strict", "safe", "audit"],
        default="strict",
        help="How to treat invisible/bidi chars: 'strict' remove, 'safe' escape with tags, 'audit' only report.",
    )
    parser.add_argument(
        "--normalize",
        choices=["NFC", "NFKC", "NFD", "NFKD", "none"],
        default="NFC",
        help="Unicode normalization form (default NFC). Use 'none' to skip.",
    )
    parser.add_argument(
        "--emoji",
        choices=["keep", "remove", "alias"],
        default="keep",
        help="Emoji handling: keep (default), remove, or alias to :shortcodes:.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Include a human-readable report on stderr of what was changed/found.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print a short stats line on stderr (counts).",
    )
    parser.add_argument(
        "--escape-format",
        choices=["angle", "brackets"],
        default="angle",
        help="When --policy=safe, choose <TAG> or [TAG] style (default: angle).",
    )

    args = parser.parse_args(argv)

    try:
        raw = _read_input(args.input)
        result = sanitize(
            raw,
            policy=args.policy,            # type: ignore[arg-type]
            normalize=args.normalize,      # type: ignore[arg-type]
            emoji=args.emoji,              # type: ignore[arg-type]
            explain=args.explain or args.stats,
            escape_format=args.escape_format,  # type: ignore[arg-type]
        )
        _write_output(args.out, result.text)

        if args.explain:
            if result.report:
                sys.stderr.write("\n".join(f"[unicode-sanity] {line}" for line in result.report) + "\n")
            else:
                sys.stderr.write("[unicode-sanity] no changes\n")

        if args.stats:
            if result.counts:
                pairs = " ".join(f"{k}={v}" for k, v in sorted(result.counts.items()))
                sys.stderr.write(f"[unicode-sanity] stats {pairs}\n")
            else:
                sys.stderr.write("[unicode-sanity] stats none\n")

        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        sys.stderr.write(f"[unicode-sanity] error: {e}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
