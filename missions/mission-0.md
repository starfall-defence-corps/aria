## Mission Context: 0 — Reporting for Duty

The cadet's **first contact with ARIA** — the enrolment mission, before any real defensive work begins. There is nothing to attack yet: this mission exists purely to prove the cadet's machine and toolchain are mission-ready. The cadet must:

1. **Prove their equipment works** — `make doctor` (Docker, required tools, port 2221 free) all green, then `make setup` to boot a single node, `sdc-gate`.

2. **Establish comms** — raise the gatehouse with `ansible all -m ping` and get `SUCCESS` (proves SSH connectivity, authentication, and remote execution all work).

3. **File a duty report** — one ad-hoc command that writes `/home/cadet/duty-report.txt` **on the node** containing the phrase "reporting for duty". This is graded on the node, not in the repo.

The cadet **edits no workspace files**. The inventory (`workspace/inventory/hosts.yml`) and `workspace/ansible.cfg` are **issued equipment** — provided intact and explicitly marked "do not edit for this mission" (they build their own inventory in Mission 1.1). The graded artifact (the duty report) lives on `sdc-gate`, so in the CI PR review there are no student-authored files to critique.

**This mission runs with `skip-tests: true` in CI** — the deterministic tests need Docker and run locally via `make test`. ARIA's PR review here is therefore an LLM-only orientation, not a code audit.

## Review Focus Areas

Keep this review **warm, brief, and encouraging** — it is a recruit's first green banner, not a graded exercise. Do not invent deficiencies where there is nothing for the cadet to author.

For the **Submission Review** section:
- Confirm the issued inventory and `ansible.cfg` are present and unmodified (the local test verifies the inventory "is still in place"). If they are intact, say so plainly — that is the pass condition here.
- Acknowledge that the substantive proof of work (ping SUCCESS + duty report on the node) is verified locally by `make test`, not in this PR.

For the **Security Observations** section:
- Do **not** perform a hardening teardown — there is no cadet-authored configuration to harden yet. At most, note that `host_key_checking = False` and `UserKnownHostsFile=/dev/null` are deliberate lab conveniences for this training environment, and that later missions tighten SSH posture.

For the **Recommendations** section:
- Point forward, not back: welcome the cadet to the Corps, confirm their machine is cleared for the Foundation module, and direct them to **Mission 1.1 — Fleet Census**, where they build their first inventory from scratch. Encourage them to keep `make doctor` in their back pocket for any future environment issue.
