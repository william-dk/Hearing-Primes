"""Offline numerical zero field and adaptive data selection."""
from __future__ import annotations
import bisect
import csv
import hashlib
import math
from pathlib import Path

SOURCE_REFERENCE = "data/provenance.json"
FORMULA_REFERENCE = "README.md#zero-field-and-reference"

def insufficient_zero_cache(path):
    raise RuntimeError(
        "The bundled zero cache is insufficient for this count and tolerance. "
        "Supply an expanded, verified indexed table inside data/ and rerun. "
        "No network request, repeated entries, or fabricated zeros will be used."
    )

def load_zeros(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows = list(csv.DictReader(f))
    assert [int(r["index"]) for r in rows] == list(range(1,len(rows)+1)), "Zero cache must be a contiguous indexed prefix"
    values = [float(r["gamma"]) for r in rows]
    assert values and values[0] > 0
    assert all(math.isfinite(g) for g in values)
    assert all(a < b for a,b in zip(values,values[1:])), "Zero ordinates must increase"
    return values

def prime_powers(primes,maximum):
    result = []
    for p in primes:
        q = p
        while q <= maximum:
            result.append((q,math.log(p)))
            q *= p
    return sorted(result)

def exact_prime_window(a,b,powers):
    """Exact prime-power step integral plus analytic elementary correction terms.

Average of (psi(x)-x+ln(2*pi)+0.5*ln(1-x^-2))/sqrt(x) over ln(x).
Jumps have measure zero in this integral. The logarithm correction uses a
convergent power series whose omitted tail is < 1e-24 for a >= 2.
"""
    assert 2 <= a < b
    du = math.log(b/a)
    psi = 2*math.fsum(w*(1/math.sqrt(max(a,q))-1/math.sqrt(b)) for q,w in powers if q < b)
    main = -2*(math.sqrt(b)-math.sqrt(a))
    constant = 2*math.log(2*math.pi)*(1/math.sqrt(a)-1/math.sqrt(b))
    elementary = 0.5*math.fsum(
        (b**(-(2*m+0.5))-a**(-(2*m+0.5)))/(m*(2*m+0.5)) for m in range(1,41))
    return (psi+main+constant+elementary)/du

def zero_point(x,gammas):
    u = math.log(x)
    return -2*math.fsum((0.5*math.cos(g*u)+g*math.sin(g*u))/(0.25+g*g) for g in gammas)

def zero_window(a,b,gammas):
    u0,u1 = math.log(a),math.log(b)
    middle,half = (u0+u1)/2,(u1-u0)/2
    # Integral of exp(i*gamma*u) over u gives the sinc factor exactly.
    return -2*math.fsum(
        math.sin(g*half)/(g*half)*(0.5*math.cos(g*middle)+g*math.sin(g*middle))/(0.25+g*g)
        for g in gammas)

def adaptive_field(primes,windows,cache_path,seconds_per_unit,harmony_seconds,tolerance=0.002):
    """Select real zero data using range, musical resolution, and measured error.

    At least len(primes) zeros is a conservative project budget, not a theorem
    pairing the nth prime to the nth zero. The actual stopping test compares
    the truncated field against the known prime-power log-window average.
    """
    values = load_zeros(cache_path)
    xmax = primes[-1]
    dx = min(xmax-2,harmony_seconds/seconds_per_unit)
    if dx <= 0:
        raise ValueError("Prime range is too small")
    spectral_cutoff = 2*math.pi/math.log(xmax/(xmax-dx))
    while len(values) < len(primes) or values[-1] <= spectral_cutoff:
        values = insufficient_zero_cache(cache_path)
    initial = max(len(primes),bisect.bisect_right(values,spectral_cutoff))
    powers = prime_powers(primes,xmax)
    truth = [exact_prime_window(a,b,powers) for a,b in windows]
    history = []
    count = initial
    while True:
        if count > len(values):
            values = insufficient_zero_cache(cache_path)
        used = values[:count]
        measured = [zero_window(a,b,used) for a,b in windows]
        errors = [x-y for x,y in zip(measured,truth)]
        maximum = max(abs(e) for e in errors)
        rms = math.sqrt(math.fsum(e*e for e in errors)/len(errors))
        history.append(dict(zero_count=count,gamma_max=used[-1],
                            max_normalized_log_window_error=maximum,
                            rms_normalized_log_window_error=rms))
        if maximum <= tolerance:
            break
        count = max(count+1,count*2)
    return used,measured,truth,dict(
        policy="At least prime_count as a conservative budget, range/resolution cutoff, then increase until measured log-window error meets tolerance.",
        minimum_count_budget=len(primes),initial_spectral_cutoff=spectral_cutoff,
        initial_zero_count=initial,selected_zero_count=len(used),
        tolerance=tolerance,history=history,
        claim="Measured approximation accuracy on the analyzed windows only; not a universal truncation-error proof and not an exact reconstruction.",
        source_reference=SOURCE_REFERENCE,formula_reference=FORMULA_REFERENCE,
        cache_sha256=hashlib.sha256(cache_path.read_bytes()).hexdigest(),cached_count=len(values))

def zeta_euler_maclaurin(gamma):
    """Independent complex zeta evaluation for numerical source spot checks."""
    s = complex(0.5,gamma)
    n = max(64,math.ceil(2*gamma))
    z = sum(k**(-s) for k in range(1,n))
    z += n**(1-s)/(s-1)+0.5*n**(-s)
    coefficients = [1/12,-1/720,1/30240,-1/1209600,1/47900160,
                    -691/1307674368000,7/523069747200,
                    -3617/10670622842880000]
    rising = s
    for k,c in enumerate(coefficients,1):
        if k > 1:
            rising *= (s+2*k-3)*(s+2*k-2)
        z += c*rising*n**(-s-2*k+1)
    return z

def audit_zero_source(gammas):
    indices = sorted({0,len(gammas)-1,*[round(i*(len(gammas)-1)/31) for i in range(32)]})
    checks = [dict(zero_index=i+1,gamma=gammas[i],
                   absolute_zeta_residual=abs(zeta_euler_maclaurin(gammas[i]))) for i in indices]
    maximum = max(c["absolute_zeta_residual"] for c in checks)
    assert maximum < 2e-6, "Published zero source failed independent numerical spot checks"
    return dict(method="Independent Euler-Maclaurin evaluation of zeta(0.5+i*gamma)",
                checked_count=len(checks),maximum_absolute_zeta_residual=maximum,checks=checks,
                limitation="Numerical spot checks of sourced approximations; not a new proof of zeros or completeness.")
