# Release 1.0.0

This release contains the manuscript, mathematical supplement, active LaTeX sources, and computational evidence for a small exploratory implementation check.

All 20 planned synthetic instances completed. A separate scalar verification pass checked all 20 saved instances and reported no failures. The check covers 81,920 correction subsets, 3900 one-event decisions, 27,300 two-event decisions, and 260 budget-specific edge-relaxation certificates.

The check uses N=200 examples, M=6 models, r=12 flagged labels, and zero reversal margin. The limits are 1/10 and 1/5. Recorded-score ties use model index. Corrected-score ties are not reversals. All objective and limit comparisons use exact integers.

The results apply to these fixed synthetic inputs and this implementation. They do not establish practical benefit, runtime savings, scalability, or reliability on future data. The stored timings are operational records. They are not benchmark results.

The computational code is under MIT. The author-owned manuscript, sources, data, results, certificates, and documentation are under CC BY 4.0. Third-party files retain their original terms. See `LICENSE.md`.
