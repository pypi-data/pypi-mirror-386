from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

import emoji as emoji_lib

SanitizePolicy = Literal["strict", "safe", "audit"]
EmojiPolicy = Literal["keep", "remove", "alias"]
NormalizeForm = Literal["NFC", "NFKC", "NFD", "NFKD", "none"]


# Character sets targeted 
# Targets common invisible and bidirectional control characters found in real data.
# Variation selectors are not removed by default to preserve emoji rendering.


# Zero-width & word joiners (common culprits)
# U+00AD SOFT HYPHEN is visible in some renderers but often behaves invisibly.
# U+061C ARABIC LETTER MARK is bidi-related.
# U+180E MONGOLIAN VOWEL SEPARATOR (deprecated; still appears in old content).
# U+200B..U+200D ZWSP, ZWNJ, ZWJ
# U+2060 WORD JOINER
# U+FEFF ZERO WIDTH NO-BREAK SPACE (BOM)
ZW_BIDI_PATTERN = re.compile(
    r"[\u00AD\u061C\u180E\u200B-\u200D\u2060\uFEFF"
    r"\u200E-\u200F"          # LRM, RLM
    r"\u202A-\u202E"          # LRE, RLE, PDF, LRO, RLO
    r"\u2066-\u2069"          # LRI, RLI, FSI, PDI
    r"]"
)

# human-friendly tags for escape mode
NAME_OVERRIDES: Dict[int, str] = {
    0x00AD: "SOFT_HYPHEN",
    0x061C: "ARABIC_LETTER_MARK",
    0x180E: "MONGOLIAN_VOWEL_SEPARATOR",
    0x200B: "ZERO_WIDTH_SPACE",
    0x200C: "ZERO_WIDTH_NON_JOINER",
    0x200D: "ZERO_WIDTH_JOINER",
    0x200E: "LEFT_TO_RIGHT_MARK",
    0x200F: "RIGHT_TO_LEFT_MARK",
    0x202A: "LEFT_TO_RIGHT_EMBEDDING",
    0x202B: "RIGHT_TO_LEFT_EMBEDDING",
    0x202C: "POP_DIRECTIONAL_FORMATTING",
    0x202D: "LEFT_TO_RIGHT_OVERRIDE",
    0x202E: "RIGHT_TO_LEFT_OVERRIDE",
    0x2060: "WORD_JOINER",
    0x2066: "LEFT_TO_RIGHT_ISOLATE",
    0x2067: "RIGHT_TO_LEFT_ISOLATE",
    0x2068: "FIRST_STRONG_ISOLATE",
    0x2069: "POP_DIRECTIONAL_ISOLATE",
    0xFEFF: "ZERO_WIDTH_NO_BREAK_SPACE",
}

def _char_tag(ch: str) -> str:
    cp = ord(ch)
    name = NAME_OVERRIDES.get(cp)
    if not name:
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = f"U+{cp:04X}"
    return name


# --- Data model ---------------------------------------------------------------

@dataclass
class CleanResult:
    text: str
    report: List[str] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)  # per-issue counts


@dataclass
class SanitizeConfig:
    policy: SanitizePolicy = "strict"
    normalize: NormalizeForm = "NFC"
    emoji_policy: EmojiPolicy = "keep"
    explain: bool = True
    escape_format: Literal["angle", "brackets"] = "angle"
    # When True, only report findings instead of removing/escaping them.
    audit_only: bool = False  # set when policy == "audit"



# --- Core functionality -------------------------------------------------------

def sanitize(
    text: str,
    policy: SanitizePolicy = "strict",
    normalize: NormalizeForm = "NFC",
    emoji: EmojiPolicy = "keep",
    explain: bool = True,
    escape_format: Literal["angle", "brackets"] = "angle",
) -> CleanResult:
    """
    Clean text by normalizing Unicode and removing/escaping invisible/bidi controls,
    with optional emoji handling and a human-readable report.

     ... Returns a CleanResult (text, report, counts).

    """
    cfg = SanitizeConfig(
        policy=policy, normalize=normalize, emoji_policy=emoji, explain=explain,
        escape_format=escape_format, audit_only=(policy == "audit")
    )
    report: List[str] = []
    counts: Dict[str, int] = {}

    # 1) Normalize
    out = text
    if cfg.normalize and cfg.normalize != "none":
        normalized = unicodedata.normalize(cfg.normalize, out)
        if normalized != out:
            out = normalized
            if cfg.explain:
                report.append(f"normalized to {cfg.normalize}")
            counts["normalized"] = counts.get("normalized", 0) + 1  # normalization

    # 2) Handle targeted invisibles / bidi controls
    matches = list(ZW_BIDI_PATTERN.finditer(out))
    if matches:
        spans = [(m.start(), m.end(), out[m.start():m.end()]) for m in matches]
        if cfg.policy == "strict":
            # remove matched characters
            builder = []
            last = 0
            removed = 0
            for s, e, ch in spans:
                builder.append(out[last:s])
                last = e
                removed += len(ch)
            builder.append(out[last:])
            out = "".join(builder)
            if cfg.explain:
                report.append(f"removed {removed} invisible/bidi character(s)")
            counts["invisibles_removed"] = counts.get("invisibles_removed", 0) + removed

        elif cfg.policy == "safe":
            # escape matched characters as tags
            def esc(tag: str) -> str:
                return f"<{tag}>" if cfg.escape_format == "angle" else f"[{tag}]"

            builder = []
            last = 0
            escaped = 0
            for s, e, ch in spans:
                builder.append(out[last:s])
                builder.append(esc(_char_tag(ch)))
                last = e
                escaped += len(ch)
            builder.append(out[last:])
            out = "".join(builder)
            if cfg.explain:
                report.append(f"escaped {escaped} invisible/bidi character(s)")
            counts["invisibles_escaped"] = counts.get("invisibles_escaped", 0) + escaped

        elif cfg.policy == "audit":
            # audit only: report findings without modification
            if cfg.explain:
                per_name: Dict[str, int] = {}
                for _, _, ch in spans:
                    per_name[_char_tag(ch)] = per_name.get(_char_tag(ch), 0) + 1
                sorted_bits = ", ".join(f"{name}×{n}" for name, n in sorted(per_name.items()))
                report.append(f"audit: found {len(spans)} invisible/bidi char(s): {sorted_bits}")
            counts["invisibles_found"] = counts.get("invisibles_found", 0) + len(spans)

    # 3) Emoji handling
    if cfg.emoji_policy == "remove":
        new_out = emoji_lib.replace_emoji(out, replace="")
        if new_out != out:
            if cfg.explain:
                report.append("removed emoji")
            counts["emoji_removed"] = counts.get("emoji_removed", 0) + 1
        out = new_out

    elif cfg.emoji_policy == "alias":
        new_out = emoji_lib.demojize(out, language="en", delimiters=(":", ":"))
        if new_out != out:
            if cfg.explain:
                report.append("converted emoji to aliases")
            counts["emoji_aliased"] = counts.get("emoji_aliased", 0) + 1
        out = new_out

    return CleanResult(text=out, report=report if cfg.explain else [], counts=counts)
