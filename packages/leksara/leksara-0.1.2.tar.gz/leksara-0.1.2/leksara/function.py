"""Convenience accessors for text-processing functions.

End users should import helper utilities from this module, e.g.::

    from leksara.function import remove_tags, replace_phone

The public surface mirrors the implementations inside ``leksara.functions``
packages without polluting the top-level namespace.
"""

from .functions.cleaner.basic import (
    remove_tags,
    case_normal,
    remove_stopwords,
    remove_whitespace,
    remove_punctuation,
    remove_digits,
    remove_emoji,
    replace_url,
)
from .functions.patterns.pii import (
    replace_phone,
    replace_address,
    replace_email,
    replace_id,
)
from .functions.review.advanced import (
    replace_rating,
    shorten_elongation,
    replace_acronym,
    normalize_slangs,
    expand_contraction,
    word_normalization,
)

__all__ = [
    "remove_tags",
    "case_normal",
    "remove_stopwords",
    "remove_whitespace",
    "remove_punctuation",
    "remove_digits",
    "remove_emoji",
    "replace_url",
    "replace_phone",
    "replace_address",
    "replace_email",
    "replace_id",
    "replace_rating",
    "shorten_elongation",
    "replace_acronym",
    "normalize_slangs",
    "expand_contraction",
    "word_normalization",
]
