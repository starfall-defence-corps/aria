## Mission Context: 2.2 — Compliance as Code (CIS Benchmarks)

The cadet's second Module 2 mission. Villain: Captain Unpatched. Students learn to implement CIS Level 1 benchmark controls as Ansible tasks, use tags for selective enforcement, and measure compliance with Lynis.

The mission has three parts:

### Compliance Range — Obstacle Course (Timed)

**Mission 1: Write the Role**
- 8 Testinfra tests are provided at `obstacle-course/mission-1/tests/test_cis_hardening.py`
- Tests check CIS controls: SSH MaxAuthTries, LoginGraceTime, ClientAlive settings, shadow permissions, core dump restriction, sysctl hardening, login banner, cron.allow
- Student creates `roles/cis_hardening/` with tagged tasks that satisfy all 8 tests
- Target: cis-target (Ubuntu, port 2251)

**Mission 2: Write the Tests**
- A `compliance_baseline` role is provided that claims to implement CIS controls
- Role has bugs: MaxAuthTries set to 5 (should be 4), shadow permissions 0644 (should be 0640), missing accept_redirects sysctl, no core dump restriction
- Student writes `tests/test_compliance_baseline.py` with tests that catch the gaps
- Some tests should pass (basic checks), some should fail (catching bugs)
- Target: cis-target (Ubuntu, port 2251)

### Main Mission: Compliance as Code
- Student extends fleet_hardening role from 1.5 with CIS Level 1 controls
- All tasks must be tagged with CIS section IDs
- Student runs Lynis scans before and after, records delta in COMPLIANCE.md
- Tests must cover at least 10 CIS/hardening checks
- Fleet: sdc-web (Ubuntu, 2221), sdc-db (Rocky, 2222), sdc-comms (Ubuntu, 2223)

## Review Focus Areas

For the **Submission Review** section, evaluate:
- **Obstacle Course 1**: Does the role satisfy all 8 CIS tests? Are tasks properly tagged? Is the implementation clean?
- **Obstacle Course 2**: Are tests meaningful? Do they verify CIS-specific values (not just "file exists")? Do they catch the planted bugs?
- **Main Mission**: Are all tasks tagged? Does COMPLIANCE.md show meaningful Lynis improvement? Do tests cover the required CIS controls?

For the **Security Observations** section, look for:
- Whether students verify specific CIS values (MaxAuthTries 4, not just "MaxAuthTries exists")
- Whether tags follow a consistent naming convention
- Whether the Lynis delta shows genuine improvement (not fabricated numbers)
- Whether tests check both OS families where applicable

For the **Recommendations** section:
- Suggest CIS Level 2 controls for further hardening
- Mention OpenSCAP as the enterprise-grade equivalent of Lynis
- Note if tag structure could be improved (e.g., hierarchical tags)
- Suggest testing selective enforcement: `ansible-playbook --tags cis_5_2`
