# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '1.0.0'
__author__ = 'Your Name'
__license__ = 'MIT'

from .translit import (
    latin_to_cyrillic,
    cyrillic_to_latin,
    transliterate,
    number_to_words,
    words_to_number,
    MongolianTransliterator
)

__all__ = [
    'latin_to_cyrillic',
    'cyrillic_to_latin',
    'transliterate',
    'number_to_words',
    'words_to_number',
    'MongolianTransliterator'
]
