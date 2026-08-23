"""Unit tests for the aria-reporter pytest plugin.

Run isolated sub-sessions with the `pytester` fixture so the plugin's own hooks
(active in this outer session only if configured — which we never do here) don't
interfere. Colour is disabled via ARIA_COLOR unset + non-tty in the subprocess.
"""
import pytest

pytest_plugins = ["pytester"]


CONFTEST = '''
from aria_reporter import configure
configure(
    phases={
        "TestPhaseOne": ("1", "First Phase"),
        "TestPhaseTwo": ("2", "Second Phase"),
    },
    friendly={
        "test_a": "Objective A",
        "test_b": "Objective B",
    },
    mission_id="test-1",
)
'''


def _run(pytester, test_body, conftest=CONFTEST):
    pytester.makeconftest(conftest)
    pytester.makepyfile(test_mission=test_body)
    # runpytest_subprocess so entry-point plugin + our conftest load exactly as
    # they would in a real mission; stderr carries the ARIA summary.
    return pytester.runpytest_subprocess("-p", "no:cacheprovider")


def test_all_pass_reports_phases_and_counts(pytester):
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
class TestPhaseTwo:
    def test_b(self): assert True
''')
    err = result.stderr.str()
    assert "Phase 1: First Phase" in err
    assert "Phase 2: Second Phase" in err
    assert "Objective A" in err
    assert "Objective B" in err
    assert "2 of 2 phases complete" in err
    assert "2 verified" in err
    assert result.ret == 0


def test_failure_surfaces_aria_hint(pytester):
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self):
        assert False, "ARIA: run make setup first"
''')
    err = result.stderr.str()
    assert "run make setup first" in err
    assert "1 deficient" in err
    # a deficient phase does not count as complete
    assert "0 of 2 phases complete" in err
    assert result.ret != 0


def test_partial_phase_failure_not_counted_complete(pytester):
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
    def test_b(self): assert False, "ARIA: nope"
''')
    err = result.stderr.str()
    # Phase 1 has one pass and one fail -> not complete
    assert "0 of 2 phases complete" in err
    assert "1 verified" in err
    assert "1 deficient" in err


def test_all_skipped_forces_nonzero_exit(pytester):
    result = _run(pytester, '''
import pytest
class TestPhaseOne:
    def test_a(self):
        pytest.skip("range unarmed")
''')
    err = result.stderr.str()
    assert "skipped" in err
    # the all-skip safeguard: inconclusive must not exit 0
    assert result.ret == 2


def test_inert_without_configure(pytester):
    # No configure() call -> plugin must not hijack output or exit code.
    result = _run(pytester, '''
def test_plain(): assert True
''', conftest="")
    err = result.stderr.str()
    assert "Phase" not in err
    assert "phases complete" not in err
    assert result.ret == 0


def test_unit_noun_configurable_for_capstones(pytester):
    conftest = '''
from aria_reporter import configure
configure(
    phases={"TestPhaseOne": ("1", "Recon")},
    friendly={"test_a": "Objective A"},
    mission_id="gateway",
    unit="Mission",
)
'''
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
''', conftest=conftest)
    err = result.stderr.str()
    assert "Mission 1: Recon" in err
    assert "1 of 1 missions complete" in err
    assert "Phase 1" not in err
    assert result.ret == 0


BADGE_CONFTEST = '''
from aria_reporter import configure
configure(
    phases={"TestPhaseOne": ("1", "First"), "TestPhaseTwo": ("2", "Second")},
    friendly={"test_a": "A", "test_b": "B"},
    mission_id="2-6",
)
'''


def test_badge_block_on_full_completion(pytester):
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
class TestPhaseTwo:
    def test_b(self): assert True
''', conftest=BADGE_CONFTEST)
    err = result.stderr.str()
    assert "Rank earned: Lieutenant" in err
    assert "img.shields.io/badge/SDC_Rank-Lieutenant-navy" in err
    assert "Mission_2.6-Counterattack-brightgreen" in err
    assert result.ret == 0


def test_no_badge_when_incomplete(pytester):
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
class TestPhaseTwo:
    def test_b(self): assert False, "ARIA: nope"
''', conftest=BADGE_CONFTEST)
    err = result.stderr.str()
    assert "Rank earned" not in err
    assert "shields.io" not in err


def test_no_badge_for_unknown_mission(pytester):
    conftest = BADGE_CONFTEST.replace('mission_id="2-6"', 'mission_id="does-not-exist"')
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
class TestPhaseTwo:
    def test_b(self): assert True
''', conftest=conftest)
    err = result.stderr.str()
    assert "Rank earned" not in err
    assert result.ret == 0


def test_shields_escape_handles_spaces_and_dashes():
    from aria_reporter.plugin import _shields_escape
    assert _shields_escape("Lieutenant Commander") == "Lieutenant_Commander"
    assert _shields_escape("Defence-in Depth") == "Defence--in_Depth"


def test_reward_for_public_helper():
    # #48 — public API used by aria-review.py to surface the badge in the PR
    # review from the same data the make-test summary emits.
    from aria_reporter import reward_for
    rank, md = reward_for("2-6")
    assert rank == "Lieutenant"
    assert "img.shields.io/badge/SDC_Rank-Lieutenant-navy" in md
    assert "Mission_2.6-Counterattack-brightgreen" in md
    # capstone earns Lieutenant Commander
    assert reward_for("master")[0] == "Lieutenant Commander"
    # unknown mission -> None (aria-review.py renders nothing)
    assert reward_for("does-not-exist") is None


def test_master_earns_lieutenant_commander(pytester):
    conftest = BADGE_CONFTEST.replace('mission_id="2-6"', 'mission_id="master", unit="Mission"')
    result = _run(pytester, '''
class TestPhaseOne:
    def test_a(self): assert True
class TestPhaseTwo:
    def test_b(self): assert True
''', conftest=conftest)
    err = result.stderr.str()
    assert "Rank earned: Lieutenant Commander" in err
    assert "SDC_Rank-Lieutenant_Commander-navy" in err


def test_unknown_class_and_test_fall_back_gracefully(pytester):
    result = _run(pytester, '''
class TestUnmapped:
    def test_unmapped(self): assert True
''')
    err = result.stderr.str()
    assert "Phase ?: Unknown" in err
    # unmapped test name shown raw
    assert "test_unmapped" in err
    assert result.ret == 0


# --- #47 intel fragments -------------------------------------------------

# mission "0" has exactly two intel fragments (phase nums 1 and 2), so a
# two-phase run either fully decrypts it or not — ideal for these tests.
INTEL0_CONFTEST = '''
from aria_reporter import configure
configure(
    phases={"TestCommsCheck": ("1", "Comms Check"), "TestDutyReport": ("2", "Report In")},
    friendly={"test_a": "A", "test_b": "B"},
    mission_id="0",
)
'''


def test_intel_decrypts_every_completed_phase(pytester):
    result = _run(pytester, '''
class TestCommsCheck:
    def test_a(self): assert True
class TestDutyReport:
    def test_b(self): assert True
''', conftest=INTEL0_CONFTEST)
    err = result.stderr.str()
    assert "DECRYPTED INTEL" in err
    assert "SDC listening post online" in err          # fragment [1]
    assert "clears you for intel access" in err         # fragment [2]
    # all fragments earned -> no "still encrypted" nag
    assert "still encrypted" not in err
    assert result.ret == 0


def test_intel_withholds_fragments_for_deficient_phases(pytester):
    result = _run(pytester, '''
class TestCommsCheck:
    def test_a(self): assert True
class TestDutyReport:
    def test_b(self): assert False, "ARIA: nope"
''', conftest=INTEL0_CONFTEST)
    err = result.stderr.str()
    # completed phase 1 decrypts; deficient phase 2 does not
    assert "SDC listening post online" in err
    assert "clears you for intel access" not in err
    assert "still encrypted" in err


def test_intel_fragments_render_in_phase_order(pytester):
    # declare the phase-2 class first; output must still list [1] before [2]
    result = _run(pytester, '''
class TestDutyReport:
    def test_b(self): assert True
class TestCommsCheck:
    def test_a(self): assert True
''', conftest=INTEL0_CONFTEST)
    err = result.stderr.str()
    assert err.index("SDC listening post online") < err.index("clears you for intel access")


def test_no_intel_block_for_mission_without_fragments(pytester):
    conftest = INTEL0_CONFTEST.replace('mission_id="0"', 'mission_id="2-1"')
    result = _run(pytester, '''
class TestCommsCheck:
    def test_a(self): assert True
class TestDutyReport:
    def test_b(self): assert True
''', conftest=conftest)
    err = result.stderr.str()
    assert "DECRYPTED INTEL" not in err
    assert result.ret == 0


def test_module1_arc_hands_off_to_gateway(pytester):
    # The 1-5 finale fragment must carry the exact hand-off the Gateway
    # briefing opens with: the 172.31.0.0/24 forward post + First Contact.
    conftest = '''
from aria_reporter import configure
configure(
    phases={
        "TestRoleStructure": ("1", "Role Structure"),
        "TestVault": ("2", "Vault"),
        "TestRoleApplied": ("3", "Role Deployment"),
        "TestIdempotency": ("4", "Idempotency"),
    },
    friendly={},
    mission_id="1-5",
)
'''
    result = _run(pytester, '''
class TestRoleStructure:
    def test_1(self): assert True
class TestVault:
    def test_2(self): assert True
class TestRoleApplied:
    def test_3(self): assert True
class TestIdempotency:
    def test_4(self): assert True
''', conftest=conftest)
    err = result.stderr.str()
    assert "172.31.0.0/24" in err
    assert "Operation First Contact" in err
    assert "forward observation post" in err
