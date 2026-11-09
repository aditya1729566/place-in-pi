# Corpus manifest v1

`data/corpus/manifest.json` is selected only after all new shards are written. The API re-hashes every shard before serving requests. Example shape (values are illustrative):

```json
{
  "constant": "pi",
  "version": "pi-1000000-<parsed-sha256-prefix>",
  "position_basis": "1-indexed after decimal",
  "digits": 1000000,
  "sha256": "<hash of concatenated ASCII decimal digits>",
  "shards": [{"file": "<immutable-name>.digits", "start": 1, "digits": 1000000, "sha256": "<shard hash>"}],
  "source": "<source URL or absolute local path>",
  "source_sha256": "<hash of original bytes>",
  "source_bytes": 1000002,
  "source_digits": 1000000,
  "prefix_taken": false,
  "retrieved_utc": "<UTC timestamp>",
  "verification": {"known_prefix_50": true, "independent_prefix_1000": true, "published_checkpoints": [9951, 11951, 49951], "source_sha256_checked": false}
}
```

Shard starts are contiguous and one-based; each file contains ASCII `0`–`9` only. The aggregate SHA-256 is over their concatenation. A new import changes the version, invalidating old cursors and indices. `--take-prefix` records the full validated source length separately from the selected searchable prefix. Source hashes measured at import time are never represented as externally published hashes.
