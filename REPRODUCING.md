# Verify the saved results

The saved inputs are sufficient to check the reported calculations. Verification does not generate a new sample. It flips the saved recorded labels and recounts model predictions with scalar Python loops. It also checks the saved primal and dual certificates with exact integers.

## Environment

The recorded run used Python 3.12.14, NumPy 2.3.5, and macOS 27.0.1 on an arm64 machine. The code uses POSIX signals for time limits. Use macOS or Linux. The current script does not support those time limits on Windows.

From the package root, create an environment and install the recorded NumPy version:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r computational-check/requirements.txt
```

The code has no SciPy dependency. The environment record gives the exact versions used for the saved run. A different environment has not been checked for identical generated inputs.

## Check the release files

From the package root, check the SHA-256 checksums:

```sh
shasum -a 256 -c SHA256SUMS
```

Each listed file must report `OK`. The computational code for the saved run has SHA-256:

```text
2ab2542e142b10c522f4e05481945fa44407af4815a29dc89cfdb4cff24c114f
```

## Verify a copy

The verifier writes its report and manifest into the supplied directory. Make a copy to keep the released evidence unchanged. Use a destination that does not already exist:

```sh
cp -R computational-check/data verification-copy
.venv/bin/python computational-check/certificate_check.py verify verification-copy
```

A successful verification exits with status zero. Its `verification.json` must contain `checked_instances` from 0 through 19 and an empty `failures` list. A nonzero exit status, timeout file, or listed failure is not a successful verification.

The archived report is in `computational-check/data/verification.json`. Verification timings and manifest contents can change in the copy. They are not mathematical results.

## Read the results

The fixed configuration uses 20 seed values, N=200, M=6, and r=12. Every instance has 4096 correction subsets. Each budget permits at most B flips among the flagged labels. All 15 model pairs have weight 1/15. The reversal margin is zero. The limits are 1/10 and 1/5.

The reference order uses decreasing recorded-label accuracy. Model index breaks a recorded-score tie. A pair reverses only when the later model has a strictly larger corrected count. A corrected-score tie does not count.

| File or field | Meaning |
|---|---|
| `input-NN.json` | Predictions, recorded labels, generated true labels, flagged indices, and seed for instance NN. |
| `result-NN.json` | Exact budget results, certificates, first crossings, and instance status. |
| `status.json` | Status of every planned instance. |
| `verification.json` | Saved-input verification result. |
| `environment.json` | Recorded software and machine information. |
| `exact_numerators[B] / Q` | Exact maximum reversal fraction U at budget B. |
| `separate_numerators[B] / Q` | Separate-event upper bound at budget B. |
| `H_numerators_denominator_2Q[B] / (2*Q)` | Exact edge-relaxation value at budget B. |
| `certificates[B]` | Graph, matching, cover, and primal and dual numerators at budget B. |

Here Q=15. Model and example indices start at zero. Bit k of a correction mask selects `flagged[k]`. A one bit flips that recorded binary label. Certificate values `x2`, `alpha2`, and `beta2` have denominator two.

The first-crossing fields use the strict condition that the objective exceeds the limit. Equality does not cross the limit. A value of 13 means no crossing was found through budget 12. It is not a measured breakdown budget beyond 12. The lower bound `b_L` certifies every budget below `b_L`. Its largest certified budget is `b_L-1` when `b_L` is at least one.

## Regenerate the fixed sample

The following optional commands generate the listed fixed inputs and compute the results in a new directory. They do not replace the archived run. Use a destination that does not already exist:

```sh
.venv/bin/python computational-check/certificate_check.py run computational-check/plan.json regenerated-data
.venv/bin/python computational-check/certificate_check.py verify regenerated-data
```

The plan imposes a 600-second run cap, a 30-second instance cap, a five-second certificate cap, and a 300-second verification cap. Incomplete or failed instances remain in the status records. A timeout does not mean that a reversal is impossible.

Compare the mathematical fields in the regenerated and archived result files. These include the recorded counts, order, pair list, reference minima, exact numerators, witness masks, bounds, certificates, and first crossings. Wall time, CPU time, environment text, and file hashes that include these records can differ. The archived timings do not measure speed relative to another method.

## Build the paper

Use a TeX installation with IEEEtran, natbib, hyperref, and the standard mathematics packages listed in the sources. Tectonic can build both documents and resolve their bibliographies. From the package root, use a new directory:

```sh
mkdir manuscript-build
unzip manuscript/active-sources.zip -d manuscript-build
cd manuscript-build
tectonic main.tex
tectonic supplement.tex
```

Compare the resulting main paper and supplement with the supplied PDFs. A successful LaTeX build checks the document build. It does not verify the mathematical claims or references.
