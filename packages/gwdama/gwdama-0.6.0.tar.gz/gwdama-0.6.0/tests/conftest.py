# tests/conftest.py
import os
import numpy as np
import pytest

'''# --- NumPy 2.x compatibility shims for legacy aliases ---
import numpy as _np
for _name, _typ in [('float', float), ('int', int), ('complex', complex), ('bool', bool), ('object', object)]:
    if not hasattr(_np, _name):
        setattr(_np, _name, _typ)
del _np, _name, _typ'''

# Use a non-interactive backend for Matplotlib before importing pyplot (avoid display issues)
import matplotlib
matplotlib.use("Agg")

from gwdama.io import GwDataManager

@pytest.fixture(scope="session", autouse=True) # runs once per entire test session
def _seed_rng():
    np.random.seed(1234)

@pytest.fixture
def dama():
    # fresh in-memory dama for most tests -> each test that takes dama as an argument gets a fresh instance
    return GwDataManager("test_dama")

# Generates a reproducible 1D white noise time series
@pytest.fixture
def white_noise_1d(): 
    N = 50_000  # big enough for PSD but still fast
    fs = 2048
    t = np.arange(N) / fs
    data = np.random.normal(0, 1, size=N)
    return {"t": t, "fs": fs, "data": data}

# I/O tests: we write datasets to this HDF5 file, then read them back to check round-trip integrity, without polluting the project directory
@pytest.fixture
def tmp_h5(tmp_path):
    return tmp_path / "roundtrip.h5"

def pytest_configure(config):
    config.addinivalue_line("markers", "network: tests requiring network connectivity")
    config.addinivalue_line("markers", "slow: time-consuming tests")

# A guard fixture for tests that would try to fetch GWOSC open data (requires network or CVMFS).
# @pytest.fixture
# def require_gwosc_env():
#     """Skip GWOSC tests unless GWOSC_TEST=1 is set."""
#     if os.environ.get("GWOSC_TEST") != "1":
#         pytest.skip("Set GWOSC_TEST=1 to enable GWOSC online/local tests.")