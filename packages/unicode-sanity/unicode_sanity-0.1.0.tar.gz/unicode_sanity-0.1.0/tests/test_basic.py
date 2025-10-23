from unicode_sanity import sanitize

def test_removes_zero_width_strict():
    text = "pass\u200Bword"  # ZERO WIDTH SPACE
    res = sanitize(text, policy="strict", explain=True)
    assert res.text == "password"
    assert any("removed" in line for line in res.report)

def test_escapes_bidi_safe():
    text = "abc\u202Edef"  # RIGHT-TO-LEFT OVERRIDE
    res = sanitize(text, policy="safe", explain=True, escape_format="brackets")
    assert "abc" in res.text and "def" in res.text
    assert "[RIGHT_TO_LEFT_OVERRIDE]" in res.text
    assert any("escaped" in line for line in res.report)

def test_audit_detects():
    text = "x\u200C\u200Dy"
    res = sanitize(text, policy="audit", explain=True)
    assert res.text == text  # unchanged
    assert any("audit: found" in line for line in res.report)

def test_normalize_nfc():
    # LATIN SMALL LETTER E + COMBINING ACUTE ACCENT -> 'é'
    text = "Cafe\u0301"
    res = sanitize(text, normalize="NFC", explain=True)
    assert res.text == "Café"
    assert any("normalized to NFC" in line for line in res.report)

def test_emoji_alias():
    text = "Hi 🙂"
    res = sanitize(text, emoji="alias", explain=True)
    assert ":slightly_smiling_face:" in res.text or ":slight_smile:" in res.text
    assert any("converted emoji to aliases" in line for line in res.report)

def test_emoji_remove():
    text = "Hi 🙂"
    res = sanitize(text, emoji="remove", explain=True)
    assert "🙂" not in res.text
    assert any("removed emoji" in line for line in res.report)
