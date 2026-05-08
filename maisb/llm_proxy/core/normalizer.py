# core/normalizer.py
# Layer 1 — Input Ingestion & Normalization
#
# Runs BEFORE any detection. Strips obfuscation so that pattern matching
# and semantic scoring operate on clean, canonical text.
#
# Covers:
#   - HTML tag stripping
#   - URI / percent-encoding decoding
#   - Base64 detection + decoding
#   - Unicode homoglyph normalization (Cyrillic, lookalikes → ASCII)
#   - Whitespace collapse
#   - Hidden-surface marker extraction (for webview)

import re
import base64
import unicodedata
from html.parser import HTMLParser
from urllib.parse import unquote


# ── HTML stripper ─────────────────────────────────────────────────────────────

class _HTMLTextExtractor(HTMLParser):
    """Extract visible + hidden text from HTML."""

    HIDDEN_ATTRS = {"display:none", "visibility:hidden", "color:white",
                    "color:#fff", "color:#ffffff", "font-size:0", "opacity:0"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden_parts = []
        self._in_hidden = False

    def handle_starttag(self, tag, attrs):
        style = dict(attrs).get("style", "").lower().replace(" ", "")
        if any(h in style for h in self.HIDDEN_ATTRS):
            self._in_hidden = True

    def handle_endtag(self, tag):
        self._in_hidden = False

    def handle_data(self, data):
        cleaned = data.strip()
        if not cleaned:
            return
        if self._in_hidden:
            self.hidden_parts.append(cleaned)
        else:
            self.parts.append(cleaned)


def strip_html(text: str) -> tuple[str, list[str]]:
    """
    Returns (visible_text, hidden_text_parts).
    hidden_text_parts is non-empty only when attacker used CSS hiding.
    """
    extractor = _HTMLTextExtractor()
    try:
        extractor.feed(text)
    except Exception:
        pass
    visible = " ".join(extractor.parts)
    return visible, extractor.hidden_parts


# ── URI decoding ──────────────────────────────────────────────────────────────

def decode_uri(text: str) -> str:
    """Decode percent-encoding once. Handles double-encoding."""
    try:
        decoded = unquote(text, errors="replace")
        # decode again in case of double-encoding
        decoded2 = unquote(decoded, errors="replace")
        return decoded2 if decoded2 != decoded else decoded
    except Exception:
        return text


# ── Base64 detection ──────────────────────────────────────────────────────────

_B64_RE = re.compile(r"(?:[A-Za-z0-9+/]{20,}={0,2})")

def decode_base64_fragments(text: str) -> str:
    """
    Find base64-like fragments >= 20 chars, attempt decode, append
    decoded text after the original. Doesn't remove original.
    """
    extra = []
    for match in _B64_RE.finditer(text):
        fragment = match.group()
        try:
            decoded = base64.b64decode(fragment + "==").decode("utf-8", errors="ignore")
            if len(decoded) > 5 and decoded.isprintable():
                extra.append(decoded)
        except Exception:
            pass
    if extra:
        return text + " " + " ".join(extra)
    return text


# ── Homoglyph normalization ───────────────────────────────────────────────────
# Maps common Cyrillic/Greek/lookalike chars used in injection attacks to ASCII.

HOMOGLYPH_MAP = str.maketrans({
    # Cyrillic lookalikes
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X",
    # Greek lookalikes
    "ο": "o", "Ο": "O", "ν": "v",
    # Unicode punctuation → ASCII
    "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-",
    # Zero-width chars (invisible but break pattern matching)
    "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": "",
    "\u00ad": "",  # soft hyphen
})

def normalize_homoglyphs(text: str) -> str:
    return text.translate(HOMOGLYPH_MAP)


# ── Whitespace collapse ───────────────────────────────────────────────────────

def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ── Main normalizer ───────────────────────────────────────────────────────────

class NormalizationResult:
    def __init__(self, normalized: str, hidden_fragments: list[str],
                 had_html: bool, had_base64: bool, had_homoglyphs: bool):
        self.normalized       = normalized
        self.hidden_fragments = hidden_fragments   # non-empty = CSS hiding attack
        self.had_html         = had_html
        self.had_base64       = had_base64
        self.had_homoglyphs   = had_homoglyphs


def normalize(raw: str, channel: str = "unknown") -> NormalizationResult:
    """
    Full normalization pipeline. Call this at Layer 1 before any detection.

    Returns NormalizationResult with:
      .normalized       — clean text for detection
      .hidden_fragments — CSS-hidden text found in HTML (webview attack signal)
      .had_*            — flags for detection engine to use as bonus signals
    """
    text = raw

    # 1. URI decode (always — even non-URL text can have %XX)
    text = decode_uri(text)

    # 2. HTML strip (extract hidden text separately)
    hidden_fragments = []
    had_html = bool(re.search(r"<[a-zA-Z][^>]*>", text))
    if had_html:
        visible, hidden_fragments = strip_html(text)
        # Include hidden text in normalized output so detection catches it
        if hidden_fragments:
            text = visible + " " + " ".join(hidden_fragments)
        else:
            text = visible

    # 3. Base64 decode fragments
    before_b64 = text
    text = decode_base64_fragments(text)
    had_base64 = (text != before_b64)

    # 4. Homoglyph normalization
    before_hg = text
    text = normalize_homoglyphs(text)
    had_homoglyphs = (text != before_hg)

    # 5. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 6. Collapse whitespace
    text = collapse_whitespace(text)

    return NormalizationResult(
        normalized=text,
        hidden_fragments=hidden_fragments,
        had_html=had_html,
        had_base64=had_base64,
        had_homoglyphs=had_homoglyphs,
    )
