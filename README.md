# v1_1000 Primes

A self-contained, MIDI-only sonification of the first **1,000 primes**, with accompaniment informed by a genuine, adaptively selected spectrum of Riemann zeta zeros.

Prime positions determine melody timing; prime gaps determine melody pitch. The selected zeros contribute collectively to a numerical field on the same number line. Averaged field values then inform a sparse, two-note accompaniment.

The texture is **homophony**: one clear melody over slow harmony. The intended instruments are **Felt Piano** and **Warm Pad**, chosen for a clean, spacious, meditative sound.

## Reference result

| Item | Included reference |
| --- | --- |
| Primes | First 1,000; 2 through 7,919 |
| Melody note events | 1,000 |
| Positive-imaginary-part zeros used | 19,152 |
| Highest selected imaginary part | 17,375.901922010 |
| Bundled zero cache | Contiguous first 20,923 entries |
| Planned score span | Approximately 17 minutes 6 seconds |
| Accompaniment sections | 263 |
| Accompaniment note events | 526 |
| Maximum simultaneous MIDI notes | 3 |
| Window-error tolerance | 0.002 |
| Maximum measured normalized window error | 0.0013181341645151223 |

The **19,152 zeros are numerical inputs, not simultaneous musical voices**. They are not paired individually with the 1,000 primes.

Open [the included two-track MIDI](outputs/v1_1000_Primes.mid) in your music software. Assign Felt Piano to the melody track and Warm Pad to the accompaniment track. MIDI stores notes and timing; it does not include a particular plugin, sample library, or effect preset. The General MIDI fallback programs are 0 and 89, using zero-based numbering.

The MIDI ending can differ slightly from the planned score span because players may omit trailing silence.

## Project contents

| Directory or file | Purpose |
| --- | --- |
| [src/dynamic_homophony.py](src/dynamic_homophony.py) | Prime melody, analysis windows, harmonic arrangement, and offline export |
| [src/zero_field.py](src/zero_field.py) | Zero-data loading, collective field, prime-power reference, adaptive selection, and source checks |
| [src/audio_core.py](src/audio_core.py) | Musical event, MIDI, and table utilities |
| [src/render_core.py](src/render_core.py) | Two-track MIDI validation |
| [data/odlyzko_zeros.csv](data/odlyzko_zeros.csv) | Bundled numerical zero cache |
| [data/zeros_used.csv](data/zeros_used.csv) | Selected 19,152-zero prefix used by the reference |
| [data/provenance.json](data/provenance.json) | Data attribution, stated precision, and hashes |
| [results/](results/) | Reference event tables, parameters, numerical checks, and validation |
| [outputs/](outputs/) | MIDI output only |

All required project files are included here. The default calculation works offline, uses project-relative paths, and does not read another project directory. Runtime input and output path options are restricted to this directory. No recorded audio or media archives are included or generated.

## Run locally

**Requirement: Python 3.10 or newer.** Only the Python standard library is used; no package installation, API key, network connection, or audio encoder is required.

From this directory:

```shell
python src/dynamic_homophony.py --count 1000 --zero-tolerance 0.002 --midi-only
```

MIDI-only mode is already the default; the explicit flag documents the intended export. Every run creates a uniquely named MIDI file in `outputs/` and calculation records in `results/generated/`. It preserves the included reference MIDI and records.

Options:

| Option | Default | Meaning |
| --- | --- | --- |
| `--count` | `1000` | Number of primes in the prefix; at least 2 |
| `--zero-tolerance` | `0.002` | Maximum accepted normalized logarithmic-window error |
| `--seconds-per-unit` | `27/209` | Seconds per unit of the number line |
| `--data` | `data/odlyzko_zeros.csv` | Indexed zero cache inside this project |
| `--out` | `outputs` | MIDI destination inside this project |
| `--midi-only` | Enabled | MIDI and calculation records only |

Larger ranges or tighter tolerances can require more zeros than the bundled cache contains. The program then stops clearly. Additional verified indexed data must be supplied inside `data/`; it never fabricates or loops entries and makes no network request.

## Prime melody

### Timing

For prime value $p$, the note onset is:

$$
t(p)=0.8+(p-2)\frac{27}{209}\quad\text{seconds}.
$$

Thus the time between two notes is proportional to the actual prime gap. Primes are not placed on an equally spaced beat grid.

### Pitch

For consecutive primes, let $g_n=p_n-p_{n-1}$. The first note uses the explicit seed $g_1=1$.

With $d_n=\lfloor g_n/2\rfloor$ and pentatonic offsets $A=[0,2,4,7,9]$:

$$
m_n=60+12\left\lfloor\frac{d_n}{5}\right\rfloor+A[d_n\bmod5].
$$

Here $m_n$ is MIDI pitch. Its equal-tempered frequency is $440\,2^{(m_n-69)/12}$ Hz.

| Prime gap | Note |
| --- | --- |
| 1, first-note seed | C4 |
| 2 | D4 |
| 4 | E4 |
| 6 | G4 |
| 8 | A4 |
| 10 | C5 |
| 12 | D5 |
| 14 | E5 |

The five-note scale is an artistic mapping, not a number-theoretic property. It orders gap sizes by pitch but does not preserve gap ratios as frequency ratios. The reference melody spans C4–E7; the maximum prime gap is 34.

Notes last at most 0.36 seconds and normally at most 78% of the next onset interval. The melody remains monophonic.

## Zero field and reference

### Source data

The bundled data comes from **Andrew Odlyzko, Tables of zeros of the Riemann zeta function**, specifically the indexed table of the first 100,000 positive-imaginary-part zeros. Its stated imaginary-part error bound is $3\times10^{-9}$.

The mathematical reference is the **NIST Digital Library of Mathematical Functions, section 25.16**, on zeta functions and prime distribution. Attribution, local filenames, numerical precision, and SHA-256 records are retained in [data/provenance.json](data/provenance.json). No external file or website is needed to run the reference case.

The cache is checked for contiguous indices, positive finite ordinates, and increasing order. Independent Euler–Maclaurin evaluation spot-checks 32 selected zeros; the largest checked $|\zeta(1/2+i\gamma)|$ is approximately $9.84\times10^{-9}$. These are numerical source checks, not a proof of every entry or of the Riemann hypothesis.

### Collective contribution

For the tabulated zeros $\rho_k=1/2+i\gamma_k$, calculate:

$$
S_N(x)=-2\operatorname{Re}\sum_{k=1}^{N}
\frac{e^{i\gamma_k\ln x}}{1/2+i\gamma_k}.
$$

This is the selected nontrivial-zero contribution in the explicit formula divided by $\sqrt{x}$. Conjugate zeros are incorporated through the factor of two and the real part. There is no tuning denominator based on the first zero.

Every selected zero participates in every analysis window. Individual values at prime positions are also saved in [results/prime_zero_field.csv](results/prime_zero_field.csv).

Accompaniment onsets are spaced 3.9 seconds apart. Each section maps to an interval $[a,b]$ on the prime number line. The finite zero field is averaged analytically in $\ln x$, using a sinc factor for each zero rather than sparse samples of rapidly oscillating terms.

For comparison, use the actual prime-power function:

$$
\psi(x)=\sum_{p^r\le x}\ln p
$$

and average the following over the same logarithmic window:

$$
R(x)=\frac{\psi(x)-x+\ln(2\pi)+\tfrac12\ln(1-x^{-2})}{\sqrt{x}}.
$$

The prime-power step integral is evaluated analytically, with elementary terms and a convergent series for the logarithmic correction. This is a reference for the normalized field; $\psi(x)$ is not the ordinary prime count $\pi(x)$.

### Adaptive prefix size

An initial spectral cutoff depends on the prime range and nominal harmonic resolution. The prime count also provides a conservative minimum numerical budget; this is an engineering choice, not an nth-prime/nth-zero correspondence.

Increase the real zero prefix until the maximum measured window difference satisfies:

$$
\max_j|\overline S_{N,j}-\overline R_j|\le0.002.
$$

| Tested zero count | Maximum normalized window error |
| --- | --- |
| 1,197 | 0.006470114 |
| 2,394 | 0.013942007 |
| 4,788 | 0.005293794 |
| 9,576 | 0.003054353 |
| **19,152** | **0.001318134** |

The final RMS window error is approximately 0.000136326. Intermediate errors need not decrease monotonically. The selected count is the first passing candidate in this tested sequence, not a proven minimum or universal matching ratio.

The tolerance measures **absolute error in a normalized logarithmic-window average**. It is not a percentage, a prime-count error, a pointwise guarantee, or an infinite-range truncation theorem.

## From field values to harmony

1. Rank each section's averaged field value within the full piece.
2. Map its empirical quartile to a target from C, Am, F, G.
3. Compare those families against the local prime melody.
4. Select a family using melody compatibility, a target-mismatch penalty, and a mild repetition penalty.
5. Play only its root and fifth as the pad accompaniment.

| Family | MIDI pad notes | Reference sections |
| --- | --- | --- |
| C | C3 + G3 | 70 |
| Am | A2 + E3 | 77 |
| F | F2 + C3 | 53 |
| G | G2 + D3 | 63 |

Because thirds are omitted, the family labels describe the arrangement context; A and E alone do not establish a minor triad. Seventeen sections differ from their field-derived target after musical compatibility selection. Targets, final choices, and override reasons are stored in [results/chord_plan.csv](results/chord_plan.csv).

The data is genuine, but quartile-to-harmony assignment, the pentatonic scale, timing scale, chord vocabulary, and instrument choices remain explicit compositional decisions.

## Validation and reproducibility

The committed [validation record](results/validation.json) covers the numerical source, selected spectrum, field approximation, MIDI counts, and musical event structure. The reference contains 1,000 melody note-ons and 526 pad note-ons, with at most three simultaneous notes.

The source, cache, selected zero data, and frozen calculation records are all included in this directory. A fresh run recreates the score independently of its original authoring location. It does not overwrite the reference MIDI.

The implementation is batch-based: changing the prime range can change the selected zero prefix and global field quartiles, so a rerun may change earlier accompaniment choices. Stable incremental composition is not implemented.

This project presents an auditable numerical-to-musical mapping. It does not claim an exact acoustic reconstruction of the prime count, a proof of the Riemann hypothesis, or subjective approval of every musical choice.
