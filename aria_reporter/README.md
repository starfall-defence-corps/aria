# aria-reporter

Shared **ARIA** test reporter for [SDC Academy](https://github.com/starfall-defence-corps/sdc-academy)
missions. A pytest plugin that renders a cadet-facing, phase-grouped summary of a
mission's verification run instead of raw pytest output.

Previously this reporter was copy-pasted into every mission's
`molecule/default/tests/conftest.py`. This package is the single canonical
source (issue [aria#9](https://github.com/starfall-defence-corps/aria/issues/9)).

## Install

Add to a mission's `requirements.txt`:

```
aria-reporter @ git+https://github.com/starfall-defence-corps/aria@main
```

(The `aria` repo is public, so no auth/token is needed locally or in CI.)

## Use

In `molecule/default/tests/conftest.py`:

```python
from aria_reporter import configure

configure(
    phases={
        "TestPhase1Triage": ("1", "Triage the Fleet"),
        "TestPhase2PurgeImplants": ("2", "Purge the Implants"),
    },
    friendly={
        "test_triage_report_generated": "Triage report generated from your playbook",
        "test_cron_purged": "Malicious cron + payload removed fleet-wide",
    },
    mission_id="2-6",
)
```

- `phases` — maps each **test-class** name to `(number, label)`.
- `friendly` — maps each **test-function** name to a human-readable objective.
- `mission_id` — e.g. `"2-6"` (used by rank/badge/intel features).

Tests should carry hints via `assert cond, "ARIA: <hint>"`; the hint is surfaced
under a failed objective.

## Behaviour

- **Inert until `configure()` is called** — installing the plugin never disturbs
  unrelated pytest runs.
- Writes the summary to **stderr**; honours `ARIA_COLOR=1` (else auto-detects a tty).
- An **all-skipped** session (range unarmed / already clean) forces a non-zero
  exit so `make test` never reports COMPLETE for an inconclusive run.
