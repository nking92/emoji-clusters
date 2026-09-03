import unittest

from emoji_clusters import Kind, split

# Regional indicators, spelled out as code points so it is obvious which
# letters make up which flag without relying on font rendering.
RI_U = "\U0001F1FA"
RI_S = "\U0001F1F8"
RI_G = "\U0001F1EC"
RI_B = "\U0001F1E7"

FLAG_US = RI_U + RI_S
FLAG_GB = RI_G + RI_B

THUMBS_UP = "\U0001F44D"
MEDIUM_SKIN_TONE = "\U0001F3FD"

SMILING_FACE = "☺"  # has both text and emoji presentation forms
VS_TEXT = "︎"
VS_EMOJI = "️"

KEYCAP = "⃣"

MAN = "\U0001F468"
WOMAN = "\U0001F469"
GIRL = "\U0001F467"
BOY = "\U0001F466"
HEART = "❤"
ZWJ = "‍"

# The England subdivision flag: black flag base, tag letters spelling
# "gbeng", cancel tag. This is the real sequence used in the wild, not a
# simplified stand-in.
BLACK_FLAG = "\U0001F3F4"
TAG_CANCEL = "\U000E007F"


def _tag_sequence(letters):
    tags = "".join(chr(0xE0000 + ord(c)) for c in letters)
    return BLACK_FLAG + tags + TAG_CANCEL


ENGLAND_FLAG = _tag_sequence("gbeng")

# name, input text, expected list of (cluster_text, kind)
CASES = [
    ("empty_string", "", []),
    (
        "plain_ascii",
        "abc",
        [("a", Kind.CODE_POINT), ("b", Kind.CODE_POINT), ("c", Kind.CODE_POINT)],
    ),
    ("emoji_with_no_modifiers", "\U0001F600", [("\U0001F600", Kind.CODE_POINT)]),
    ("digit_without_keycap_mark", "5", [("5", Kind.CODE_POINT)]),
    ("keycap_with_variation_selector", "#" + VS_EMOJI + KEYCAP, [("#" + VS_EMOJI + KEYCAP, Kind.KEYCAP)]),
    ("keycap_without_variation_selector", "3" + KEYCAP, [("3" + KEYCAP, Kind.KEYCAP)]),
    ("single_flag", FLAG_US, [(FLAG_US, Kind.FLAG)]),
    (
        "two_adjacent_flags",
        FLAG_US + FLAG_GB,
        [(FLAG_US, Kind.FLAG), (FLAG_GB, Kind.FLAG)],
    ),
    (
        "odd_trailing_regional_indicator",
        FLAG_US + RI_G,
        [(FLAG_US, Kind.FLAG), (RI_G, Kind.CODE_POINT)],
    ),
    (
        "skin_tone_modifier",
        THUMBS_UP + MEDIUM_SKIN_TONE,
        [(THUMBS_UP + MEDIUM_SKIN_TONE, Kind.MODIFIER)],
    ),
    (
        "emoji_presentation_selector",
        SMILING_FACE + VS_EMOJI,
        [(SMILING_FACE + VS_EMOJI, Kind.PRESENTATION_EMOJI)],
    ),
    (
        "text_presentation_selector",
        SMILING_FACE + VS_TEXT,
        [(SMILING_FACE + VS_TEXT, Kind.PRESENTATION_TEXT)],
    ),
    (
        "zwj_family_of_four",
        MAN + ZWJ + WOMAN + ZWJ + GIRL + ZWJ + BOY,
        [(MAN + ZWJ + WOMAN + ZWJ + GIRL + ZWJ + BOY, Kind.ZWJ_SEQUENCE)],
    ),
    (
        "zwj_sequence_with_embedded_presentation_selector",
        WOMAN + ZWJ + HEART + VS_EMOJI + ZWJ + MAN,
        [(WOMAN + ZWJ + HEART + VS_EMOJI + ZWJ + MAN, Kind.ZWJ_SEQUENCE)],
    ),
    ("tag_sequence_england_flag", ENGLAND_FLAG, [(ENGLAND_FLAG, Kind.TAG)]),
    ("malformed_lone_zwj", ZWJ, [(ZWJ, Kind.MALFORMED)]),
    ("malformed_lone_variation_selector", VS_EMOJI, [(VS_EMOJI, Kind.MALFORMED)]),
    ("malformed_lone_skin_tone_modifier", MEDIUM_SKIN_TONE, [(MEDIUM_SKIN_TONE, Kind.MALFORMED)]),
    (
        "malformed_lone_tag_letter",
        chr(0xE0067),
        [(chr(0xE0067), Kind.MALFORMED)],
    ),
    (
        "zwj_at_end_of_string_does_not_extend",
        "\U0001F600" + ZWJ,
        [("\U0001F600", Kind.CODE_POINT), (ZWJ, Kind.MALFORMED)],
    ),
    (
        "mixed_text_and_emoji",
        "Hi " + THUMBS_UP + MEDIUM_SKIN_TONE + "!",
        [
            ("H", Kind.CODE_POINT),
            ("i", Kind.CODE_POINT),
            (" ", Kind.CODE_POINT),
            (THUMBS_UP + MEDIUM_SKIN_TONE, Kind.MODIFIER),
            ("!", Kind.CODE_POINT),
        ],
    ),
]


class SplitTableTests(unittest.TestCase):
    def test_cases(self):
        for name, text, expected in CASES:
            with self.subTest(name=name):
                got = [(c.text, c.kind) for c in split(text)]
                self.assertEqual(got, expected)

    def test_clusters_reassemble_to_original_text(self):
        for name, text, _expected in CASES:
            with self.subTest(name=name):
                got = "".join(c.text for c in split(text))
                self.assertEqual(got, text)


class ClassifyTests(unittest.TestCase):
    def test_classify_single_cluster(self):
        from emoji_clusters import classify

        self.assertEqual(classify(FLAG_US), Kind.FLAG)
        self.assertEqual(classify(THUMBS_UP + MEDIUM_SKIN_TONE), Kind.MODIFIER)

    def test_classify_rejects_multiple_clusters(self):
        from emoji_clusters import classify

        with self.assertRaises(ValueError):
            classify(FLAG_US + FLAG_GB)

    def test_classify_rejects_empty_string(self):
        from emoji_clusters import classify

        with self.assertRaises(ValueError):
            classify("")


if __name__ == "__main__":
    unittest.main()
