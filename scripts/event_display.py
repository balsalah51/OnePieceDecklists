"""Normalize tournament labels and keep placeholder events off the homepage."""

from __future__ import annotations

import html
import re

TEST_RE = re.compile(
    r"(tournoi\s*test|\btest\s+tournament\b|\btest\s+event\b)",
    re.I,
)
HREF_RE = re.compile(r"tournoi-test|test-tournament", re.I)
SOURCE_PREFIX_RE = re.compile(
    r"^(?:public\s+(?:optcg\.gg|onepiecedb|tcg\s*portal)\s+list|"
    r"youtube\s+(?:list|deck\s+profile)|x\s+list|community\s+list)\s*·\s*",
    re.I,
)
SOURCE_TAIL_RE = re.compile(
    r"(?:\s*·\s*)?(?:public\s+list(?:\s+from\s+[\w.]+)?|also\s+on\s+x\s+@\S+)\s*$",
    re.I,
)
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
SOURCE_PIECE_RE = re.compile(
    r"^(?:public\s+list(?:\s+from\s+[\w.]+)?|optcg\.gg|onepiecedb|tcg\s*portal|youtube|web)$",
    re.I,
)
BRACKET_RE = re.compile(r"^\s*\[([^\]]+)\]\s*")
PIPE_RE = re.compile(r"\s*\|\s*")
DASH_SPLIT = re.compile(r"\s+[-–—]\s+")
MULTI_SPACE = re.compile(r"\s+")
ONE_PIECE_RE = re.compile(r"\bONE\s+PIECE\b", re.I)
TRAIL_SET_RE = re.compile(r"[-:\s]+(?:OP|EB|ST)\d+(?:\.\d+)?\s*$", re.I)
SET_ONLY_RE = re.compile(r"^(?:OP|EB|ST|EGB)\d*(?:\.\d+)?$", re.I)
NAMED_SERIES = re.compile(
    r"rumble league|chinoizecup|versus cup|treasure cup|regional|championship|"
    r"flagship|nationals|finals|league|liga|cup",
    re.I,
)

PHRASES = [
    (re.compile(r"\brumble\s+league\b", re.I), "Rumble League"),
    (re.compile(r"\bchinoize\s*cup\b", re.I), "ChinoizeCup"),
    (re.compile(r"\bwin\s+a\s+box\b", re.I), "Win a Box"),
    (re.compile(r"\bwin\s+a\s+case\b", re.I), "Win a Case"),
    (re.compile(r"\bversus\s+cup\b", re.I), "Versus Cup"),
    (re.compile(r"\btreasure\s+cups?\b", re.I), "Treasure Cup"),
    (re.compile(r"\bstore\s+championships?\b", re.I), "Store Championship"),
    (re.compile(r"\broad\s+to\s+finals\b", re.I), "Road to Finals"),
    (re.compile(r"\bregional\s+championships?\b", re.I), "Regional"),
    (re.compile(r"\bregionals?\b", re.I), "Regional"),
    (re.compile(r"\bnationals?\b", re.I), "Nationals"),
    (re.compile(r"\bflagship\b", re.I), "Flagship"),
    (re.compile(r"\bchampionships?\b", re.I), "Championship"),
    (re.compile(r"\bextra\s+grand\s+battle\b", re.I), "Extra Grand Battle"),
    (re.compile(r"\bliga\s+phoenix\b", re.I), "Liga Phoenix"),
    (re.compile(r"\bmana\b", re.I), "Mana"),
]


def is_test_row(row: dict) -> bool:
    """True for placeholder events such as Tournoi Test and Player01."""
    blob = " ".join(
        str(row.get(key) or "")
        for key in (
            "tournament_name",
            "tournament",
            "subtitle",
            "title",
            "title_override",
            "href",
            "slug",
        )
    )
    if TEST_RE.search(blob) or HREF_RE.search(blob):
        return True
    player = str(row.get("player") or "").strip()
    return bool(re.fullmatch(r"player\d+", player, re.I) and re.search(r"test", blob, re.I))


def _tidy_piece(text: str) -> str:
    text = ONE_PIECE_RE.sub("", text)
    text = TRAIL_SET_RE.sub("", text)
    text = text.replace("°", "")
    text = MULTI_SPACE.sub(" ", text).strip(" -–—·,")
    for pattern, replacement in PHRASES:
        text = pattern.sub(replacement, text)
    return MULTI_SPACE.sub(" ", text).strip(" -–—·")


def display_event(raw: str) -> str:
    """Turn a source event title into a short label for the homepage."""
    original = (raw or "").strip()
    original = SOURCE_PREFIX_RE.sub("", original)
    original = ISO_DATE_RE.sub("", original)
    for _ in range(3):
        cleaned = SOURCE_TAIL_RE.sub("", original).strip(" ·")
        if cleaned == original:
            break
        original = cleaned
    if not original:
        return ""
    text = original
    tag = ""
    match = BRACKET_RE.match(text)
    if match:
        tag = match.group(1).strip()
        text = text[match.end() :]
    pieces: list[str] = []
    for chunk in PIPE_RE.split(text):
        bits = [bit for bit in DASH_SPLIT.split(chunk) if bit.strip()]
        pieces.extend(bits if len(bits) >= 2 else [chunk])
    cleaned: list[str] = []
    seen: set[str] = set()
    for piece in pieces:
        piece = _tidy_piece(piece)
        key = piece.lower()
        if not piece or key in seen or SET_ONLY_RE.fullmatch(piece) or SOURCE_PIECE_RE.fullmatch(piece):
            continue
        seen.add(key)
        cleaned.append(piece)

    def series_rank(piece: str) -> int:
        return 0 if NAMED_SERIES.search(piece) else 1

    cleaned.sort(key=series_rank)
    name = " · ".join(cleaned)
    if tag.upper() == "EGB" and "extra grand battle" not in name.lower():
        name = f"Extra Grand Battle · {name}" if name else "Extra Grand Battle"
    if name:
        return name
    if tag and not SET_ONLY_RE.fullmatch(tag):
        tidied = _tidy_piece(tag)
        if tidied:
            return tidied
    return original


def event_weight(raw: str) -> int:
    """Higher means a larger offline event. Online cups stay at 0."""
    name = (raw or "").lower()
    if "store championship" in name:
        return 2
    if any(token in name for token in ("championship", "flagship", "nationals", "worlds")):
        return 3
    if "regional" in name or "treasure cup" in name or "road to finals" in name or re.search(r"\bfinals\b", name):
        return 2
    if "liga " in name or "liga phoenix" in name or "offline" in name:
        return 1
    return 0


def event_badge(raw: str) -> str:
    name = (raw or "").lower()
    if "store championship" in name:
        return "Store Championship"
    if any(token in name for token in ("championship", "flagship", "nationals", "worlds")):
        return "Championship"
    if "regional" in name:
        return "Regional"
    if "treasure cup" in name:
        return "Treasure Cup"
    if "road to finals" in name or re.search(r"\bfinals\b", name):
        return "Finals"
    if event_weight(raw) >= 1:
        return "League"
    return ""


def event_note_html(raw: str, when: str = "") -> str:
    label = display_event(raw)
    badge = event_badge(raw)
    parts: list[str] = []
    if badge:
        kind = "major" if event_weight(raw) >= 2 else "league"
        parts.append(f'<span class="event-rank event-rank-{kind}">{html.escape(badge)}</span>')
    text = html.escape(label)
    if when and when not in label:
        text = f"{text} · {html.escape(when)}"
    parts.append(text)
    return " ".join(parts)
