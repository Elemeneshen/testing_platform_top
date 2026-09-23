"""
Answer checking service for auto_check tasks.
Implements three types of checking: exact, regex, and tokenized.
"""

import re
from typing import Literal

CheckerType = Literal["exact", "regex", "tokenized"]


def check_answer(answer: str, checker_type: CheckerType, expected: str) -> bool:
    """
    Check if the answer matches the expected value based on checker type.

    Args:
        answer: The student's answer
        checker_type: Type of check to perform (exact, regex, tokenized)
        expected: The expected answer/value

    Returns:
        True if answer matches expected, False otherwise
    """
    if checker_type == "exact":
        return _check_exact(answer, expected)
    elif checker_type == "regex":
        return _check_regex(answer, expected)
    elif checker_type == "tokenized":
        return _check_tokenized(answer, expected)
    else:
        raise ValueError(f"Unknown checker type: {checker_type}")


def _check_exact(answer: str, expected: str) -> bool:
    """
    Exact match: answer must be identical to expected (case-sensitive).
    """
    return answer == expected


def _check_regex(answer: str, expected: str) -> bool:
    """
    Regex match: answer must match the expected regular expression pattern.
    """
    try:
        pattern = re.compile(expected)
        return bool(pattern.fullmatch(answer))
    except re.error:
        # If regex is invalid, treat as no match
        return False


def _check_tokenized(answer: str, expected: str) -> bool:
    """
    Tokenized match: compare token by token, ignoring whitespace differences.
    Splits both strings by whitespace and compares the resulting tokens.
    """
    answer_tokens = answer.split()
    expected_tokens = expected.split()
    return answer_tokens == expected_tokens