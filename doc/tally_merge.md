# Tally merge modes and MCNP validation

Checked against **MCNP 6.3.1 Theory & User Manual**, LA-UR-24-24602, Rev. 1,
using the PDF supplied with this workspace:

- Section 2.6.1, equations (2.209), (2.219), and (2.222): history-score mean,
  population variance, and variance of the mean (printed pages 144–145).
- Section 2.6.4, equations (2.226a–b): per-starting-history normalization and
  relative error (printed pages 147–148).
- Sections E.6–E.7: `merge_mctal.pl` and `merge_meshtal.pl`, with examples of
  statistically independent, otherwise identical calculations (printed pages
  978–982). These utilities pool histories; they do not add source responses.

The local PDF viewer page numbers are four higher than the printed numbers.
The [published manual](https://mcnp.lanl.gov/pdf_files/TechReport_2024_LANL_LA-UR-24-24602Rev.1_KuleszaAdamsEtAl.pdf)
and the manual's referenced
[LANL tally-merge tutorial, slides 7–10](https://mcnp.lanl.gov/pdf_files/TechReport_2008_LANL_LA-UR-08-00249_Brown.pdf)
provide the supporting definitions and pooled-moment derivation.

Let `m_i`, `R_i`, and `N_i` be each run's printed bin value, relative error,
and actual tally-header NPS. These bin values are already normalized by that
run's histories; they are not unnormalized score sums. Plot multipliers and
per-MeV display normalization are never used as merge inputs.

## Default: add source contributions

Leave **Normalize merge by total NPS** unchecked. Inputs must have equal NPS.

```
M = sum(m_i)
sigma = sqrt(sum((m_i * R_i)^2))
R = sigma / abs(M)
```

This is independent-error propagation for a sum of source responses, matching
the original FMESH merge calculation. It is appropriate when each input is an
additive contribution on the intended common physical normalization. It is
not the operation performed by the MCNP statistical merge utilities.
Equal NPS does not establish equal physical source strengths or compatible
source normalization. If the sources require different physical coefficients,
those must be accounted for before their contributions are added.

The output retains the common NPS as a convention for this summed response;
it is **not** the total number of independently pooled histories. The result is
named `merged_<timestamp>.o`. Different source definitions alone do not ensure
statistical independence: shared histories or random streams can require
covariance terms that ordinary output tables do not provide.

## Optional: normalize by total NPS

Check **Normalize merge by total NPS**. Positive, known NPS is required for each
input, but counts may differ. The result is `merged_<timestamp>_NPSnorm.o`, with
the sum of input NPS recorded in its tally header.

The MCNP pooled-history calculation is:

```
N = sum(N_i)
S_i = N_i * m_i
Q_i = N_i * m_i^2 * (1 + N_i * R_i^2)
M = sum(S_i) / N
sigma^2 = (sum(Q_i) / N - M^2) / N
R = sigma / abs(M)
```

`S_i` and `Q_i` reconstruct the first and second history-score sums using MCNP's
history-based variance convention (division by `N`, not `N - 1`). No Bessel
correction is introduced. For numerical stability, the implementation uses the
algebraically equivalent centered expression, with `w_i = N_i / N`:

```
sigma^2 = sum((w_i * m_i * R_i)^2) + sum(w_i * (m_i - M)^2) / N
```

The second term accounts for differences between run means. Omitting it would
propagate errors of a weighted combination rather than reproduce MCNP's pooled
history statistics. The same calculation is applied separately to the reported
energy-integrated totals and their own errors; total uncertainty is not inferred
from bin errors, which lack inter-bin covariance information.

The manual's intended use is independent, non-overlapping runs of the same
physical problem and source distribution. If source definitions differ, the
mean becomes a source mixture weighted by `N_i / N`; simulation counts are not
automatically physical source strengths. Its pooled error describes pooled
history statistics, not the propagated uncertainty of a fixed-weight sum of
distinct source contributions. With two equal-NPS inputs, values 2 and 6 give
8 in default sum mode and 4 in normalized mode.

## Validation and limitations

Both modes require matching particle, tally type, value count, and exact energy
boundaries, including the lower boundary. Missing NPS, invalid data, or incompatible
inputs produce a warning before any output file is created. These checks cannot
establish that geometry, material data, tally response, source normalization,
random streams, and histories are physically compatible; ordinary parsed tally
tables do not contain all of that information.

An all-zero bin has zero relative error. If nonzero contributions cancel to a
zero result with nonzero absolute uncertainty, merging is rejected: a finite
relative-error column cannot encode that result. The earlier implementation
silently wrote zero error for this case, following the FMESH script; that is not
justified by the manual's all-zero-score convention and has been corrected.

Statistical checks and fluctuation charts cannot be reconstructed and remain
N/A. The saved file is an MCNP-style tally table reloadable by this plotter,
not a full simulation output or an MCTAL file. Printed input precision limits
the precision of reconstructed statistics. Do not include an original run again
when merging a result that already contains it; the plotter has no complete
history-overlap tracking.

The regression tests compare normalized results with statistics calculated
directly from synthetic per-history scores, including unequal NPS, different
run means, sequential merges, and output/reload round trips.
