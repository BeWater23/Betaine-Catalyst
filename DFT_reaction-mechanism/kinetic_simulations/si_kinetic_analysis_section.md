# Kinetic Analysis

Concentration-time data for N-methylmorpholine (NMM), the iminoester, and the
product were analyzed using the Python notebook `kinetic_investigation.ipynb`.
The input data were read from the first worksheet of
`conc-time-profile.xlsx`. The analysis used the concentration columns
`c(nmm)`, `c(imino)`, and `c(product)` directly. Time values were converted to
elapsed minutes by subtracting the first time point from each measurement. The
data set contained 17 time points spanning 0 to 113.2 min.

Nonlinear least-squares fitting was performed with `scipy.optimize.curve_fit`.
The nominal catalyst concentration was taken as
$c_\mathrm{cat}=2.08 \times 10^{-4}$ M, with the catalyst-concentration range
$1.04 \times 10^{-4}$ to $3.13 \times 10^{-4}$ M used to estimate the
sensitivity of the derived activation free energies. The initial
concentrations used in the fits were $c_{\mathrm{NMM},0}=0.06776$ M and
$c_{\mathrm{imino},0}=0.09074$ M.

## Integrated Rate Laws Used for Fitting

Two kinetic models were evaluated. In the first treatment, NMM depletion was
fit with an apparent first-order expression. For a species $i$, where
$i=\mathrm{NMM}$ or $i=\mathrm{imino}$, the fitted differential and
integrated forms were:

$$
\frac{dc_i}{dt} = -c_\mathrm{cat}kc_i
$$

$$
c_i(t) = c_{i,0}\exp(-c_\mathrm{cat}kt)
$$

The product concentration was described from the fitted NMM depletion with an
additional maximum-yield term:

$$
c_\mathrm{product}(t) = Y_\mathrm{max}
\left(c_{\mathrm{NMM},0} - c_\mathrm{NMM}(t)\right).
$$

In the second treatment, NMM and iminoester depletion were fit with the
integrated second-order expression for unequal initial concentrations, again
including $c_\mathrm{cat}$ explicitly in the exponential term:

$$
\frac{dc_\mathrm{NMM}}{dt}
= -c_\mathrm{cat}k c_\mathrm{NMM}c_\mathrm{imino}
$$

$$
c_\mathrm{NMM}(t)
=
\frac{
c_{\mathrm{NMM},0}
\left(c_{\mathrm{NMM},0}-c_{\mathrm{imino},0}\right)
\exp\left[\left(c_{\mathrm{NMM},0}-c_{\mathrm{imino},0}\right)c_\mathrm{cat}kt\right]
}{
c_{\mathrm{NMM},0}
\exp\left[\left(c_{\mathrm{NMM},0}-c_{\mathrm{imino},0}\right)c_\mathrm{cat}kt\right]
-c_{\mathrm{imino},0}
}
$$

$$
c_\mathrm{imino}(t)
=
\frac{
c_{\mathrm{imino},0}
\left(c_{\mathrm{imino},0}-c_{\mathrm{NMM},0}\right)
\exp\left[\left(c_{\mathrm{imino},0}-c_{\mathrm{NMM},0}\right)c_\mathrm{cat}kt\right]
}{
c_{\mathrm{imino},0}
\exp\left[\left(c_{\mathrm{imino},0}-c_{\mathrm{NMM},0}\right)c_\mathrm{cat}kt\right]
-c_{\mathrm{NMM},0}
}
$$

The second-order product trace was fit using the corresponding NMM depletion
profile and the same bounded yield-cap parameter:

$$
c_\mathrm{product}(t) =
Y_\mathrm{max}\left(c_{\mathrm{NMM},0}-c_\mathrm{NMM}(t)\right),
\qquad 0 \leq Y_\mathrm{max} \leq 1.
$$

The fitted product-yield cap accounts for the fact that the measured product
concentration plateaus below the full stoichiometric NMM concentration.

Activation free energies were estimated from the fitted rate constants using
the Eyring equation at 298.15 K,

$$
\Delta G^\ddagger = -RT \ln\left(\frac{kh}{k_\mathrm{B}T}\right).
$$

## Results

The first-order NMM fit gave $k = 2.04 \times 10^{2}$ min$^{-1}$, equivalent
to $3.41$ s$^{-1}$ after conversion from minutes to seconds, with a fitted
product yield cap of 0.924. This corresponds to
$\Delta G^\ddagger = 70.0$ kJ mol$^{-1}$
$= 16.73$ kcal mol$^{-1}$. Propagating the catalyst-concentration range
gave $\Delta G^\ddagger = 68.3$-71.0 kJ mol$^{-1}$.

The second-order NMM fit gave $k = 3.45 \times 10^{3}$
M$^{-1}$ min$^{-1}$, equivalent to $57.6$
M$^{-1}$ s$^{-1}$ after conversion from minutes to seconds, with a fitted
product yield cap of 0.954. This corresponds to
$\Delta G^\ddagger = 63.0$ kJ mol$^{-1}$
$= 15.05$ kcal mol$^{-1}$. Propagating the same
catalyst-concentration range gave
$\Delta G^\ddagger = 61.3$-64.0 kJ mol$^{-1}$. The second-order treatment
therefore gave the closest agreement with the DFT barrier of
64.3 kJ mol$^{-1}$ (15.37 kcal mol$^{-1}$).

The final measured product concentration was 0.06015 M, corresponding to 88.8%
of the initial NMM concentration. The fitted product-yield caps of 92.4% and
95.4% for the first- and second-order fits, respectively, are consistent with
the observed product plateau.

| Kinetic treatment | Fitted trace | Fitted rate constant | Product yield cap | Derived $\Delta G^\ddagger$ |
| --- | --- | --- | --- | --- |
| First-order apparent depletion | NMM | $2.04 \times 10^{2}$ min$^{-1}$ ($3.41$ s$^{-1}$) | 0.924 | 70.0 kJ mol$^{-1}$ (16.73 kcal mol$^{-1}$) |
| Second-order apparent depletion | NMM | $3.45 \times 10^{3}$ M$^{-1}$ min$^{-1}$ ($57.6$ M$^{-1}$ s$^{-1}$) | 0.954 | 63.0 kJ mol$^{-1}$ (15.05 kcal mol$^{-1}$) |
| DFT comparison | -- | -- | -- | 64.3 kJ mol$^{-1}$ (15.37 kcal mol$^{-1}$) |

For reference, fitting the iminoester depletion trace gave
$k = 1.05 \times 10^{2}$ min$^{-1}$ in the first-order treatment and
$k = 4.38 \times 10^{3}$ M$^{-1}$ min$^{-1}$ in the second-order
treatment. The NMM-derived values above were used for the reported comparison
because the product trace was modeled directly from NMM consumption.
