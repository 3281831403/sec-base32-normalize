"""十条契约测试，一条对一个缺陷，顺序与题面缺陷顺序一致。"""

import pytest

from codec.base32 import (
    add_padding,
    check_digit,
    code_batch,
    fold_case,
    map_lookalikes,
    normalize,
    strip_separators,
    validate_alphabet,
)

STANDARD = "AB12CD34"
STANDARD_LONG = "AB12CD34EF56GH78"


def test_defect_01_lowercase_is_folded_not_rejected():
    assert fold_case("ab12-cd34") == "AB12-CD34"
    assert fold_case("aB1Z") == "AB1Z"
    assert normalize("ab12cd34") == STANDARD


def test_defect_02_lookalikes_map_to_canonical_characters():
    assert map_lookalikes("OILU") == "011V"
    assert map_lookalikes("AB12CD34") == "AB12CD34"
    assert normalize("ABIZCD34") == "AB1ZCD34"
    assert normalize("ABOZCD34") == "AB0ZCD34"


def test_defect_03_hyphenated_groups_are_stripped():
    assert strip_separators("ab-12 cd\t34\n") == "ab12cd34"
    assert strip_separators("AB12--CD34") == "AB12CD34"
    assert normalize("AB12-CD34") == STANDARD
    assert normalize("AB12 CD34") == STANDARD


def test_defect_04_existing_padding_is_never_doubled():
    assert add_padding("AB12CD34") == "AB12CD34"
    assert add_padding("AB12CD3") == "AB12CD3="
    assert add_padding("AB12CD3=") == "AB12CD3="
    assert add_padding(add_padding("AB12CD")) == "AB12CD=="
    with pytest.raises(ValueError):
        add_padding("AB12CD34====")
    with pytest.raises(ValueError):
        add_padding("AB12=CD3")


def test_defect_05_illegal_characters_are_reported():
    assert validate_alphabet(STANDARD) == []
    assert any(p.startswith("illegal_char") for p in validate_alphabet("AB12CD3!"))
    assert any(p.startswith("illegal_char") for p in validate_alphabet("AB12CD3U"))
    assert any(p.startswith("illegal_char") for p in validate_alphabet("AB12CD3I"))


def test_defect_06_length_must_be_multiple_of_eight():
    assert validate_alphabet(STANDARD_LONG) == []
    for bad in ("AB12CD3456", "AB12CD345678", "AB12C", "AB12CD34567890123456"):
        problems = validate_alphabet(bad)
        assert any(p.startswith("bad_length") for p in problems), bad
    with pytest.raises(ValueError):
        normalize("AB12CD3456")


def test_defect_07_check_digit_uses_modulo_not_raw_sum():
    digit = check_digit(STANDARD)
    assert digit == "W"
    assert len(digit) == 1
    assert check_digit(STANDARD_LONG) == "R"


def test_defect_08_check_digit_is_always_uppercase():
    assert check_digit("ab12cd34") == "W"
    assert check_digit("ab12cd34") == check_digit(STANDARD)
    assert check_digit("ab12cd34").isupper()
    assert check_digit("AB12CD34") == "W"


def test_defect_09_normalize_is_idempotent():
    once = normalize("ab12-cd34")
    twice = normalize(once)
    assert once == STANDARD
    assert twice == once
    assert "=" not in twice
    assert normalize(normalize("AB12 CD34")) == STANDARD


def test_defect_10_batch_normalizes_every_code_independently():
    codes = ["ab12-cd34", "AB12CD34", "ef56-gh78"]
    assert code_batch(codes, {}) == {
        "ab12-cd34": "AB12CD34",
        "AB12CD34": "AB12CD34",
        "ef56-gh78": "EF56GH78",
    }
    assert code_batch(["ab12cd34", "EF56GH78"], {"keep_separators": True}) == {
        "ab12cd34": "AB12-CD34",
        "EF56GH78": "EF56-GH78",
    }
    assert code_batch(["AB12CD34"], {"with_check_digit": True}) == {
        "AB12CD34": "AB12CD34W"
    }
    assert code_batch(["AB12CD34", "bad!"], {"strict": False}) == {
        "AB12CD34": "AB12CD34"
    }