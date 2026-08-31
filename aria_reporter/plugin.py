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
    "1-4": "Sub-Lieutenant", "1-5": "Sub-Lieutenant", "1-6": "Sub-Lieutenant",
    "gateway": "Lieutenant",
    "2-1": "Lieutenant", "2-2": "Lieutenant", "2-3": "Lieutenant",
    "2-4": "Lieutenant", "2-5": "Lieutenant", "2-6": "Lieutenant",
    "master": "Lieutenant Commander",
    # Module 3 (MOS specialisations): held at Lieutenant Commander; 2+ MOS earns Commander.
    "3-4": "Lieutenant Commander",
}

# mission_id -> (badge label, codename)
CODENAME = {
    "0": ("Mission 0", "Reporting for Duty"),
    "1-1": ("Mission 1.1", "Fleet Census"),
    "1-2": ("Mission 1.2", "Lock the Door"),
    "1-3": ("Mission 1.3", "Clean Sweep"),
    "1-4": ("Mission 1.4", "Many Ships"),
    "1-5": ("Mission 1.5", "Clean House"),
    "1-6": ("Mission 1.6", "Inventory from Nothing"),
    "gateway": ("Gateway", "First Contact"),
    "2-1": ("Mission 2.1", "Weapon Handling Test"),
    "2-2": ("Mission 2.2", "Compliance as Code"),
    "2-3": ("Mission 2.3", "Fleet Sync"),
    "2-4": ("Mission 2.4", "Defence in Depth"),
    "2-5": ("Mission 2.5", "Noise Storm"),
    "2-6": ("Mission 2.6", "Counterattack"),
    "3-4": ("MOS 4", "Eyes Everywhere"),
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
    # 1-6 Inventory from Nothing — the last Foundation skill before Gateway.
    "1-6": {
        "1": "Before the tasking can launch, a complication: the boarded post's addressing will not hold still. A ghost is moving it. Command names her Nyx, the Signal Ghost.",
        "2": "Nyx rotates a node's address faster than any static map can follow. Lesson from the frontier — fingerprint the service, never trust the number.",
        "3": "Every fleet you will ever be handed begins the way this one has: alive, unlabelled, buried in the noise of its own subnet. No inventory — just a range.",
        "4": "You raise the whole map from a single line — 172.30.0.0/24 — and hold it while Nyx moves the fleet beneath you. The map survives the rotation.",
        "5": "Cartography confirmed. You can walk into any range cold and chart it from nothing. Cleared to deploy: Gateway — Operation First Contact, at 172.31.0.0/24.",
    },
    # 3-4 MOS 4 Eyes Everywhere — the Detection & Monitoring specialisation.
    "3-4": {
        "1": "First MOS-4 intercept: a raider cell learned we win or lose by what we can see. They mean to blind us before they board.",
        "2": "Their operator surfaces in the logs that survive — The Phantom Logstash. It doesn't break in; it breaks your pipeline, then walks in unwatched.",
        "3": "Decrypt: the Phantom's tell is a fleet that looks instrumented but delivers nothing — agents installed, forwarders never restarted. Config without delivery is blindness with paperwork.",
        "4": "Coverage is the whole game. One dark node is the door. The Phantom hunts the single host your rollout skipped.",
        "5": "Confirmed doctrine: name your collector, never number it. The Phantom's favourite trick is moving the SIEM and watching hardcoded fleets go quiet. Yours stayed lit. Eyes everywhere.",
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
# Capstone performance tiers (#50). The Gateway and Master briefings define a
# time-based rating ("drill the skill until it bends to your will" — speed is
# mastery). Each entry is an ascending list of (upper_bound_minutes_exclusive,
# rating); the first bucket whose bound the elapsed time is under wins. The
# final bucket uses a sentinel bound (None) as the catch-all "retry" band.
#
# Wall-clock comes from the ARIA_ELAPSED_MIN env var, which `make test` sets
# from a start stamp written by `make setup` — a real, honest timer, not the
# honour-system CHECKLIST clock. If the var is absent the reference table is
# printed instead so the cadet can self-assess.
# ---------------------------------------------------------------------------

TIERS = {
    "gateway": [
        (45, "Ace Cadet"), (55, "Distinguished"), (65, "Qualified"),
        (75, "Passed"), (None, "RTB — retry"),
    ],
    "master": [
        (150, "Outstanding"), (180, "Excellent"), (210, "Qualified"),
        (240, "Passed"), (None, "Return to AIT — retry"),
    ],
}


def _tier_for(mission_id, elapsed_min):
    """Rating for a completion time, or None if the mission has no tiers."""
    table = TIERS.get(mission_id)
    if table is None or elapsed_min is None:
        return None
    for bound, rating in table:
        if bound is None or elapsed_min < bound:
            return rating
    return table[-1][1]


def _tier_table(mission_id):
    """One-line reference of a mission's tier bands, or "" if none."""
    table = TIERS.get(mission_id)
    if not table:
        return ""
    parts, prev = [], 0
    for bound, rating in table:
        if bound is None:
            parts.append(f"{rating} {prev}+")
        else:
            parts.append(f"{rating} <{bound}")
            prev = bound
    return "  ·  ".join(parts)


def _elapsed_min_from_env():
    """Parse ARIA_ELAPSED_MIN (whole minutes) from the environment, or None."""
    raw = os.environ.get("ARIA_ELAPSED_MIN", "").strip()
    if not raw:
        return None
    try:
        val = int(raw)
    except ValueError:
        return None
    return val if val >= 0 else None


# ---------------------------------------------------------------------------
# Exercise scoring engine (#56). A host-side poller (scripts/score-poller.sh,
# started by `make setup` on the capstones) TCP-probes each scored node's
# published SSH port every few seconds and appends a JSONL availability log:
#
#     {"t": 1690000000, "up": {"sdc-fwd-web": 1, "sdc-fwd-db": 1, ...}}
#
# At `make test`, the log path is handed to the plugin via ARIA_SCORE_LOG. This
# mirrors a real cyber-exercise scoring engine: service availability over the
# whole run is measured, not just a point-in-time check. The composite exercise
# score blends that availability with objective completion (phases green), so a
# fast run that dropped the scored service scores worse than a steady one.
# ---------------------------------------------------------------------------

# Composite score (0–100) -> rating band. First band whose floor is met wins.
SCORE_BANDS = [
    (95, "Flawless"), (85, "Distinguished"), (70, "Qualified"),
    (50, "Passed"), (0, "Insufficient"),
]

# Composite weighting: availability vs objective completion.
_AVAIL_WEIGHT = 0.5
_OBJECTIVE_WEIGHT = 0.5


def _load_score_samples(log_path):
    """Parse the JSONL availability log into a list of ``up`` dicts (per node
    1/0). Malformed or blank lines are skipped; a missing file yields []."""
    import json
    samples = []
    try:
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                up = rec.get("up")
                if isinstance(up, dict) and up:
                    samples.append({k: (1 if v else 0) for k, v in up.items()})
    except (OSError, IOError):
        return []
    return samples


def _availability(samples):
    """Return (overall_pct, per_node_pct, longest_outage) for the run.

    overall_pct is the mean of every (node, sample) reachability check.
    longest_outage is the largest run of consecutive samples in which *any*
    scored node was down (a proxy for the worst service dip)."""
    if not samples:
        return None, {}, 0
    nodes = sorted({n for s in samples for n in s})
    per_node = {}
    for n in nodes:
        seen = [s[n] for s in samples if n in s]
        per_node[n] = round(100.0 * sum(seen) / len(seen), 1) if seen else 0.0

    total_checks = sum(len(s) for s in samples)
    total_up = sum(v for s in samples for v in s.values())
    overall = round(100.0 * total_up / total_checks, 1) if total_checks else None

    longest = cur = 0
    for s in samples:
        if any(v == 0 for v in s.values()):
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    return overall, per_node, longest


def _rate_score(score):
    """Map a composite 0–100 score to its rating band."""
    for floor, label in SCORE_BANDS:
        if score >= floor:
            return label
    return SCORE_BANDS[-1][1]


def score_summary(log_path, objective_ratio=None):
    """Public: compute the exercise score from an availability log.

    Returns a dict {availability, per_node, longest_outage, objective_pct,
    composite, rating, samples} or None if the log has no usable samples.
    ``objective_ratio`` is phases_complete / total_phases (0..1)."""
    samples = _load_score_samples(log_path)
    if not samples:
        return None
    overall, per_node, longest = _availability(samples)
    if overall is None:
        return None
    obj_pct = None if objective_ratio is None else round(100.0 * objective_ratio, 1)
    if obj_pct is None:
        composite = round(overall)
    else:
        composite = round(_AVAIL_WEIGHT * overall + _OBJECTIVE_WEIGHT * obj_pct)
    composite = max(0, min(100, composite))
    return {
        "availability": overall,
        "per_node": per_node,
        "longest_outage": longest,
        "objective_pct": obj_pct,
        "composite": composite,
        "rating": _rate_score(composite),
        "samples": len(samples),
    }


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

            # #50 — capstone performance tier (only for missions with a TIERS
            # table). Real wall-clock from ARIA_ELAPSED_MIN when make test set
            # it; otherwise the reference table for honour-system self-scoring.
            mid = _CONFIG.get("mission_id")
            if mid in TIERS:
                elapsed = _elapsed_min_from_env()
                if elapsed is not None:
                    rating = _tier_for(mid, elapsed)
                    self._out(
                        f"\n  {p['YELLOW']}{p['BOLD']}⏱  Time: {elapsed} min"
                        f"  →  Performance tier: {rating}{p['RESET']}\n"
                    )
                    self._out(f"  {p['DIM']}{_tier_table(mid)}{p['RESET']}\n")
                else:
                    self._out(
                        f"\n  {p['YELLOW']}{p['BOLD']}⏱  Performance tiers"
                        f"{p['RESET']} {p['DIM']}(run `make setup` to start the "
                        f"clock){p['RESET']}\n"
                    )
                    self._out(f"  {p['DIM']}{_tier_table(mid)}{p['RESET']}\n")

        # #56 — exercise score from the availability poller. Shown for capstones
        # whenever ARIA_SCORE_LOG points at a log with samples — live, on every
        # run, not just at completion (the score IS the during-the-run metric).
        mid = _CONFIG.get("mission_id")
        score_log = os.environ.get("ARIA_SCORE_LOG", "").strip()
        if mid in TIERS and score_log:
            obj_ratio = (phases_complete / total_phases) if total_phases else None
            score = score_summary(score_log, obj_ratio)
            if score:
                self._out(
                    f"\n  {p['CYAN']}{p['BOLD']}📊  Exercise score: "
                    f"{score['composite']}/100 — {score['rating']}{p['RESET']}\n"
                )
                detail = (
                    f"service availability {score['availability']}%  ·  "
                    f"objectives {phases_complete}/{total_phases}  ·  "
                    f"{score['samples']} polls"
                )
                if score["longest_outage"]:
                    detail += f"  ·  longest dip {score['longest_outage']} polls"
                self._out(f"  {p['DIM']}{detail}{p['RESET']}\n")
                worst = [n for n, pct in score["per_node"].items() if pct < 100.0]
                if worst:
                    downs = ", ".join(
                        f"{n} {score['per_node'][n]}%" for n in sorted(worst)
                    )
                    self._out(f"  {p['DIM']}nodes with downtime: {downs}{p['RESET']}\n")


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
