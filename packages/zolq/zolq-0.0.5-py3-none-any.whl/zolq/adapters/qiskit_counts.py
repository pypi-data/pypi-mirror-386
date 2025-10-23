import numpy as np

def counts_to_probvec(counts, nbits=None):
    if nbits is None:
        nbits = max(len(k) for k in counts)
    dim = 2**nbits
    p = np.zeros(dim)
    total = sum(counts.values())
    for bitstr, c in counts.items():
        idx = int(bitstr, 2)
        p[idx] = c / total
    return p

def diag_density_from_counts(counts, nbits=None):
    p = counts_to_probvec(counts, nbits)
    return np.diag(p.astype(complex))

def project_counts(counts, R, nbits=None):
    rho = diag_density_from_counts(counts, nbits)
    I = np.eye(rho.shape[0], dtype=complex)
    Pi = 0.5 * (I + R)
    num = Pi @ rho @ Pi
    p_pass = float(np.real(np.trace(num)))
    if p_pass <= 0:
        return counts, 0.0
    rho_p = (num / p_pass).real
    diag = np.real(np.diag(rho_p))
    diag = np.clip(diag, 0, 1)
    diag = diag / diag.sum() if diag.sum() > 0 else diag
    return diag, p_pass
