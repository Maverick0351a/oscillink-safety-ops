# Runtime parser fuzz corpus

Each `*.hex` file is the lowercase hexadecimal representation of one minimized malformed byte
sequence. The harness decodes bytes before exercising both exact observation binding and bounded
JSONL replay parsing. These synthetic maintainer regressions are not field or certification evidence.

Run deterministically:

```bash
uv run python fuzz/runtime_observation_fuzz.py fuzz/corpus/runtime/*.hex
```

With optional Atheris installed, invoke the harness without seed arguments for mutation fuzzing.
Atheris is intentionally not part of the canonical verifier or runtime dependency set.
