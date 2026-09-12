# Bundled G2P model attribution

The distribution contains three unmodified model archives from Montreal Forced Aligner. Each model is licensed under Creative Commons Attribution 4.0 International (`CC-BY-4.0`). The complete licence text is in `LICENSES/CC-BY-4.0.txt`.

| Language | Licensed material | Creator/maintainer | Version | Source | Bundled archive SHA-256 | Changes |
| --- | --- | --- | --- | --- | --- | --- |
| English | English (US) MFA G2P model | Montreal Forced Aligner; citation credits Michael McAuliffe and Morgan Sonderegger | 3.0.0, trained 2023-05-07 | https://github.com/MontrealCorpusTools/mfa-models/releases/tag/g2p-english_us_mfa-v3.0.0 | `9923b38d59a8b3e3e322f225c52523c2a6248e5ffc9fd89be151ade2dc97cb02` | None; upstream ZIP redistributed byte-for-byte |
| German | German MFA G2P model | Montreal Forced Aligner; citation credits Michael McAuliffe and Morgan Sonderegger | 3.0.0, trained 2024-03-07 | https://github.com/MontrealCorpusTools/mfa-models/releases/tag/g2p-german_mfa-v3.0.0 | `ab5340cb0ff19a5e383564b4adf5db301e8d8bf23218d6b0e4e37d38a8943f73` | None; upstream ZIP redistributed byte-for-byte |
| French | French MFA G2P model | Montreal Forced Aligner; citation credits Michael McAuliffe and Morgan Sonderegger | 3.0.0, trained 2024-03-06 | https://github.com/MontrealCorpusTools/mfa-models/releases/tag/g2p-french_mfa-v3.0.0 | `d4ebbb146ca123e887d2f0c17d09dff6c4f4a7d51a5be49c5564fb7f4a80d3c4` | None; upstream ZIP redistributed byte-for-byte |

The models are used only to generate pronunciation candidates. They are not represented as part of the Slabika project's MIT/Apache/CC0 material, and recipients retain all rights granted directly by CC BY 4.0. No endorsement by Montreal Forced Aligner or the cited authors is implied.

Model cards report that these models were trained from the corresponding MFA pronunciation dictionaries. The v3 model cards contain null evaluation values rendered as 100% WER/PER; this package does not present those values as measured model quality. Practical Slabika projection results are documented separately in the package README.
