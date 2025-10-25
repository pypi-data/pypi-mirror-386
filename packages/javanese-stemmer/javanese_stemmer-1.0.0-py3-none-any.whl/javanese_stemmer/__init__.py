"""
Javanese Stemmer Library
========================

A comprehensive Javanese language stemmer with morphophonological rules.

Basic Usage:
    >>> from javanese_stemmer import JavaneseStemmer
    >>> stemmer = JavaneseStemmer()
    >>> stemmer.stem('mangan')
    'pangan'

Quick Usage:
    >>> from javanese_stemmer import stem_word
    >>> stem_word('mangan')
    'pangan'
"""

from .stemmer import (
    JavaneseStemmer,
    JavaneseStemmerLibrary,
    create_stemmer,
    StemmerFactory,
    stem_word,
    stem_sentence,
    stem_text,
)

__version__ = "1.0.0"
__author__ = "Stevia Anlena Putri"  # ⚠️ CHANGE THIS TO YOUR NAME
__all__ = [
    'JavaneseStemmer',
    'JavaneseStemmerLibrary',
    'create_stemmer',
    'StemmerFactory',
    'stem_word',
    'stem_sentence',
    'stem_text',
]
