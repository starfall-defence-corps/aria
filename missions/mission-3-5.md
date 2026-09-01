## Mission Context: MOS 5 — Battle Rattle (Incident Response Automation)

The reusable-runbook Module 3 (Specialization) mission. Blue teams lose exercises because their incident response is bespoke and one-off — a script written for yesterday's indicator is useless against today's. The cadet builds FOUR **parameterised** IR runbooks, canonically at `workspace/runbooks/<verb>.yml`, and each is graded **behaviourally and for reusability**: ARIA runs the SAME runbook against TWO independent, randomised scenarios (indicators/users/services the cadet cannot see) in one lab pass. A runbook hardcoded to one scenario passes it and FAILS the other. Purely defensive (the cadet responds to an incident on their own fleet). Villain: **The Hydra** — sever one indicator and it regrows under a new one; only automation that works for ANY indicator holds the line.

Lab: 3 fleet nodes (`sdc-web`, `sdc-db`, `sdc-comms`) + an opaque range/injector (`sdc-range`) that sources traffic from the mission's nonce indicator IPs. The four runbooks (the cadet's "battle rattle"):

1. **`block-ioc.yml`** (`-e ioc_ip=<ip>`) — firewall-DROP all traffic from a given indicator, fleet-wide, idempotently, without blocking legitimate sources. Graded by sourcing traffic from the range: after the block the indicator cannot reach any node, a legitimate source still can, and SSH still answers.
2. **`collect-triage.yml`** (`-e evidence_log=<path> -e report_path=<path>`) — READ-ONLY recon: find the top `src=<ip>` in the evidence log and write, on each node, `{"indicator_ip": "...", "hits": <count on this node>}` at report_path. Graded on discovering the real indicator + the correct per-node count, deterministically, while changing nothing else (a read-only canary).
3. **`rotate-creds.yml`** (`-e target_user=<user> -e new_password=<secret>`) — rotate a compromised local credential fleet-wide, leaving the account usable. Graded by verifying (on the node) that the old password is rejected and the new one works, the account is not locked, and the stored hash is IDENTICAL on a re-run (a stable salt — idempotent rotation, no credential churn).
4. **`restore-service.yml`** (`-e service_name=<svc> -e golden_root=<dir>`) — declaratively reconcile a downed systemd service from the known-good unit at `{{ golden_root }}/{{ service_name }}.service`, reload systemd only when the unit changed, then enable+start. ARIA breaks two services two ways (one corrupted unit, one deleted) — a bare `systemctl restart` fixes neither. Graded on active + enabled + serving the correct known-good content, idempotently.

Grading (deterministic pytest, all-nodes, no partial credit, dead lab → INCONCLUSIVE never a pass): the single `dual_nonce` primitive runs each runbook against both scenarios, asserts the effect on every node via implementation-independent probes, checks liveness (the box still works), and checks idempotence (a second identical run changes nothing). Completing MOS 5 is one of the 2+ MOS specialisations that earn the rank of **Commander**.

### Review Focus Areas

For the **Submission Review** section, evaluate:
- Is every runbook **parameterised** on its `-e` variables (`ioc_ip`, `target_user`/`new_password`, `service_name`/`golden_root`, `evidence_log`/`report_path`) with NO hardcoded indicator, address, username, or service name?
- Does each target the whole `fleet` group (all-nodes), not a single host?
- **Idempotence**: iptables/`user`/`copy`+`systemd` used so a re-run is a no-op; a stable salt for the credential hash (not a fresh random salt each run); systemd reloaded only when the unit changed.
- Is `collect-triage` genuinely **read-only** (no `become`, no mutation) and does it emit valid JSON per node?

For the **Security Observations** section, look for:
- Blanket firewall changes (a `-P INPUT DROP` or dropping more than the one indicator) that would black-hole legitimate traffic.
- Credential rotation that **locks** the account instead of rotating it, or leaves the old password valid.
- A `restore-service` that improvises a listener or bare-restarts instead of reconciling from the known-good store — it will not survive the corrupted/deleted-unit cases.
- Any hardcoded indicators, addresses, or plaintext secrets committed into the runbooks.

For the **Recommendations** section, consider suggesting:
- Treat every runbook as reusable kit: drive it entirely from `-e` variables so it works for ANY future incident, not the one in front of you.
- Make responses safe to re-run mid-incident (idempotent) — a runbook you cannot run twice is a liability under pressure.
- Reconcile to declared known-good state rather than issuing imperative fixes; recon should observe, never alter.
