# slabika-pronunciation

Optional native pronunciation models for Slabika. The package predicts pronunciations for previously unseen English, German and French words and returns the model's spelling-to-phone spans.

```python
from slabika_pronunciation import pronounce

result = pronounce("Bradshaw", "english")
assert result.phones == "bɹædʃɒː"
```

This package is intentionally separate from the pure-Python `slabika` wheel because the compressed model archives total about 41 MB and carry CC BY 4.0 attribution duties. Commercial use, modification and redistribution are permitted under the included licences. Preserve `MODEL_ATTRIBUTION.md`, `THIRD_PARTY_NOTICES.md`, and the applicable texts in `LICENSES/` when redistributing the package.

## Safety status

Pronunciation generation is operational, including unseen words. Automatic conversion of a pronunciation into Slovak PSP line-break positions remains conservative and is not enabled globally in `slabika` 0.1.0. A September 2026 benchmark against 255 unambiguously profile-routed reviewed forms found breakpoint precision of 93.9% for English, 82.2% for German and 61.9% for French with the best tested conservative projection. Those values are insufficient for silently changing production typography. The models are therefore shipped as an explicit pronunciation API and review aid; PSP and verified human decisions remain authoritative.

## Build and test

Build a platform wheel from this directory with `python -m maturin build --release`. Run tests against an installed wheel with `python -m pytest`. `Cargo.lock` pins the native dependency graph; model hashes are checked at runtime and in tests.
