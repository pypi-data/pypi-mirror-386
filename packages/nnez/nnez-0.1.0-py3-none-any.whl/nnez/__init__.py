"""
nnez - Neural Network Easy Extraction

Simple and efficient extraction of activation patterns from transformer language models.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main functions for easy access
from .core import (
    get_activity_from_text,
    get_model_cached,
)

# Import grammar utilities
from .grammar import (
    get_article,
    get_article_with_noun,
    pluralize,
    singularize,
    quantify,
    a_or_an,
    with_article,
    an,
)

# Define what's available when using "from nnez import *"
__all__ = [
    # Core functionality
    "get_activity_from_text",
    "get_model_cached",

    # Grammar utilities
    "get_article",
    "get_article_with_noun",
    "pluralize",
    "singularize",
    "quantify",
    "a_or_an",
    "with_article",
    "an",

    # Version info
    "__version__",
]