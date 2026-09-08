# emoji-clusters

Split text into the units a person actually perceives as "one emoji",
without splitting a flag, a family, or a skin-toned thumbs-up in half.

## The problem

Python strings are sequences of code points, and most emoji people type as
"one character" are actually several:

```python
>>> len("👨‍👩‍👧‍👦")   # family emoji: four people joined by ZWJ
7
>>> "👨‍👩‍👧‍👦"[:1]   # slicing by code point breaks it
'👨'
>>> "🇺🇸"[0]           # US flag is two regional indicator symbols
'🇺'
```

Truncating a string, counting "characters" for a UI limit, or splitting on
character boundaries all silently corrupt sequences like these if you work
code point by code point. `emoji_clusters` walks a string and groups these
sequences back together so you can iterate, slice, or count at the level
users actually see.

## What it does not do

It does not tell you whether a given code point *is* an emoji - that
requires Unicode's emoji-data table, which changes every year, and pulling
that in would mean either a dependency or a data file to keep updated.
Instead it recognizes the fixed set of code points that give emoji
*sequences* their structure - the zero-width joiner, variation selectors,
regional indicators, skin tone modifiers, the keycap combining mark, and
tag characters - and keeps whatever they're attached to together as one
cluster. A plain letter and a bare emoji with no modifiers both come back
as `Kind.CODE_POINT`, because structurally they're the same thing: one
code point, nothing attached.

## Usage

```python
from emoji_clusters import split, classify, Kind

for cluster in split("Hi 👍🏽! 🇺🇸🇬🇧"):
    print(cluster.text, cluster.kind)

# H  Kind.CODE_POINT
# i  Kind.CODE_POINT
#    Kind.CODE_POINT
# 👍🏽 Kind.MODIFIER
# !  Kind.CODE_POINT
#    Kind.CODE_POINT
# 🇺🇸 Kind.FLAG
# 🇬🇧 Kind.FLAG

classify("🇺🇸")   # Kind.FLAG
classify("👨‍👩‍👧‍👦")  # Kind.ZWJ_SEQUENCE

truncate("👨‍👩‍👧‍👦!", 1)   # "👨‍👩‍👧‍👦" - not "👨"
truncate("🇺🇸🇬🇧", 1)      # "🇺🇸" - not the "🇺" half of a flag
```

`truncate(text, max_clusters)` keeps at most `max_clusters` clusters,
cutting between clusters rather than in the middle of one.

`split` never separates the code points of a single sequence across two
clusters, and joining `cluster.text` for every cluster back together
always reproduces the original string exactly.

```python
from emoji_clusters import count_clusters, cluster_boundaries, cluster_index_at

count_clusters("👨‍👩‍👧‍👦🇺🇸")   # 2 - not len(), which counts code points

cluster_boundaries("🇺🇸🇬🇧")   # [0, 2, 4] - code point offsets between clusters

cluster_index_at("Hi 🇺🇸", 4)   # 3 - which cluster owns code point index 4
```

`count_clusters` is the cheap check when you only need a length, since it
skips building the `Cluster` objects `split` allocates. `cluster_boundaries`
gives slice-ready offsets for every cluster in one pass. `cluster_index_at`
answers "which cluster is this code point index inside of", for when an
index comes from somewhere else (a regex match, a cursor position) and
needs mapping back onto cluster boundaries.

### Kinds

| Kind | Example | Structure |
|---|---|---|
| `CODE_POINT` | `a`, `😀` | one code point, nothing attached |
| `PRESENTATION_TEXT` | `☺︎` | code point + U+FE0E |
| `PRESENTATION_EMOJI` | `☺️` | code point + U+FE0F |
| `MODIFIER` | `👍🏽` | code point + skin tone modifier |
| `KEYCAP` | `3️⃣` | digit/`#`/`*` + optional U+FE0F + U+20E3 |
| `FLAG` | `🇺🇸` | two regional indicator symbols |
| `TAG` | England flag | tag base + tag letters + cancel tag |
| `ZWJ_SEQUENCE` | `👨‍👩‍👧‍👦` | two or more elements joined by U+200D |
| `MALFORMED` | a lone `U+200D` | a joiner/selector/modifier with nothing valid to attach to |

## Installing

No PyPI release yet. Clone the repo and use it as a local package, or copy
`emoji_clusters/` into your project - it has no dependencies.

## Running the tests

```
python -m unittest discover -s tests
```

## License

MIT, see [LICENSE](LICENSE).
