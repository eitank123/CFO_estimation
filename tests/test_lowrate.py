"""Low-rate study (polar_ber_experiment.py, CFO_STUDY=lowrate): code table on the SNR grid, CRB, the CRB and
NN + CRC search sources, operating-point helpers. Run: py -m pytest tests -q"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["CFO_STUDY"] = "lowrate"

import polar_ber_experiment as p  # noqa: E402
from polar import PolarCode  # noqa: E402


def test_lowrate_codes_on_an_snr_grid():
    for name, A, lo in (("R=0.025", 26, -12), ("R=0.05", 51, -11), ("R=0.75", 768, 0)):
        assert p.CODES[name][0] == A and p.CODES[name][1] == 11
        snrs = [p.esn0(name, e) for e in p.CODES[name][2]]
        assert snrs[0] == pytest.approx(lo, abs=1e-3)
        assert np.allclose(np.diff(snrs), 0.5, atol=1e-3)
    assert p.esn0("R=0.1", p.CODES["R=0.1"][2][0]) == pytest.approx(-9.0, abs=1e-3)   # extended below -5 dB


def test_crb_matches_main_formula():
    import main
    for snr in (-5.0, 0.0, 6.0):
        assert p.crb_std(snr) ** 2 == pytest.approx(main.compute_cfo_crlb(np.array([snr]), 128)[0], rel=1e-12)
    assert p.crb_std(-5.0) == pytest.approx(4.79e-4, rel=0.01)
    assert p.crb_std(-5.0, 512) == pytest.approx(p.crb_std(-5.0) * np.sqrt(128 * (128 ** 2 - 1) / (512 * (512 ** 2 - 1))))


def test_decoder_reports_crc_and_metric():
    code = PolarCode(1024, 51, 11, 8)
    rng = np.random.default_rng(1)
    data = rng.integers(0, 2, (20, 51), dtype=np.uint8)
    cw = code.encode(data)
    llr = (1 - 2.0 * cw) * 8.0
    dec, ok, pm = code.decode(llr, return_info=True)
    assert (dec == data).all() and ok.all()
    _, ok_noise, pm_noise = code.decode(rng.normal(0, 1, (200, 1024)), return_info=True)
    assert ok_noise.mean() < 0.05 and np.median(pm_noise) > np.median(pm)    # noise: CRC fails, worse metric


def _point(src, snr, frames=400, seed=7):
    eb = [e for e in p.CODES["R=0.1"][2] if abs(p.esn0("R=0.1", e) - snr) < 0.01][0]
    pf = os.path.join(os.environ.get("TEMP", "/tmp"), "test_lowrate.progress")
    return p.simulate_point(("R=0.1", eb, src, 8, 200, 10 ** 9, frames, seed, 0, pf))


def test_search_beats_nn_at_minus_4_db():
    # same seed = same data, CFO, phase and noise for every source (common random numbers)
    genie, nn, search = (_point(s, -4.0) for s in (p.GENIE, "SNR-aware NN", p.SEARCH))
    assert search["bler"] <= nn["bler"]
    assert nn["bler"] > 0.05 and search["bler"] < 0.02 and genie["bler"] < 0.01
    assert search["extra_decodes_per_frame"] > 0 and nn["extra_decodes_per_frame"] == 0
    assert search["rmse_cfo_final"] < search["rmse_cfo_first"]          # the search moves the CFO towards the truth
    assert search["undetected_bler"] <= search["bler"]


def test_crb_source_error_spread():
    r = _point(p.CRB_SRC, -4.0, frames=400)
    assert r["rmse_cfo_first"] == pytest.approx(p.crb_std(-4.0), rel=0.15)


def test_required_snr_interpolation():
    snr = np.array([-5.0, -4.0, -3.0])
    assert p.required_snr(snr, np.array([0.1, 0.001, 0.0])) == pytest.approx(-4.5)
    assert p.required_snr(snr, np.array([0.005, 0.001, 0.0])) == -5.0
    assert p.required_snr(snr, np.array([0.5, 0.2, 0.05])) is None


def test_search_variants_cost_less():
    """Same frames: stopping at the first CRC pass or halving the grid never needs more decodes than the full search,
    and both start from the same NN decision, so they are never worse than the NN alone."""
    nn, full, first, half = (_point(s, -5.0, frames=400) for s in ("SNR-aware NN", p.SEARCH, p.SEARCH_FIRST,
                                                                    p.SEARCH_HALF))
    assert first["extra_decodes_per_frame"] <= full["extra_decodes_per_frame"]
    assert half["extra_decodes_per_frame"] <= full["extra_decodes_per_frame"] * 0.6
    for v in (first, half):
        assert v["bler"] <= nn["bler"] and v["undetected_bler"] <= v["bler"]
