## Mission Context: 2.6 — Counterattack (Incident Response on a Live, Scored Fleet)

Lieutenant rank mission (Module 2 finale). Adversary: **The Operator** — a
persistence-focused intruder who used mission 2.5's noise storm as cover to
plant four identical implants on every fleet node. Purely defensive incident
response: triage (read-only evidence gathering) then eradication, performed
against a live `sdc-web` service that is scored on availability throughout.

The four implants, planted on `sdc-app` / `sdc-web` / `sdc-db` (172.30.0.11–13):
1. A malicious cron job (`/etc/cron.d/starfall-sync`) running `/usr/local/bin/.sync-agent`
2. A rogue systemd beacon (`starfall-beacon.service` + `.timer`) with an nginx dependency drop-in so it starts with the web service
3. An extra key in root's `authorized_keys` tagged `attacker@starfall-shadow`
4. A backdoor account `svc-telemetry` with passwordless sudo via `/etc/sudoers.d/`

Root's password is also treated as leaked and must be rotated. The Operator's
C2 sits at `172.30.0.20` (block it; never touch it). The web service must never
drop below **quorum** (≥2 of 3 nodes answering) during remediation — sequencing
the restart safely is the real skill under test. Only two student files:
`workspace/triage.yml` and `workspace/eradicate.yml`.

Five sequential phases:

### Phase 1: Triage the Fleet (read-only)
- Catalogue all four implants on every node into a verifiable structured report
- Every probe task must leave `changed: 0` — evidence gathering, not alteration
- Report includes a live, per-host secret readable only from a still-compromised node

### Phase 2: Purge the Implants
- Remove the cron job and the rogue beacon (unit, timer, payload, nginx drop-in); silence the C2 callbacks

### Phase 3: Accounts, Keys & Creds
- Delete the `svc-telemetry` backdoor account, pull the attacker's root key, rotate root's password

### Phase 4: Block the C2
- Firewall-drop all egress to `172.30.0.20`, fleet-wide

### Phase 5: Clean & Services Up (capstone)
- Restart the web service to apply cleaned config without ever dropping below quorum

`make test` regenerates the triage report fresh and runs `eradicate.yml` once
against an armed, monitored segment; because eradication is graded on live
availability, a clean scored run needs `make reset` first. An all-skipped result
means the fleet is already clean (nothing to eradicate), not a failure.

## Review Focus Areas

For the **Submission Review** section, evaluate:
- **Read-only triage**: Does `triage.yml` gather evidence without mutating the hosts? Any task that could report `changed` on a probe is a defect — it contaminates evidence and may tip off the Operator.
- **Completeness on every node**: Are all four implants handled on all three nodes? A fleet with two nodes clean and one compromised is not clean — no partial credit.
- **Quorum discipline**: Does `eradicate.yml` sequence the nginx restart (serial / rolling) so ≥2 nodes always answer? A naive fleet-wide `restart` is the classic failure.

For the **Security Observations** section, look for:
- Whether *every* facet of each implant is removed (e.g. the beacon's unit, timer, payload binary, AND the nginx dependency drop-in — missing the drop-in leaves nginx dirty)
- Whether root's password is genuinely rotated, not just left behind other defences
- Whether the backdoor sudoers drop-in is removed along with the account
- Whether egress to the C2 is blocked, not just inbound

For the **Recommendations** section:
- Reinforce the 2.3 rolling-update discipline: `serial:` + health-gated restarts keep the scored service up
- Suggest `changed_when: false` on triage probes to guarantee read-only behaviour
- Note that eradication should be idempotent — a second run should find nothing and stay green/skip
- Encourage verifying the C2 has gone silent (no callbacks) as the true success signal, not merely that files were deleted
