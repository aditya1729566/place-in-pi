#!/usr/bin/env python3
"""Independently compute a small decimal π fixture with Chudnovsky binary splitting."""
from math import isqrt
from pathlib import Path

DIGITS = 1000
C3_OVER_24 = 640320 ** 3 // 24


def binary_split(a: int, b: int):
    if b - a == 1:
        if a == 0:
            p = q = 1
        else:
            p = (6 * a - 5) * (2 * a - 1) * (6 * a - 1)
            q = a ** 3 * C3_OVER_24
        t = p * (13591409 + 545140134 * a)
        if a & 1:
            t = -t
        return p, q, t
    m = (a + b) // 2
    p1, q1, t1 = binary_split(a, m)
    p2, q2, t2 = binary_split(m, b)
    return p1 * p2, q1 * q2, t1 * q2 + p1 * t2


def pi_digits(count: int) -> str:
    _, q, t = binary_split(0, count // 14 + 2)
    sqrt_scaled = isqrt(10005 * 10 ** (2 * (count + 5)))
    scaled_pi = q * 426880 * sqrt_scaled // t
    return str(scaled_pi)[1:count + 1]


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "data/fixtures/pi-first-1000.digits"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(pi_digits(DIGITS) + "\n")
    print(output)
