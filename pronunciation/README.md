# slabika-pronunciation

Optional native pronunciation models for Slabika. The package predicts pronunciations for previously unseen English, German and French words and returns the model's spelling-to-phone spans.

```python
from slabika_pronunciation import pronounce

result = pronounce("Bradshaw", "english")
assert result.phones == "bɹædʃɒː"
```

This package is intentionally separate from the pure-Python `slabika` wheel because the compressed model archives total about 41 MB and carry CC BY 4.0 attribution duties. Commercial use, modification and redistribution are permitted under the included licences. Preserve `MODEL_ATTRIBUTION.md`, `THIRD_PARTY_NOTICES.md`, and the applicable texts in `LICENSES/` when redistributing the package.

## Safety status

Pronunciation generation is operational, including unseen words. As of 2026-09-12, `slabika` uses the optional English model automatically for eligible English words, through its shared experimental `english_projection` layer; missing runtime, model errors or incomplete alignment fall back to the existing division path. German and French automatic division instead uses native-pattern PSP adapters, not these G2P models; generated DE/FR IPA remains a review aid. The earlier 255-form pronunciation-projection benchmark (EN 93.9%, DE 82.2%, FR 61.9% breakpoint precision) describes the older experiment, not the current adapters' accuracy. PSP remains the authority; model outputs and human proposals require independent verification.

## Build and test

Build a platform wheel from this directory with `python -m maturin build --release`. Run tests against an installed wheel with `python -m pytest`. `Cargo.lock` pins the native dependency graph; model hashes are checked at runtime and in tests.
