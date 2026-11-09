import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "engine/build/pi_search"


def commands(shards, lines):
    result = subprocess.run([str(ENGINE), *map(str, shards)], input="\n".join(lines) + "\n", text=True, capture_output=True, check=True)
    return result.stdout.rstrip("\n").splitlines()


def test_overlaps_and_shard_boundary(tmp_path):
    left, right = tmp_path / "a", tmp_path / "b"
    left.write_text("111")
    right.write_text("11")
    rows = commands([left, right], ["SCAN\t111\t0\t20\t5000", "DIGITS\t2\t4"])
    assert rows[0].split("\t")[1:4] == ["1", "3", "1"]
    assert rows[0].endswith("1,2,3")
    assert rows[1] == "DIGITS\t1111"


def test_cross_shard_pattern_and_leading_zero(tmp_path):
    left, right = tmp_path / "a", tmp_path / "b"
    left.write_text("141")
    right.write_text("59201")
    rows = commands([left, right], ["SCAN\t4159\t0\t5\t5000", "SCAN\t01\t0\t5\t5000"])
    assert rows[0].endswith("2")
    assert rows[1].endswith("7")


def test_randomized_against_python_oracle(tmp_path):
    rng = random.Random(417)
    digits = "1" + "".join(str(rng.randrange(10)) for _ in range(2500))
    shards = []
    for index in range(0, len(digits), 317):
        path = tmp_path / str(index)
        path.write_text(digits[index:index + 317])
        shards.append(path)
    patterns = [digits[i:i + length] for i, length in [(315, 5), (631, 8), (999, 3), (1400, 12)]] + ["00000", "123456"]
    rows = commands(shards, [f"SCAN\t{pattern}\t0\t100\t5000" for pattern in patterns])
    for pattern, row in zip(patterns, rows):
        expected = [i + 1 for i in range(len(digits) - len(pattern) + 1) if digits.startswith(pattern, i)]
        fields = row.split("\t")
        assert fields[1] == "1"
        assert int(fields[2]) == len(expected)
        assert int(fields[3]) == (expected[0] if expected else 0)
        assert [int(value) for value in fields[5].split(",") if value] == expected[:100]
