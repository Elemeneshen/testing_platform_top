import pytest
from .checker import check_answer, CheckerType


def test_check_exact():
    """Test exact matching."""
    assert check_answer("hello", "exact", "hello") == True
    assert check_answer("hello", "exact", "hello ") == False  # trailing space
    assert check_answer("hello", "exact", "Hello") == False  # case sensitive
    assert check_answer("", "exact", "") == True
    assert check_answer(" ", "exact", " ") == True


def test_check_regex():
    """Test regex matching."""
    # Exact match via regex
    assert check_answer("hello", "regex", "hello") == True
    assert check_answer("hello", "regex", "hell") == False

    # Pattern matching
    assert check_answer("hello123", "regex", r"hello\d+") == True
    assert check_answer("hello", "regex", r"hello\d+") == False

    # Special regex characters
    assert check_answer("hello.world", "regex", r"hello\.world") == True
    assert check_answer("helloworld", "regex", r"hello\.world") == False

    # Invalid regex should return False
    assert check_answer("test", "regex", "[") == False  # unclosed bracket
    assert check_answer("test", "regex", "*") == False  # nothing to repeat


def test_check_tokenized():
    """Test tokenized matching (whitespace-insensitive)."""
    assert check_answer("hello world", "tokenized", "hello world") == True
    assert check_answer("hello  world", "tokenized", "hello world") == True  # extra spaces
    assert check_answer("  hello   world  ", "tokenized", "hello world") == True  # leading/trailing
    assert check_answer("hello\tworld\n", "tokenized", "hello world") == True  # tabs/newlines

    # Different tokens
    assert check_answer("hello world", "tokenized", "world hello") == False
    assert check_answer("hello", "tokenized", "hello world") == False
    assert check_answer("hello world", "tokenized", "hello") == False

    # Empty strings
    assert check_answer("", "tokenized", "") == True
    assert check_answer("   ", "tokenized", "") == True  # only whitespace
    assert check_answer("", "tokenized", "   ") == True  # only whitespace


def test_invalid_checker_type():
    """Test that invalid checker type raises ValueError."""
    with pytest.raises(ValueError):
        check_answer("test", "invalid", "test")

    with pytest.raises(ValueError):
        check_answer("test", "", "test")