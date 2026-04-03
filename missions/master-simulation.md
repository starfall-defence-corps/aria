## Mission Context: Master Simulation — Operation: Iron Curtain

The Master Simulation is the **capstone assessment** for Module 2 (Advanced Training). The cadet must synthesise every skill from missions 2.1–2.4 — plus all Module 1 foundations — to replace General Snowflake's hand-built infrastructure with uniform, tested, automated CIS compliance across a 6-node fleet. This is a 3.5-hour timed assessment with no step-by-step guidance.

The Iron Curtain Fleet consists of 6 nodes: sdc-iron-web-1 (Ubuntu 22.04), sdc-iron-web-2 (Ubuntu 22.04), sdc-iron-db-1 (Rocky Linux 9), sdc-iron-db-2 (Rocky Linux 9), sdc-iron-app (Ubuntu 22.04), sdc-iron-comms (Ubuntu 22.04). All nodes ship with General Snowflake's misconfigurations: SSH root login enabled, password auth, weak MaxAuthTries/LoginGraceTime/ClientAliveInterval, /etc/shadow 0644, IP forwarding enabled, ICMP redirects accepted, no cron.allow/at.allow, core dumps unrestricted, no login banner, telnet/xinetd on Ubuntu, hardcoded credentials at /opt/fleet-db-creds.txt.

The assessment has four missions:

### Mission 1: Assessment (40 min)
- Write `inventory/hosts.yml` with `debian` and `redhat` groups for all 6 nodes
- Create `inventory/group_vars/debian.yml` and `inventory/group_vars/redhat.yml`
- Run Lynis baseline audits on all Ubuntu nodes
- Complete `ASSESSMENT.md` with fleet inventory, Lynis scores, CIS violations, remediation plan

### Mission 2: Remediation (75 min)
- Create `roles/iron_curtain/` CIS hardening role with minimum 8 tagged tasks
- Each CIS task must have a tag matching the control section (e.g., `cis_5_2`)
- Deploy with `serial` (rolling update — never all 6 at once)
- Create Molecule configuration and at least 8 Testinfra tests
- Encrypt sensitive variables with Vault (password: `iron-curtain`)
- Update `ASSESSMENT.md` with post-hardening Lynis scores showing improvement

### Mission 3: Automation (60 min)
- Write `.github/workflows/ci.yml` with lint → test stages, matrix for both OS families, `needs` keyword
- Write `.github/workflows/drift-detection.yml` with weekly cron schedule and failure notification
- Create `Makefile` with `lint`, `test`, `scan` targets
- Configure `.ansible-lint`
- Complete `PIPELINE.md` with pipeline documentation

### Mission 4: Incident (35 min)
- Run `make incident` to trigger a Voidborn compromise
- Detect which node was compromised (correct answer: `sdc-iron-web-2`)
- Document investigation timeline, specific changes found, and remediation in `INCIDENT.md`
- Remediate all unauthorised changes and verify compliance restored

## Review Focus Areas

For the **Submission Review** section, evaluate comprehensiveness across all four missions:

**Assessment (Mission 1)**:
- Does the inventory correctly define `debian` and `redhat` groups with all 6 nodes?
- Are group_vars populated with OS-specific service names and packages?
- Is `ASSESSMENT.md` filled in with real Lynis hardening index scores (not the template)?
- Are CIS violations documented per category with a remediation plan?

**Remediation (Mission 2)**:
- Does `roles/iron_curtain/` have proper structure (tasks, handlers, templates, defaults)?
- Are there at least 8 CIS tasks, each with a tag matching its control section?
- Does `site.yml` use `serial` for rolling deployment?
- Is `vault.yml` properly encrypted (not plaintext)?
- Do Molecule tests exist and cover the hardening controls?
- Does `ASSESSMENT.md` show Lynis improvement (before vs after scores)?

**Automation (Mission 3)**:
- Does the CI workflow have distinct lint and test stages with `needs` dependency?
- Is the test stage using a matrix strategy for both OS families?
- Does the drift detection workflow have a `schedule` trigger with a cron expression?
- Does the drift workflow create a GitHub issue on failure?
- Is the Makefile functional with `lint`, `test`, `scan` targets?
- Is `PIPELINE.md` filled in (not the empty template)?

**Incident (Mission 4)**:
- Is the correct compromised node identified (`sdc-iron-web-2`)?
- Does `INCIDENT.md` include a timeline of investigation steps?
- Are the specific unauthorised changes documented?
- Were remediation steps actually applied (not just described)?
- Do all nodes pass compliance checks after remediation?

For the **Security Observations** section, look for:
- **CRITICAL**: Any plaintext secrets (passwords, API keys, credentials) in committed files
- Whether `.vault-pass` is properly gitignored
- Whether hardcoded credentials at `/opt/fleet-db-creds.txt` are being removed
- Whether telnet/xinetd are removed (not just stopped)
- Whether the CI pipeline would actually catch regressions
- Whether drift detection would fire on real configuration changes

For the **Recommendations** section:
- This is the Module 2 capstone — be direct and thorough about what is missing or incomplete
- Note if any of the four missions is entirely skipped or only partially completed
- Comment on whether the CIS role is genuinely reusable or tightly coupled to this fleet
- Evaluate Molecule test quality — do tests assert real CIS controls or just check file existence?
- Assess the CI pipeline — would it catch a regression if someone broke SSH hardening?
- Note performance tier if timing information is available
- Emphasise whether the cadet has demonstrated mastery of Module 2 skills or has gaps
- A passing submission requires all four missions substantially complete — partial credit is not sufficient for the capstone
