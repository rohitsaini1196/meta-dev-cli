import pytest
import typer

from meta_cli.utils import validate_phone_number


def test_valid_us_number():
    assert validate_phone_number("+14155552671") == "14155552671"


def test_valid_india_number():
    assert validate_phone_number("+919876543210") == "919876543210"


def test_strips_formatting():
    assert validate_phone_number("+1 (415) 555-2671") == "14155552671"


def test_invalid_number_raises():
    with pytest.raises(typer.BadParameter):
        validate_phone_number("not-a-number")


def test_too_short_raises():
    with pytest.raises(typer.BadParameter):
        validate_phone_number("+123")


def test_leading_zero_raises():
    with pytest.raises(typer.BadParameter):
        validate_phone_number("+0123456789")
