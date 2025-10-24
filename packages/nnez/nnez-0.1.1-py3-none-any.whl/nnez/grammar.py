"""
Grammar utilities for determining correct articles/determiners for nouns using inflect.
"""

import inflect
from typing import Optional, Tuple
import re

# Initialize the inflect engine
p = inflect.engine()


def get_article(
    noun: str,
    definite: bool = False,
    quantity: Optional[str] = None,
    is_proper: bool = False,
    count: Optional[int] = None,
) -> str:
    """
    Get the correct article/determiner for a given noun using inflect.

    Args:
        noun: The noun to get an article for
        definite: If True, use "the" for definite reference
        quantity: Optional quantity hint ("singular", "plural", "mass", or None for auto-detect)
        is_proper: If True, treat as proper noun (usually no article)
        count: Optional count to determine singular/plural (1 = singular, >1 = plural)

    Returns:
        The appropriate article/determiner

    Examples:
        >>> get_article("apple")
        'an'
        >>> get_article("apples")
        'some'
        >>> get_article("dog")
        'a'
        >>> get_article("dogs")
        'some'
        >>> get_article("Paris", is_proper=True)
        ''
        >>> get_article("water")
        'some'
    """
    # Clean the noun
    noun = noun.strip()

    # Proper nouns typically don't take articles
    if is_proper or _is_likely_proper(noun):
        return ""

    # Handle definite articles
    if definite:
        return "the"

    # Determine if plural
    is_plural_noun = False

    if count is not None:
        is_plural_noun = count != 1
    elif quantity == "plural":
        is_plural_noun = True
    elif quantity == "singular":
        is_plural_noun = False
    else:
        # Auto-detect using inflect
        is_plural_noun = _is_plural(noun)

    # Check for mass/uncountable nouns
    if quantity == "mass" or _is_mass_noun(noun):
        return "some"

    # Handle plural nouns
    if is_plural_noun:
        return "some"

    # For singular nouns, use inflect to get the correct indefinite article
    return _get_indefinite_article(noun)


def _get_indefinite_article(word: str) -> str:
    """
    Determine whether to use 'a' or 'an' before a word using inflect.

    Inflect handles pronunciation-based rules automatically.
    """
    if not word:
        return "a"

    # Use inflect's a/an method
    result = p.a(word)

    # Extract just the article from "a word" or "an word"
    if result.startswith("an "):
        return "an"
    elif result.startswith("a "):
        return "a"

    # Fallback for edge cases
    return "a"


def _is_plural(noun: str) -> bool:
    """
    Check if a noun is plural using inflect's singular_noun method.

    Returns True if the noun is plural, False otherwise.
    """
    if not noun:
        return False

    # inflect.singular_noun() returns:
    # - False if the word is already singular
    # - The singular form if the word is plural
    # - Sometimes returns the word itself for ambiguous cases

    singular_form = p.singular_noun(noun)

    # If singular_noun returns False, the word is already singular
    if singular_form is False:
        return False

    # If it returns a different word, the original was plural
    if singular_form and singular_form.lower() != noun.lower():
        return True

    # For ambiguous cases (like "sheep", "deer"), check our special cases
    return _check_ambiguous_plural(noun)


def _check_ambiguous_plural(noun: str) -> bool:
    """
    Handle ambiguous cases where singular and plural forms are the same.

    This requires context, so we'll default to singular for these cases.
    """
    # Words that are the same in singular and plural
    invariant_nouns = {
        "sheep",
        "deer",
        "fish",
        "moose",
        "series",
        "species",
        "means",
        "offspring",
        "aircraft",
        "spacecraft",
        "hovercraft",
    }

    if noun.lower() in invariant_nouns:
        # Default to singular without context
        return False

    return False


def _is_mass_noun(noun: str) -> bool:
    """
    Check if a noun is a mass/uncountable noun.

    This still requires a curated list as inflect doesn't directly identify mass nouns.
    """
    noun = noun.lower().strip()

    # Common mass nouns
    mass_nouns = {
        # Liquids
        "water",
        "milk",
        "juice",
        "coffee",
        "tea",
        "wine",
        "beer",
        "oil",
        "gasoline",
        "blood",
        "soup",
        "honey",
        "syrup",
        # Food
        "bread",
        "butter",
        "cheese",
        "meat",
        "rice",
        "salt",
        "sugar",
        "flour",
        "food",
        "pasta",
        "cereal",
        "yogurt",
        # Materials
        "wood",
        "paper",
        "plastic",
        "glass",
        "metal",
        "gold",
        "silver",
        "cotton",
        "wool",
        "silk",
        "leather",
        "fabric",
        "cloth",
        # Abstract
        "information",
        "advice",
        "knowledge",
        "wisdom",
        "intelligence",
        "ignorance",
        "love",
        "hate",
        "anger",
        "happiness",
        "sadness",
        "joy",
        "fear",
        "courage",
        "music",
        "art",
        "poetry",
        "literature",
        "beauty",
        "ugliness",
        "time",
        "space",
        "energy",
        "power",
        "force",
        "strength",
        "money",
        "wealth",
        "poverty",
        "work",
        "homework",
        "research",
        "progress",
        "news",
        "mail",
        "email",
        "software",
        "hardware",
        "data",
        # Weather
        "weather",
        "rain",
        "snow",
        "wind",
        "sunshine",
        "fog",
        "thunder",
        "lightning",
        "humidity",
        "precipitation",
        # Other
        "furniture",
        "equipment",
        "luggage",
        "baggage",
        "garbage",
        "trash",
        "rubbish",
        "traffic",
        "transportation",
        "pollution",
        "smoke",
        "dust",
        "dirt",
        "mud",
        "hair",
        "air",
        "oxygen",
        "hydrogen",
        "electricity",
        "gravity",
        "pressure",
        "sand",
        "grass",
        "vegetation",
    }

    return noun in mass_nouns


def _is_likely_proper(noun: str) -> bool:
    """
    Heuristic to detect if a noun is likely a proper noun.
    """
    if not noun:
        return False

    # Acronyms are not proper nouns for article purposes
    if noun.isupper() and len(noun) <= 4:
        return False

    # Check if capitalized (proper nouns are usually capitalized)
    if noun[0].isupper():
        # Common titles and words that aren't proper nouns by themselves
        common_words = {
            "Mr",
            "Mrs",
            "Ms",
            "Dr",
            "Prof",
            "Professor",
            "President",
            "King",
            "Queen",
            "Lord",
            "Lady",
            "Captain",
            "General",
            "Colonel",
            "Major",
            "The",
            "This",
            "That",
            "These",
            "Those",
        }

        first_word = noun.split()[0]
        if first_word not in common_words:
            # Additional check: if it's a known common noun, don't treat as proper
            if not _is_common_noun(noun):
                return True

    return False


def _is_common_noun(word: str) -> bool:
    """
    Check if a capitalized word is actually a common noun (not a proper noun).
    """
    # List of common nouns that might appear capitalized
    common_capitalized = {
        "Internet",
        "Web",
        "Email",
        "Phone",
        "Computer",
        "University",
        "College",
        "School",
        "Hospital",
        "Street",
        "Road",
        "Avenue",
        "Park",
        "Building",
        "Company",
        "Corporation",
        "Department",
        "Committee",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    }

    return word in common_capitalized


def get_article_with_noun(
    noun: str,
    definite: bool = False,
    quantity: Optional[str] = None,
    is_proper: bool = False,
    count: Optional[int] = None,
) -> str:
    """
    Get the article and noun together as a phrase.

    Examples:
        >>> get_article_with_noun("apple")
        'an apple'
        >>> get_article_with_noun("dogs")
        'some dogs'
    """
    article = get_article(noun, definite, quantity, is_proper, count)
    if article:
        return f"{article} {noun}"
    return noun


def pluralize(word: str, count: Optional[int] = None) -> str:
    """
    Get the plural form of a word using inflect.

    Args:
        word: The word to pluralize
        count: Optional count (if provided, returns singular for 1, plural otherwise)

    Returns:
        The pluralized form
    """
    if count == 1:
        return word
    elif count is not None:
        return p.plural(word)
    else:
        return p.plural(word)


def singularize(word: str) -> str:
    """
    Get the singular form of a word using inflect.

    Args:
        word: The word to singularize

    Returns:
        The singular form
    """
    result = p.singular_noun(word)
    if result is False:
        # Already singular
        return word
    return result


def quantify(count: int, noun: str) -> str:
    """
    Combine a count with a noun, handling pluralization automatically.

    Args:
        count: The number
        noun: The noun

    Returns:
        The quantified phrase (e.g., "1 dog", "2 dogs", "no dogs")
    """
    # Use inflect's quantify method
    if count == 0:
        return f"no {p.plural(noun)}"
    else:
        # inflect can handle this elegantly
        return p.inflect(f"num({count}) {p.plural(noun, count)}")


# Convenience functions
def a_or_an(noun: str) -> str:
    """Get 'a' or 'an' for a noun."""
    return get_article(noun, definite=False)


def with_article(noun: str) -> str:
    """Get noun with its indefinite article."""
    return get_article_with_noun(noun, definite=False)


def an(word: str) -> str:
    """
    Return the word with appropriate article using inflect.

    Examples:
        >>> an("apple")
        'an apple'
        >>> an("dog")
        'a dog'
    """
    return p.a(word)


def test_articles():
    """Test the article detection with various examples."""
    test_cases = [
        # Basic cases
        ("apple", "an"),
        ("banana", "a"),
        ("elephant", "an"),
        ("dog", "a"),
        # Plurals
        ("apples", "some"),
        ("dogs", "some"),
        ("children", "some"),
        ("people", "some"),
        # Special pronunciation
        ("hour", "an"),
        ("honest", "an"),
        ("university", "a"),
        ("umbrella", "an"),
        ("european", "a"),
        ("one", "a"),
        ("eight", "an"),
        ("eleven", "an"),
        # Mass nouns
        ("water", "some"),
        ("information", "some"),
        ("furniture", "some"),
        ("advice", "some"),
        # Proper nouns
        ("Paris", ""),
        ("Microsoft", ""),
        # Edge cases
        ("FBI", "an"),  # Pronounced "eff-bee-eye"
        ("NASA", "a"),  # Pronounced "nah-sah"
        ("URL", "an"),  # Can be "a URL" or "an URL" depending on pronunciation
        ("SQL", "an"),  # Pronounced "ess-kyoo-ell" or "sequel"
    ]

    print("Testing article detection with inflect:")
    print("-" * 50)

    for noun, expected in test_cases:
        result = get_article(
            noun,
            is_proper=(noun[0].isupper() and noun in ["Paris", "Microsoft"]),
        )
        status = "✓" if result == expected else "✗"
        print(f"{status} '{noun}' -> '{result}' (expected '{expected}')")
        if result != expected:
            print(f"  Full phrase: '{get_article_with_noun(noun)}'")
        assert result == expected


def demo():
    """Demonstrate various features of the grammar module."""
    print("\n" + "=" * 50)
    print("Grammar Module Demo (using inflect)")
    print("=" * 50)

    # Articles
    print("\n1. Article Detection:")
    words = ["apple", "hour", "university", "FBI", "dog", "eight"]
    for word in words:
        print(f"  {word:12} -> {with_article(word)}")

    # Pluralization
    print("\n2. Pluralization:")
    words = ["cat", "mouse", "child", "person", "goose", "fish"]
    for word in words:
        plural = pluralize(word)
        print(f"  {word:12} -> {plural}")

    # Singularization
    print("\n3. Singularization:")
    words = ["cats", "mice", "children", "people", "geese", "fish"]
    for word in words:
        singular = singularize(word)
        print(f"  {word:12} -> {singular}")

    # Quantification
    print("\n4. Quantification:")
    nouns = ["apple", "child", "mouse", "sheep"]
    counts = [0, 1, 2, 5]
    for noun in nouns:
        for count in counts:
            phrase = quantify(count, noun)
            print(f"  {count} + {noun:8} -> {phrase}")
        print()

    # Using inflect's a() method directly
    print("\n5. Direct inflect usage:")
    phrases = [
        "hour ago",
        "FBI agent",
        "European country",
        "apple",
        "SQL database",
    ]
    for phrase in phrases:
        result = an(phrase)
        print(f"  {phrase:20} -> {result}")


if __name__ == "__main__":
    print("=" * 70)
    print("GRAMMAR ARTICLE DETECTOR (Powered by inflect)")
    print("=" * 70)
    print()

    # Run tests
    test_articles()

    # Run demo
    demo()

    print("\n" + "=" * 70)
    print("Interactive testing - try your own nouns!")
    print("Type 'quit' to exit")
    print("=" * 70)

    while True:
        noun = input("\nEnter a noun: ").strip()
        if noun.lower() in ["quit", "exit", "q"]:
            break

        article = get_article(noun)
        phrase = get_article_with_noun(noun)

        print(f"  Article: '{article}'")
        print(f"  Phrase: '{phrase}'")
        print(f"  Definite: '{get_article_with_noun(noun, definite=True)}'")
        print(f"  Plural: '{pluralize(noun)}'")
        print(f"  With inflect.a(): '{an(noun)}'")
