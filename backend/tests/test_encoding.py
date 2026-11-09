import pytest

from app.encoding import EncodingError, LATIN, UTF8, encode


def test_latin_fixed_width_and_explicit_removal():
    assert encode("ADA")["encoded_pattern"] == "010401"
    result = encode("Pi, Ada!")
    assert result["normalized_text"] == "PIADA"
    assert result["encoded_pattern"] == "1609010401"
    assert result["removed_units"] == [",", " ", "!"]


def test_unicode_bytes_and_nfc():
    assert encode("PI", UTF8)["encoded_pattern"] == "080073"
    assert encode("e\u0301", UTF8)["encoded_pattern"] == encode("é", UTF8)["encoded_pattern"]
    assert encode("π🙂", UTF8)["pattern_length"] == len("π🙂".encode()) * 3


def test_unsupported_or_empty_text():
    with pytest.raises(EncodingError):
        encode("π", LATIN)
    with pytest.raises(EncodingError):
        encode("...", LATIN)
    with pytest.raises(EncodingError):
        encode("A\x00B", UTF8)
    with pytest.raises(EncodingError):
        encode("A\nB", UTF8)


def test_leading_zero_preserved():
    assert encode("A")["encoded_pattern"] == "01"
