"""Viewer highlight boxes for extracted values (frontend `source.boundingBox`).

The frontend draws one rectangle per field as ``[x, y, width, height]`` relative
to the rendered page (top-left origin, 0..1, ``RELATIVE_0_1``). Readings store
word boxes as ``[x1, y1, x2, y2]``; this module locates the quoted value and
converts the union of its word boxes. An unlocatable or ambiguous value yields
``None`` so the viewer shows the page and quote without guessing a position.

On a model-transcribed scan the quote comes from the transcript while the boxes
come from local OCR, whose spelling and reading order differ. Those pages fall
back to an approximate alignment that still refuses weak or ambiguous matches.
"""

from collections import Counter
from difflib import SequenceMatcher
from functools import lru_cache

from agent.review.reading import compact, locate

PADDING = 0.002
# Approximate alignment (transcribed pages only). The quote must resemble one stretch of OCR
# words clearly more than any other stretch, or no box is returned.
MIN_QUOTE_RATIO = 0.5
MIN_RAW_RATIO = 0.7
MIN_MARGIN = 0.08
MIN_RAW_MATCHED = 0.5
MIN_ANCHOR_TOKEN = 4


def evidence_page(page, quote):
    """A page is evidence only together with a quote.

    The model schema requires an integer page even for a value it did not find
    (empty quote), so that page number is filler and must not steer the viewer.
    """
    return page if isinstance(quote, str) and quote.strip() else None


def public_source(source):
    """Drop a quote-less page from a stored field source (also fixes older rows)."""
    if not isinstance(source, dict) or source.get("page") is None:
        return source
    page = evidence_page(source["page"], source.get("text"))
    if page is not None:
        return source
    return {**source, "page": None, "boundingBox": None}


def union_box(boxes):
    """Union of ``[x1, y1, x2, y2]`` boxes as a clamped ``[x, y, width, height]``."""
    valid = [
        box
        for box in boxes or []
        if isinstance(box, (list, tuple))
        and len(box) == 4
        and all(isinstance(value, (int, float)) for value in box)
    ]
    if not valid:
        return None
    x1 = max(0.0, min(box[0] for box in valid) - PADDING)
    y1 = max(0.0, min(box[1] for box in valid) - PADDING)
    x2 = min(1.0, max(box[2] for box in valid) + PADDING)
    y2 = min(1.0, max(box[3] for box in valid) + PADDING)
    x, y = round(x1, 6), round(y1, 6)
    # Rounding must never push the box past the page edge; the viewer rejects x+width>1.
    width = min(round(x2 - x1, 6), round(1.0 - x, 6))
    height = min(round(y2 - y1, 6), round(1.0 - y, 6))
    if width <= 0 or height <= 0:
        return None
    return [x, y, width, height]


def bounding_box(recognized, page, quote, raw=None):
    """Locate ``raw`` inside ``quote`` on ``page``; fall back to the whole quote."""
    layout = recognized.get("layout_pages") if isinstance(recognized, dict) else None
    if not isinstance(layout, list) or not isinstance(page, int) or not quote:
        return None
    reading = {"pages": layout}
    for needle in (raw, quote):
        if not needle:
            continue
        try:
            boxes = locate(reading, page, quote, str(needle))
        except (KeyError, TypeError, ValueError):
            return None
        box = union_box(boxes)
        if box is not None:
            return box
    sources = recognized.get("text_sources")
    if isinstance(sources, list) and 1 <= page <= len(sources) and sources[page - 1] == "model_transcription":
        try:
            return _approximate_box(layout, page, quote, raw)
        except (KeyError, TypeError, ValueError):
            return None
    return None


def _best_window(text, key, factors, floor):
    """``(ratio, start, length, rival)`` for the stretch of ``text`` most similar to ``key``.

    ``rival`` is the best ratio of any stretch that does not overlap the winner. A cheap
    character-count bound skips stretches that can neither win nor be a relevant rival.
    """
    if not text or not key:
        return None
    need, candidates = Counter(key), []
    for length in sorted({min(len(text), max(1, int(len(key) * factor))) for factor in factors}):
        have = Counter(text[:length])
        overlap = sum(min(count, need[char]) for char, count in have.items())
        for start in range(len(text) - length + 1):
            if start:
                gone, come = text[start - 1], text[start + length - 1]
                if gone != come:
                    if have[gone] <= need[gone]:
                        overlap -= 1
                    have[gone] -= 1
                    have[come] += 1
                    if have[come] <= need[come]:
                        overlap += 1
            candidates.append((2 * overlap / (length + len(key)), start, length))
    candidates.sort(reverse=True)
    matcher = SequenceMatcher(autojunk=False)
    matcher.set_seq2(key)
    scored, best = [], 0.0
    for bound, start, length in candidates:
        if bound < max(best, floor) - MIN_MARGIN:
            break
        matcher.set_seq1(text[start : start + length])
        ratio = matcher.ratio()
        scored.append((ratio, start, length))
        best = max(best, ratio)
    if not scored:
        return None
    ratio, start, length = max(scored)
    rival = max((r for r, s, n in scored if s + n <= start or s >= start + length), default=0.0)
    return ratio, start, length, rival


def _unique_token_window(text, quote, key):
    """``(start, length)`` of the stretch most like ``key`` that holds every quote token occurring
    exactly once in ``text``; ``None`` without such a token or when those tokens lie far apart."""
    spots = []
    for token in {compact(part) for part in quote.split()}:
        if len(token) >= MIN_ANCHOR_TOKEN and text.count(token) == 1:
            position = text.find(token)
            spots.append((position, position + len(token)))
    if not spots:
        return None
    low, high = min(a for a, _ in spots), max(b for _, b in spots)
    best = None
    for length in sorted({min(len(text), max(1, int(len(key) * factor))) for factor in (0.8, 1.0, 1.25)}):
        for start in range(max(0, high - length), min(low, len(text) - length) + 1):
            ratio = SequenceMatcher(None, text[start : start + length], key, autojunk=False).ratio()
            if best is None or ratio > best[0]:
                best = (ratio, start, length)
    return (best[1], best[2]) if best and best[0] >= MIN_QUOTE_RATIO else None


@lru_cache(maxsize=512)
def _quote_window(text, quote):
    """``(start, length)`` of the OCR stretch a quote refers to. Cached: the fields of one table
    row share a quote, and a document's fields are located one after another."""
    key = compact(quote)
    anchor = _best_window(text, key, (0.8, 1.0, 1.25), MIN_QUOTE_RATIO)
    if anchor and anchor[0] >= MIN_QUOTE_RATIO and anchor[0] - anchor[3] >= MIN_MARGIN:
        return anchor[1], anchor[2]
    # Rows of one table resemble each other; a token printed once on the page tells them apart.
    return _unique_token_window(text, quote, key)


def _approximate_box(layout, page, quote, raw):
    """Box of ``raw`` for a quote that is not the OCR's own text; ``None`` unless clearly unique."""
    blocks = next((item["blocks"] for item in layout if item["page"] == page), [])
    quote_key, raw_key = compact(quote), compact(str(raw)) if raw else ""
    joined, spans = "", []
    for block in blocks:
        for word in block["words"]:
            start = len(joined)
            joined += compact(word["text"])
            spans.append((start, len(joined), word["bbox"]))

    def box(low, high):
        return union_box([bbox for a, b, bbox in spans if a < high and b > low])

    found = _quote_window(joined, quote)
    if not found:
        return None
    start, length = found
    if not raw_key or quote_key.count(raw_key) != 1:
        # Same rule as the exact path: an ambiguous value marks its whole quote.
        return box(start, start + length)
    window = joined[start : start + length]
    raw_start = quote_key.find(raw_key)
    raw_end = raw_start + len(raw_key)
    opcodes = SequenceMatcher(None, window, quote_key, autojunk=False).get_opcodes()

    def to_window(position):
        for _, i1, i2, j1, j2 in opcodes:
            if j1 <= position <= j2 and j2 > j1:
                return i1 + round((position - j1) * (i2 - i1) / (j2 - j1))
        return len(window)

    matched = sum(
        max(0, min(j2, raw_end) - max(j1, raw_start)) for tag, _, _, j1, j2 in opcodes if tag == "equal"
    )
    if matched / len(raw_key) >= MIN_RAW_MATCHED:
        return box(start + to_window(raw_start), start + to_window(raw_end))
    # Table columns interleave in OCR reading order, so the value can sit just after the
    # stretch that matched its label. Look for the value itself there.
    region = joined[start : start + int(length * 2.5) + len(raw_key)]
    near = _best_window(region, raw_key, (1.0,), MIN_RAW_RATIO)
    if near and near[0] >= MIN_RAW_RATIO and near[0] - near[3] >= MIN_MARGIN:
        return box(start + near[1], start + near[1] + near[2])
    return None
