"""Versioned, authoritative text-to-decimal encodings."""
import unicodedata
from dataclasses import dataclass

LATIN = "latin-a1z26-v1"
UTF8 = "utf8-decimal-v1"
PROFILES = {
    LATIN: {"id": LATIN, "version": 1, "name": "Latin A1Z26", "description": "A=01 through Z=26; spaces and common punctuation can be removed explicitly."},
    UTF8: {"id": UTF8, "version": 1, "name": "Unicode UTF-8 bytes", "description": "Every UTF-8 byte becomes a three-digit decimal token, 000–255."},
}
REMOVABLE = set(" \t\n\r.,'!?-")


class EncodingError(ValueError):
    pass


def encode(raw_text: str, profile_id: str = LATIN, letters_only: bool = True) -> dict:
    if not raw_text or len(raw_text) > 128:
        raise EncodingError("Enter 1–128 characters.")
    if profile_id not in PROFILES:
        raise EncodingError("Unknown encoding profile.")
    if any(unicodedata.category(char) == "Cc" and (profile_id != LATIN or char not in "\t\n\r") for char in raw_text):
        raise EncodingError("Control characters are not supported.")
    try:
        normalized = unicodedata.normalize("NFC", raw_text)
        normalized.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise EncodingError("Invalid Unicode input.") from exc
    removed = []
    units = []
    if profile_id == LATIN:
        kept = []
        for char in normalized:
            if char in REMOVABLE and letters_only:
                removed.append(char)
                continue
            upper = char.upper() if "a" <= char <= "z" else char
            if not "A" <= upper <= "Z":
                raise EncodingError(f"{char!r} is not in A–Z. Choose Unicode UTF-8 bytes for this text.")
            token = f"{ord(upper) - 64:02d}"
            units.append({"unit": char, "normalized_unit": upper, "token": token})
            kept.append(upper)
        normalized = "".join(kept)
    else:
        for byte in normalized.encode("utf-8"):
            units.append({"unit": f"0x{byte:02X}", "normalized_unit": str(byte), "token": f"{byte:03d}"})
    pattern = "".join(item["token"] for item in units)
    if not pattern:
        raise EncodingError("The text has no encodable characters.")
    if len(pattern) > 384:
        raise EncodingError("The encoded pattern exceeds the 384-digit limit.")
    return {
        "raw_text": raw_text, "normalized_text": normalized,
        "profile_id": profile_id, "profile_version": 1,
        "letters_only": letters_only if profile_id == LATIN else None,
        "removed_units": removed, "units": units,
        "encoded_pattern": pattern, "pattern_length": len(pattern),
    }
