from pathlib import Path

from scripts.generate_fixture import pi_digits

ROOT = Path(__file__).resolve().parents[2]


def test_independent_fixture_is_reproducible():
    expected = (ROOT / "data/fixtures/pi-first-1000.digits").read_text().strip()
    assert pi_digits(1000) == expected
    assert expected.startswith("14159265358979323846264338327950288419716939937510")
