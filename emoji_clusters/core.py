"""Structural segmentation of text into emoji-aware clusters.

This does not consult a table of which code points are "emoji" - there is
no such table in the standard library, and shipping one means tracking a
new Unicode Emoji version every year. Instead it segments text using the
small set of fixed code points that give emoji sequences their structure:
the zero-width joiner, variation selectors, regional indicators, skin tone
modifiers, the keycap combining mark, and the tag characters used for
subdivision flags. Every one of those is a stable, already-assigned code
point, so this needs no maintenance as new emoji are added to Unicode.

The trade-off: a plain letter and a plain emoji with no modifiers both come
back as Kind.CODE_POINT, because structurally they look the same. Callers
who need "is this actually an emoji" still need a property table; callers
who need "don't split this flag/family/keycap in half" do not.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Optional, Tuple

ZWJ = "‍"
VS_TEXT = "︎"
VS_EMOJI = "️"
KEYCAP_COMBINING = "⃣"
KEYCAP_BASES = frozenset("0123456789#*")

REGIONAL_INDICATOR_START = 0x1F1E6
REGIONAL_INDICATOR_END = 0x1F1FF

SKIN_TONE_MODIFIER_START = 0x1F3FB
SKIN_TONE_MODIFIER_END = 0x1F3FF

TAG_START = 0xE0020
TAG_END = 0xE007E
TAG_CANCEL = 0xE007F


class Kind(Enum):
    """What kind of structure produced a cluster."""

    CODE_POINT = "code_point"
    PRESENTATION_TEXT = "presentation_text"
    PRESENTATION_EMOJI = "presentation_emoji"
    MODIFIER = "modifier"
    KEYCAP = "keycap"
    FLAG = "flag"
    TAG = "tag"
    ZWJ_SEQUENCE = "zwj_sequence"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class Cluster:
    """A run of text that should be kept together, and why."""

    text: str
    kind: Kind

    @property
    def codepoints(self) -> Tuple[str, ...]:
        return tuple(f"U+{ord(ch):04X}" for ch in self.text)


def _is_regional_indicator(cp: int) -> bool:
    return REGIONAL_INDICATOR_START <= cp <= REGIONAL_INDICATOR_END


def _is_skin_tone_modifier(cp: int) -> bool:
    return SKIN_TONE_MODIFIER_START <= cp <= SKIN_TONE_MODIFIER_END


def _is_tag_char(cp: int) -> bool:
    return TAG_START <= cp <= TAG_END


def _scan_core_element(text: str, i: int) -> Tuple[int, bool, Optional[str]]:
    """Consume one base code point plus an optional variation selector or
    skin tone modifier, starting at i. Returns (end, had_modifier, vs)."""
    n = len(text)
    j = i + 1
    had_modifier = False
    vs: Optional[str] = None
    if j < n:
        ch = text[j]
        cp = ord(ch)
        if ch in (VS_TEXT, VS_EMOJI):
            vs = ch
            j += 1
        elif _is_skin_tone_modifier(cp):
            had_modifier = True
            j += 1
    return j, had_modifier, vs


def iter_clusters(text: str) -> Iterator[Cluster]:
    """Walk text left to right, yielding one Cluster per emoji sequence or
    ordinary code point. Sequences never split across clusters."""
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        cp = ord(ch)

        if _is_regional_indicator(cp) and i + 1 < n and _is_regional_indicator(ord(text[i + 1])):
            yield Cluster(text[i:i + 2], Kind.FLAG)
            i += 2
            continue

        if i + 1 < n and _is_tag_char(ord(text[i + 1])):
            j = i + 1
            while j < n and _is_tag_char(ord(text[j])):
                j += 1
            if j < n and ord(text[j]) == TAG_CANCEL:
                j += 1
                yield Cluster(text[i:j], Kind.TAG)
                i = j
                continue

        if ch in KEYCAP_BASES:
            j = i + 1
            if j < n and text[j] == VS_EMOJI:
                j += 1
            if j < n and text[j] == KEYCAP_COMBINING:
                j += 1
                yield Cluster(text[i:j], Kind.KEYCAP)
                i = j
                continue

        if (
            ch == ZWJ
            or ch in (VS_TEXT, VS_EMOJI)
            or _is_skin_tone_modifier(cp)
            or _is_tag_char(cp)
            or cp == TAG_CANCEL
        ):
            # A marker code point with nothing valid in front of it to
            # attach to - not part of a well-formed sequence.
            yield Cluster(ch, Kind.MALFORMED)
            i += 1
            continue

        j, had_modifier, vs = _scan_core_element(text, i)
        joined = False
        while j < n and text[j] == ZWJ and j + 1 < n:
            joined = True
            j += 1  # consume the ZWJ
            j, _, _ = _scan_core_element(text, j)

        if joined:
            kind = Kind.ZWJ_SEQUENCE
        elif had_modifier:
            kind = Kind.MODIFIER
        elif vs == VS_EMOJI:
            kind = Kind.PRESENTATION_EMOJI
        elif vs == VS_TEXT:
            kind = Kind.PRESENTATION_TEXT
        else:
            kind = Kind.CODE_POINT

        yield Cluster(text[i:j], kind)
        i = j


def split(text: str) -> List[Cluster]:
    """Convenience wrapper around iter_clusters that returns a list."""
    return list(iter_clusters(text))


def truncate(text: str, max_clusters: int) -> str:
    """Truncate text to at most max_clusters clusters, without cutting a
    flag, keycap, ZWJ sequence, or other multi-code-point cluster in half.

    Raises ValueError if max_clusters is negative.
    """
    if max_clusters < 0:
        raise ValueError(f"max_clusters must be >= 0, got {max_clusters}")
    if max_clusters == 0:
        return ""
    parts = []
    count = 0
    for cluster in iter_clusters(text):
        if count >= max_clusters:
            break
        parts.append(cluster.text)
        count += 1
    return "".join(parts)


def classify(text: str) -> Kind:
    """Classify a string that is expected to already be a single cluster.

    Raises ValueError if text is empty or contains more than one cluster,
    since in that case there is no single answer to give.
    """
    clusters = split(text)
    if len(clusters) != 1:
        raise ValueError(
            f"expected exactly one cluster, got {len(clusters)} for {text!r}"
        )
    return clusters[0].kind
