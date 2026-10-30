# Small synthetic implementation check

This package accompanies *Certified Model Ranking under Limited Label Errors*. It checks the binary event tests and the uniform-weight conflict certificate on 20 small synthetic prediction tables. It does not test the list constructions or establish practical benefit on real benchmarks.

Each input has 200 examples, six models, and 12 flagged labels. All 4096 correction subsets were enumerated. The code checks every budget from zero through 12. All 20 inputs completed, and an independent scalar verification pass checked their saved inputs and results. The sample contains 81,920 correction subsets, 3,900 one-event checks, 27,300 two-event checks, and 260 exact graph certificates. No mismatch or certificate failure was found in this sample.

The graph calculation uses a bipartite double cover. A matching and vertex cover produce half-integral primal and dual solutions. Integer checks establish feasibility and equal objectives. No numerical optimization solver is required. The recorded configuration is exploratory and fixed for this sample. It does not reproduce or validate results from other studies.

## Files

- `certificate_check.py`: generator, event tests, exact graph method, exhaustive reference, and independent saved-input verifier.
- `plan.json`: numerical settings, seeds, tie rule, and finite execution limits.
- `data/input-*.json`: all 20 generated inputs.
- `data/result-*.json`: every budget result, correction witness, and graph certificate.
- `data/status.json` and `data/verification.json`: complete status and verification records.
- `data/environment.json`: executed software versions and code checksum.
- `data/log-*.txt`: unfiltered process logs. Empty logs indicate no process output.
- `summary.json`: counts for the complete sample.
- `MANIFEST.json`: SHA-256 checksums of these files.

The configuration retains the executed numerical settings and limits. Administrative fields are omitted. Timing fields are execution receipts. They are not performance comparisons. The value 13 denotes no violation within the 12 permitted changes. It is not a finite breakdown budget beyond that range.

## Verify the saved sample

The recorded environment used Python 3.12.14 and NumPy 2.3.5 on macOS. The script uses Unix signals for its time limits. Use macOS or Linux. Install the version in `requirements.txt` in an isolated Python environment. Keep the supplied records unchanged and verify a copy:

```sh
cp -R data verification-copy
python3 certificate_check.py verify verification-copy
```

A successful check exits with status zero and lists all 20 checked instances with no failures. The verifier writes its new receipt and manifest in the copy. It checks corrections and certificates independently of the first enumeration. It does not regenerate the sample.

## Generate a new reproduction

Use a new output directory:

```sh
python3 certificate_check.py run plan.json reproduction
python3 certificate_check.py verify reproduction
```

The run cap is 600 seconds, with 30 seconds per input and five seconds per graph certificate. Verification has a separate 300-second cap. Every input has one attempt. Failed or incomplete outcomes remain visible. New timing receipts can differ. Saved inputs permit verification without relying on random generation across software versions.

## Interpret the results

At limits 1/10 and 1/5, the conflict-aware breakdown lower bound exceeded the separate-event bound in 5/20 and 10/20 inputs. The exact breakdown was finite in 16 and five inputs. The conflict-aware bound equaled it in 16/16 and 3/5 finite cases. All remaining inputs had no violation within the permitted range, and the certificate confirmed that result. These counts describe this small sample only. They do not prove general software correctness or a runtime advantage.

## License

The code is under the MIT License. Data, results, certificates, configuration, and documentation are under Creative Commons Attribution 4.0 International. See `LICENSE.md` and the included full license texts.
