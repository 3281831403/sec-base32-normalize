"""五条边界测试：标准码、写法等价、非法输入、校验位敏感度、批量独立性。"""

import pytest

from codec.base32 import check_digit, code_batch, normalize

STANDARD = "AB12CD34"
STANDARD_LONG = "AB12CD34EF56GH78"


def test_standard_code_is_unchanged_by_normalize():
    assert normalize(STANDARD) == STANDARD
    assert normalize(STANDARD_LONG) == STANDARD_LONG
    assert normalize("01234567") == "01234567"
    assert normalize("0123-4567") == "01234567"


def test_lowercase_hyphenated_form_matches_standard():
    assert normalize("ab12-cd34") == normalize(STANDARD) == STANDARD
    assert normalize("Ab12 Cd34") == STANDARD
    assert normalize("ab12cd34") == STANDARD


def test_illegal_character_is_rejected_with_value_error():
    with pytest.raises(ValueError) as excinfo:
        normalize("AB12CD3!")
    assert "illegal_char" in str(excinfo.value)
    with pytest.raises(ValueError):
        normalize(STANDARD_LONG[:-1] + "!")


def test_check_digit_changes_for_every_single_character_edit():
    base = check_digit(STANDARD)
    variants = ["BB12CD34", "AB22CD34", "AB12DD34", "AB12CD44", "AB12CD35"]
    digits = [check_digit(variant) for variant in variants]
    assert all(digit != base for digit in digits)
    assert len(set(digits)) == len(digits)


def test_two_batches_match_individual_normalization():
    codes = ["ab12-cd34", "EF56-GH78", "0123-4567"]
    first = code_batch(codes, {})
    second = code_batch(codes, {})
    assert first == second
    assert first == {code: normalize(code) for code in codes}
    assert first["0123-4567"] == "01234567"