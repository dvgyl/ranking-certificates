# Certified Model Ranking under Limited Label Errors

Dev D. Goyal. Independent researcher.

This package contains the paper, its supplement, the active LaTeX sources, and a small computational check. The paper studies certificates for a fixed model ranking when a limited number of recorded test labels can be wrong. A certificate bounds the total weight of model comparisons that can reverse under the permitted label corrections.

The computational check uses 20 synthetic binary prediction tables. Each table has 200 examples, six models, and 12 flagged labels. It checks every correction subset and every integer budget from zero through 12. It uses equal weights for all 15 model pairs and limits of 1/10 and 1/5.

The saved verification report records 20 checked instances and no failures. The event tests agreed with exhaustive label correction on these inputs. The edge-relaxation values have exact primal and dual certificates. This is an exploratory implementation check. It does not establish practical benefit, performance on future data, or general correctness of the implementation.

## Files

| Location | Contents |
|---|---|
| `manuscript/main.pdf` | Named manuscript. |
| `manuscript/supplement.pdf` | Mathematical supplement. |
| `manuscript/active-sources.zip` | Active LaTeX sources. |
| `computational-check/certificate_check.py` | Instance generator, exact calculations, and saved-input verifier. |
| `computational-check/plan.json` | Fixed configuration and seed list. |
| `computational-check/data/` | Inputs, results, certificates, verification report, and environment record. |
| `REPRODUCING.md` | Verification and reproduction instructions. |
| `CITATION.cff` | Citation metadata for the software. |
| `.zenodo.json` | Metadata for a Zenodo archive of the package. |
| `SHA256SUMS` | SHA-256 checksums for the release files. |

Start with the paper. Use `REPRODUCING.md` to check the saved computational evidence. Build instructions are in `REPRODUCING.md`.

The computational code is under the MIT License. The author-owned manuscript, sources, data, results, certificates, and documentation are under Creative Commons Attribution 4.0 International. Third-party files retain their own terms. See `LICENSE.md` for the exact scope and full license texts.

Use `CITATION.cff` to cite the software. The citation metadata include the package DOI and repository URL.

The complete AI assistance disclosure is in `AI_DISCLOSURE.pdf` and `AI_DISCLOSURE.txt`. The manuscript acknowledgment gives the same disclosure.

## Citation and repository

The research-package DOI is [10.5281/zenodo.23812960](https://doi.org/10.5281/zenodo.23812960). The repository is [dvgyl/ranking-certificates](https://github.com/dvgyl/ranking-certificates).
