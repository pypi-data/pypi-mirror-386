import math
import numpy as np

from zolq.binding import (
    bell_demo,
    bind_reflection,
    project_reflection,
)

def is_prob(x, eps=1e-12):
    return (x >= -eps) and (x <= 1 + eps)

def density_from_state(vec):
    """Given a state vector (complex), return rho = |psi><psi| with trace=1."""
    v = vec / np.linalg.norm(vec)
    return np.outer(v, v.conj())

def test_project_increases_fidelity_on_bell():
    # Use default noise where we observed improvement
    res = bell_demo(p_dephase=0.20, p_depol=0.15, mode="project")
    assert "fidelity_before" in res and "fidelity_after" in res and "pass_probability" in res
    f_before = res["fidelity_before"]
    f_after = res["fidelity_after"]
    p_pass = res["pass_probability"]

    # Basic sanity
    assert is_prob(f_before)
    assert is_prob(f_after)
    assert is_prob(p_pass)
    # Post-selected projection should not decrease fidelity on the kept runs
    assert f_after + 1e-9 >= f_before

def test_twirl_returns_valid_fidelity():
    # Twirl is CPTP averaging; fidelity may or may not increase, but stays in [0,1]
    res = bell_demo(p_dephase=0.25, p_depol=0.20, mode="twirl")
    assert res["mode"] == "twirl"
    f_before = res["fidelity_before"]
    f_after = res["fidelity_after"]
    assert is_prob(f_before)
    assert is_prob(f_after)

def test_project_reflection_identity_is_noop():
    # Build a random pure state density matrix for 2 qubits (dim=4)
    rng = np.random.default_rng(7)
    v = rng.normal(size=4) + 1j * rng.normal(size=4)
    rho = density_from_state(v)
    I4 = np.eye(4, dtype=complex)

    # Project onto +1 eigenspace of identity -> should pass with prob=1 and be unchanged
    rho_p, p = project_reflection(rho, I4)
    # Pass probability is exactly 1
    assert math.isclose(p, 1.0, rel_tol=0, abs_tol=1e-12)
    # State unchanged (within numerical tolerance)
    assert np.allclose(rho_p, rho, atol=1e-10)

def test_bind_reflection_scores_in_range():
    # Check score range for the gentle (CPTP) reflection bind using R=I
    rng = np.random.default_rng(3)
    v = rng.normal(size=4) + 1j * rng.normal(size=4)
    rho = density_from_state(v)
    I4 = np.eye(4, dtype=complex)

    rho_p, s, phase, trace = bind_reflection(rho, I4)
    # Score mapped to [0,1]; trace contains the raw expectation in [-1,1]
    assert is_prob(s)
    assert "exp_R_before" in trace
    assert -1 - 1e-12 <= trace["exp_R_before"] <= 1 + 1e-12
    # Density matrix should remain valid (Hermitian, trace ~1, PSD-ish numerically)
    assert np.allclose(rho_p, rho_p.conj().T, atol=1e-10)
    tr = np.trace(rho_p)
    assert math.isclose(float(np.real(tr)), 1.0, abs_tol=1e-10)
