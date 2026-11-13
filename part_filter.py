"""Which blind_ber_<part>.json files stay out of the main results (blind_ber.merge, est3/plots.blind_parts): smoke
tests and the BLIND_IMPLEMENTATION/testing/ parts. Testing parts are named t-<...> or contain "tst" / "smoke" (2026-11-13
rule); the parts merged into blind_ber.json before the rule are kept (TEST_KEEP), so the current results do not change;
EXCLUDE_PARTS drops named parts explicitly."""

# merged into blind_ber.json (2026-11-12 19:40) before the rule, match it: kept until a decision to drop them
TEST_KEEP = ("t-dump10", "t-dump15a", "t-dump15b")
# explicit exclusions; candidates (testing/run.py parts carrying baseline rows, not yet decided): srch10, srch15, srch2,
# srch25, nph15a, nph15b (merged), nf10a, nf10b, nf15a, nf15b, nf15c, nn15a, nn15b, nn15c (not merged yet)
EXCLUDE_PARTS = ()


def test_part(part):
    """True: part (the name between blind_ber_ and .json) is a smoke / testing part, left out of the main results."""
    if part in EXCLUDE_PARTS or "smoke" in part:
        return True
    return (part.startswith("t-") or "tst" in part) and part not in TEST_KEEP
