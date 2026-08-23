"""
ARIA shared test reporter — SDC Academy
=======================================
A pytest plugin that renders a cadet-facing, phase-oriented summary of a
mission's verification run (``✓ / ✗ / ○`` per objective, grouped by phase,
with a "N of M phases complete" progress line).

It was previously copy-pasted verbatim into every mission's
``molecule/default/tests/conftest.py``; that duplication had already drifted
(older missions lacked the all-skip → exit-2 safeguard, one mission used
unicode escapes). This is the single canonical home. Missions opt in with::

    # molecule/default/tests/conftest.py
    from aria_reporter import configure
    configure(
        phases={"TestPhase1Triage": ("1", "Triage the Fleet"), ...},
        friendly={"test_triage_report_generated": "…", ...},
        mission_id="2-6",
    )

The plugin is INERT until ``configure()`` is called — with no configuration it
does not touch pytest's output or exit code, so installing it never disturbs
unrelated pytest runs (including this repo's own test suite).

Emission point for downstream gamification (#47 intel fragments, #48 rank/
badges, #50 tiers): the reporter already tracks per-phase pass/fail and
verified/deficient/skipped counts — those features render from ``summary()``.
"""
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Per-mission configuration (populated by configure())
# ---------------------------------------------------------------------------

_CONFIG = {
    "active": False,
    "phases": {},      # {ExactTestClassName: (num, label)}
    "friendly": {},    # {exact_test_func_name: human label}
    "mission_id": None,
    "unit": "Phase",   # segment noun: "Phase" for missions, "Mission" for capstones
}


def configure(phases=None, friendly=None, mission_id=None, unit="Phase"):
    """Activate the ARIA reporter for this mission's test session.

    phases    -- maps each test-class name to a ``(number, label)`` pair.
    friendly  -- maps each test-function name to a human-readable objective.
    mission_id-- e.g. "2-6" (stored for downstream rank/badge/intel features).
    unit      -- singular noun for a segment: "Phase" (default, used by the
                 numbered missions) or "Mission" (the gateway/master capstones,
                 which group work into "Mission 1/2/3"). The plural in the
                 progress line is derived as ``unit.lower() + "s"``.
    """
    _CONFIG["phases"] = dict(phases or {})
    _CONFIG["friendly"] = dict(friendly or {})
    _CONFIG["mission_id"] = mission_id
    _CONFIG["unit"] = unit or "Phase"
    _CONFIG["active"] = True
    _reporter.reset()


# ---------------------------------------------------------------------------
# Rank ladder + mission codenames (#48). Royal Navy officer track (sdc-academy
# #64) — never mixes officer and rating ranks. Full mission completion earns the
# rank the cadet holds at that milestone; the plugin emits a copy-paste
# shields.io badge block the cadet adds to their README.
# ---------------------------------------------------------------------------

RANK_BY_MISSION = {
    "0": "Midshipman",
    "1-1": "Sub-Lieutenant", "1-2": "Sub-Lieutenant", "1-3": "Sub-Lieutenant",
    "1-4": "Sub-Lieutenant", "1-5": "Sub-Lieutenant",
    "gateway": "Lieutenant",
    "2-1": "Lieutenant", "2-2": "Lieutenant", "2-3": "Lieutenant",
    "2-4": "Lieutenant", "2-5": "Lieutenant", "2-6": "Lieutenant",
    "master": "Lieutenant Commander",
}

# mission_id -> (badge label, codename)
CODENAME = {
    "0": ("Mission 0", "Reporting for Duty"),
    "1-1": ("Mission 1.1", "Fleet Census"),
    "1-2": ("Mission 1.2", "Lock the Door"),
    "1-3": ("Mission 1.3", "Clean Sweep"),
    "1-4": ("Mission 1.4", "Many Ships"),
    "1-5": ("Mission 1.5", "Clean House"),
    "gateway": ("Gateway", "First Contact"),
    "2-1": ("Mission 2.1", "Weapon Handling Test"),
    "2-2": ("Mission 2.2", "Compliance as Code"),
    "2-3": ("Mission 2.3", "Fleet Sync"),
    "2-4": ("Mission 2.4", "Defence in Depth"),
    "2-5": ("Mission 2.5", "Noise Storm"),
    "2-6": ("Mission 2.6", "Counterattack"),
    "master": ("Master Simulation", "Iron Curtain"),
}


def _shields_escape(text):
    """shields.io badge encoding: '-' -> '--', '_' -> '__', ' ' -> '_'."""
    return text.replace("-", "--").replace("_", "__").replace(" ", "_")


# ---------------------------------------------------------------------------
# Intel fragments (#47). Every phase a cadet *completes* (all its checks green)
# decrypts one short story fragment. Read in order across Module 1 (missions 0
# and 1-1..1-5), the fragments assemble the exact picture the Gateway
# Simulation opens with: a Voidborn-boarded forward observation post at
# 172.31.0.0/24. Deficient/partial phases decrypt nothing — a reason to finish
# every phase, not just enough to pass. Keyed {mission_id: {phase_num: text}}.
# Missions with no entry simply emit no intel (graceful).
# ---------------------------------------------------------------------------

INTEL = {
    # Prologue — the listening post comes online.
    "0": {
        "1": "SDC listening post online. Static clears — something is transmitting on a channel that should be dead.",
        "2": "The fragments carry one tag: VOIDBORN. Command opens a case file and clears you for intel access.",
    },
    # 1-1 Fleet Census — learning to see the enemy.
    "1-1": {
        "1": "First intercept decoded. The Voidborn keep a ledger of every ship they have boarded. An SDC frontier node is on it.",
        "2": "Traffic analysis: a raider cell is pinging our frontier, quietly mapping which nodes still answer.",
        "3": "Their probes gather facts before they strike — OS, open ports, users. The same reconnaissance you just ran.",
        "4": "A calling card surfaces in the wreckage: files left world-writable, chmod 777. The signature of Saboteur Chmod-777.",
        "5": "Filtered from the noise, one name sits atop every order the cell receives: Dread Admiral Snowflake.",
    },
    # 1-2 Lock the Door — how they get in.
    "1-2": {
        "1": "Captured Voidborn orders read like playbooks — numbered, repeatable, run against many ships in one pass.",
        "2": "They rehearse each boarding dry before committing a single trooper. This is discipline, not a rabble.",
        "3": "Breach method confirmed: Warlord Hardcoded-Password simply walks through doors left unlocked — open SSH, root login permitted.",
        "4": "Their foothold re-runs clean, leaving no second trace. Whatever we harden, we must harden so it stays hardened.",
    },
    # 1-3 Clean Sweep — the second column.
    "1-3": {
        "1": "Fresh orders intercepted. A second raider column is forming up behind the first.",
        "2": "Corsair Unpatched preys on what defenders forget — stale packages and dead services nobody bothered to remove.",
        "3": "Where firewalls sleep, the Voidborn pour through. Three frontier posts are reporting their firewalls down.",
        "4": "Decrypt: they hunt unhardened kernels, the soft underbelly of any node rushed into service unprepared.",
        "5": "Confirmed — their foothold self-repairs overnight. A one-time fix will not hold this line.",
    },
    # 1-4 Many Ships — they scale up.
    "1-4": {
        "1": "Scale intercept: the raiders have stopped striking one ship at a time. Now they take whole fleets in a single order.",
        "2": "Their orders adapt per target — Ubuntu here, Rocky there — one plan reshaped to fit many hulls.",
        "3": "Reaver YOLO-Deploy ships fast and mixed-OS on purpose, betting we cannot defend both fronts at once.",
        "4": "A frontier sector falls silent. Its last transmission: firewalls overwhelmed clear across the line.",
        "5": "The silent sector's configuration keeps drifting back open. Something re-breaks it every night.",
    },
    # 1-5 Clean House — the picture resolves, and hands off to Gateway.
    "1-5": {
        "1": "Marauder Copy-Paste's weakness is plain: their tactics are stolen and brittle. Ours will be roles — clean, reusable, ours.",
        "2": "The final decrypt needs a key. SDC cryptographers open the Vault, and the last of the picture resolves.",
        "3": "It assembles: a forward observation post — three nodes — already boarded. SSH wide open, secrets sitting on disk.",
        "4": "Coordinates locked: 172.31.0.0/24. The post is a liability and still bleeding. Command cuts a Gateway tasking — Operation First Contact.",
    },
}


def _intel_for(mission_id, completed_nums):
    """Return [(num, fragment)] for completed phases with intel, phase-ordered.

    completed_nums is the list of phase-number strings whose every check passed.
    Fragments for deficient or partial phases are intentionally withheld.
    """
    table = INTEL.get(mission_id)
    if not table:
        return []
    def _key(n):
        return (0, int(n)) if n.isdigit() else (1, n)
    out = []
    for num in sorted(set(completed_nums), key=_key):
        frag = table.get(num)
        if frag:
            out.append((num, frag))
    return out


def _badge_block(mission_id):
    """Return the markdown badge lines for a fully-completed mission, or None."""
    rank = RANK_BY_MISSION.get(mission_id)
    label, codename = CODENAME.get(mission_id, (None, None))
    if not rank or not label:
        return None
    rank_badge = (
        f"![SDC Rank](https://img.shields.io/badge/"
        f"SDC_Rank-{_shields_escape(rank)}-navy)"
    )
    mission_badge = (
        f"![{label}](https://img.shields.io/badge/"
        f"{_shields_escape(label)}-{_shields_escape(codename)}-brightgreen)"
    )
    return rank, f"{rank_badge} {mission_badge}"


def reward_for(mission_id):
    """Public: ``(rank, badge_markdown)`` for a mission, or ``None`` if unknown.

    Same data the make-test summary emits on full completion (#48). Exposed so
    the CI review (``aria-review.py``) can surface the rank/badge in the PR
    review from a single source of truth — no duplicated badge strings.
    """
    return _badge_block(mission_id)


# ---------------------------------------------------------------------------
# Colour (honours ARIA_COLOR=1, else auto-detects a tty)
# ---------------------------------------------------------------------------

def _color_enabled():
    return (
        os.environ.get("ARIA_COLOR") == "1"
        or (hasattr(sys.stderr, "isatty") and sys.stderr.isatty())
    )


def _c(code):
    return code if _color_enabled() else ""


def _palette():
    return {
        "GREEN": _c("\033[32m"), "RED": _c("\033[31m"),
        "YELLOW": _c("\033[33m"), "CYAN": _c("\033[36m"),
        "DIM": _c("\033[2m"), "BOLD": _c("\033[1m"), "RESET": _c("\033[0m"),
    }


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------

class _ARIAReporter:
    def __init__(self):
        self.reset()

    def reset(self):
        self._current_class = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self._phase_results = {}
        self._current_phase_passed = True

    @staticmethod
    def _out(text):
        sys.stderr.write(text)
        sys.stderr.flush()

    def record(self, nodeid, outcome, longrepr):
        p = _palette()
        parts = nodeid.split("::")
        cls = parts[1] if len(parts) > 1 else ""
        test = parts[-1]

        num, label = _CONFIG["phases"].get(cls, ("?", "Unknown"))
        name = _CONFIG["friendly"].get(test, test)

        if cls != self._current_class:
            if self._current_class is not None:
                self._phase_results[self._current_class] = self._current_phase_passed
            self._current_phase_passed = True
            self._current_class = cls
            self._out(f"\n  {p['CYAN']}{p['BOLD']}{_CONFIG['unit']} {num}: {label}{p['RESET']}\n")

        if outcome != "passed":
            self._current_phase_passed = False

        if outcome == "passed":
            self.passed += 1
            self._out(f"    {p['GREEN']}✓{p['RESET']} {name}\n")
        elif outcome == "skipped":
            self.skipped += 1
            self._out(f"    {p['YELLOW']}○{p['RESET']} {p['DIM']}{name} — skipped{p['RESET']}\n")
        else:
            self.failed += 1
            hint = _extract_hint(longrepr)
            if hint:
                self._out(f"    {p['YELLOW']}✗{p['RESET']} {name}\n")
                self._out(f"      {p['DIM']}↳ {hint}{p['RESET']}\n")
            else:
                self._out(f"    {p['RED']}✗{p['RESET']} {name}\n")

    def summary(self):
        p = _palette()
        if self._current_class is not None:
            self._phase_results[self._current_class] = self._current_phase_passed

        total = self.passed + self.failed + self.skipped
        self._out(f"\n  {'─' * 44}\n")

        phases_complete = sum(1 for v in self._phase_results.values() if v)
        total_phases = len(_CONFIG["phases"])
        plural = _CONFIG["unit"].lower() + "s"
        self._out(f"  {p['BOLD']}Progress:{p['RESET']} {phases_complete} of {total_phases} {plural} complete\n")

        segs = []
        if self.passed:
            segs.append(f"{p['GREEN']}{self.passed} verified{p['RESET']}")
        if self.failed:
            segs.append(f"{p['RED']}{self.failed} deficient{p['RESET']}")
        if self.skipped:
            segs.append(f"{p['YELLOW']}{self.skipped} skipped{p['RESET']}")
        self._out(
            f"  {p['BOLD']}Results:{p['RESET']} {' · '.join(segs)}"
            f"  {p['DIM']}({total} checks){p['RESET']}\n"
        )

        # #47 — decrypt one intel fragment per fully-completed phase, in phase
        # order. Partial/deficient phases decrypt nothing (a reason to finish
        # every phase). Missions without an INTEL entry emit no block.
        completed_nums = [
            _CONFIG["phases"].get(cls, ("?", ""))[0]
            for cls, passed in self._phase_results.items()
            if passed
        ]
        fragments = _intel_for(_CONFIG.get("mission_id"), completed_nums)
        if fragments:
            self._out(f"\n  {p['CYAN']}{p['BOLD']}📡 DECRYPTED INTEL{p['RESET']}\n")
            for num, frag in fragments:
                self._out(f"    {p['DIM']}[{num}]{p['RESET']} {frag}\n")
            total_intel = len(INTEL.get(_CONFIG.get("mission_id"), {}))
            if len(fragments) < total_intel:
                locked = total_intel - len(fragments)
                self._out(
                    f"    {p['DIM']}…{locked} fragment(s) still encrypted — "
                    f"clear every phase to decrypt them.{p['RESET']}\n"
                )

        # #48 — rank + shareable badges, only on a fully-completed mission
        # (every phase green, nothing deficient). Incomplete runs are unchanged.
        complete = (
            self.failed == 0 and total_phases > 0 and phases_complete == total_phases
        )
        if complete:
            block = _badge_block(_CONFIG.get("mission_id"))
            if block:
                rank, badges = block
                self._out(f"\n  {p['CYAN']}{p['BOLD']}🎖  Rank earned: {rank}{p['RESET']}\n")
                self._out(f"  {p['DIM']}Add your badges to your README:{p['RESET']}\n")
                self._out(f"  {badges}\n")


def _extract_hint(longrepr):
    """Pull an ``assert cond, 'ARIA: <hint>'`` message out of a failure."""
    if longrepr is None:
        return None
    crash = getattr(longrepr, "reprcrash", None)
    if crash:
        msg = getattr(crash, "message", "")
        if "ARIA:" in msg:
            return msg.split("ARIA:", 1)[-1].strip()
    text = str(longrepr)
    if "ARIA:" in text:
        raw = text.split("ARIA:")[-1].splitlines()[0].strip()
        return raw.rstrip("'\"")
    return None


_reporter = _ARIAReporter()


# ---------------------------------------------------------------------------
# pytest hooks — all no-op unless configure() has been called
# ---------------------------------------------------------------------------

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    if not _CONFIG["active"]:
        return
    if report.when == "call":
        _reporter.record(report.nodeid, report.outcome, report.longrepr)
        report.longrepr = None
    elif report.when == "setup" and report.skipped:
        _reporter.record(report.nodeid, "skipped", report.longrepr)
        report.longrepr = None


def pytest_report_teststatus(report, config):
    if not _CONFIG["active"]:
        return None
    if report.when == "call":
        return report.outcome, "", ""
    if report.when == "setup" and report.skipped:
        return "skipped", "", ""


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _CONFIG["active"]:
        return
    _reporter.summary()
    terminalreporter.stats.pop("failed", None)
    terminalreporter.stats.pop("error", None)


def pytest_sessionfinish(session, exitstatus):
    # An all-skipped run (range unarmed / already clean) is INCONCLUSIVE, not a
    # pass — force a non-zero exit so `make test` never reports COMPLETE for it.
    # (Canonicalised from mission-2-6; older missions lacked this safeguard.)
    if not _CONFIG["active"]:
        return
    if _reporter.passed == 0 and _reporter.failed == 0 and _reporter.skipped > 0:
        session.exitstatus = 2
