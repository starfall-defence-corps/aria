## Mission Context: MOS 4 — Eyes Everywhere (Detection & Monitoring)

The first Module 3 (Specialization) mission. Blue teams lose exercises for lack of **visibility**, not lack of hardening. The cadet builds ONE Ansible role (`telemetry`) that deploys observability across the whole fleet, and it is graded **behaviourally**: telemetry events must **actually arrive at a central collector** — a config that looks correct but delivers nothing is deficient. Purely defensive (the cadet deploys their own telemetry). Villain: **The Phantom Logstash**, who relocates the SIEM mid-mission to blind a fleet that hardcoded the collector's address.

Lab: 3 fleet nodes (`sdc-web`, `sdc-db`, `sdc-comms`) + a central collector (`sdc-collector`). The role deploys three telemetry streams:

1. **journald → rsyslog → collector** — a forward rule shipping `*.*` over TCP to the collector **by name** (`{{ collector_host }}`, not an IP), with an rsyslog **restart** so it takes effect.
2. **auditd (deploy + userspace shim)** — kernel audit is unreliable in containers, so the role deploys `/etc/audit/rules.d/sdc.rules` (key `sdc_identity`) **and** a userspace `sdc-audit-shim` that emits an audit-class event through the same journald→rsyslog pipe. The audit signal is graded at the collector, never via flaky kernel audit.
3. **osquery-style agent** — the lab provides `fleetquery` (a scheduled-query agent); the cadet deploys it, templates its config, and enables its timer. It reports the node's telemetry-id and watches a probe directory.

Grading (behavioural, all-nodes, no partial credit): ARIA generates a fresh-nonce event on every node for each channel (`logger -t sdc_eyes`, `sdc-audit-shim`, a probe file) and polls the collector to confirm arrival. The capstone relocates the collector; a name-based config re-onboards automatically, a hardcoded-IP config goes blind.

### Review Focus Areas

For the **Submission Review** section, evaluate:
- Is the rsyslog forward rule actually **applied** (a restart handler notified), not just written to disk?
- Is the collector referenced by the **variable/name** `collector_host`, never a hardcoded IP?
- Is the fleetquery agent **enabled and started** on every node (a timer that isn't enabled delivers nothing)?
- **All-node coverage** — no node left dark — and role **idempotence** (handlers for restarts; no forced changes each run).

For the **Security Observations** section, look for:
- Audit rules under `/etc/audit/rules.d/` (with `augenrules`), not appended to a monolithic `audit.rules`.
- The agent's node-identity (`node_nonce`) reported intact — telemetry you can't attribute to a host is half-blind.
- Any hardcoded collector addresses or credentials committed into the role.

For the **Recommendations** section, consider suggesting:
- Reference services by **name**, not number — telemetry must survive the SIEM relocating.
- Durable/queued forwarding (TCP + an action queue) so bursts aren't dropped.
- Treating *arrival at the collector* — not file presence on the node — as the success signal.
