# Third-party notices

This file accompanies the `slabika-pronunciation` binary distribution. It adds no conditions; the corresponding licence texts govern.

## MFA G2P models

The bundled English, German and French model archives are maintained by Montreal Forced Aligner and licensed under CC BY 4.0. Required attribution, versions, source locations, hashes and modification status are recorded in `MODEL_ATTRIBUTION.md`. Full terms: `LICENSES/CC-BY-4.0.txt`.

## Rust WFST implementation

The native decoder uses `rustfst` 1.3.1 by Alexandre Caulier and contributors, declared `MIT OR Apache-2.0`. Full terms: `LICENSES/MIT.txt` and `LICENSES/Apache-2.0.txt`.

The multigraph-aware input lattice and Python binding are original Slabika code. Their structure was informed by the public API of `phonetisaurus-g2p` 0.1.1, Copyright 2025 lastleon, licensed under MIT. The package does not contain or link the original C++ Phonetisaurus implementation. The original MIT notice is retained in `LICENSES/phonetisaurus-g2p-MIT.txt`.

The compiled extension also includes transitive Rust crates pinned in `Cargo.lock`. Their package names, versions, declared SPDX expressions, copyright notices and licence texts are included in `THIRD_PARTY_LICENSES.html`, generated from the locked graph for each release. No GPL, AGPL, LGPL, non-commercial or source-available-only dependency is used.
