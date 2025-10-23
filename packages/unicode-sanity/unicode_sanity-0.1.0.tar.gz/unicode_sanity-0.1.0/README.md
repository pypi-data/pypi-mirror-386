# unicode-sanity

**Clean messy Unicode text**: remove or escape invisible/bidi control characters, normalize to a consistent form, and optionally remove/alias emoji — with a clear, human-readable report of what changed.

## Why?
Copy-pasted or scraped text often contains **invisible junk** (zero-width spaces, bidi control marks, BOMs) that break searching, matching, and CSV exports. `unicode-sanity` fixes these safely and explains what it did.

## Install
```bash
pip install unicode-sanity
```

## Usage

### CLI
Run the sanitizer against a file or standard input:

```bash
unicode-sanity input.txt --out cleaned.txt --policy safe --escape-format brackets --explain --stats
```

- `--policy strict` removes invisible/bidi characters (default).
- `--policy safe` replaces them with visible tags such as `[ZERO_WIDTH_SPACE]`.
- `--policy audit` leaves text unchanged and only reports findings.
- Add `--emoji remove` to strip emoji or `--emoji alias` to turn them into `:shortcodes:`.
- `--normalize` controls Unicode normalization (`NFC`, `NFKC`, `NFD`, `NFKD`, or `none`).

### Python API

```python
from unicode_sanity import sanitize

result = sanitize("Cafe\u0301 \u200B", policy="safe", emoji="alias", explain=True)
print(result.text)
# -> Café <ZERO_WIDTH_SPACE>
print(result.report)
# -> ['normalized to NFC', 'escaped 1 invisible/bidi character(s)', 'converted emoji to aliases']
```

The `sanitize` helper returns a `CleanResult` dataclass with the cleaned text, an optional report, and per-issue counts that are handy for dashboards or logs.
