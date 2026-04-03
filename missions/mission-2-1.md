## Mission Context: 2.1 — Weapon Handling Test (Molecule Deep Dive)

The cadet's first Module 2 mission. Villain: Private YOLO-Deploy. This mission is fundamentally different from Module 1 — instead of writing Ansible roles to pass pre-written tests, students learn to write tests themselves using Molecule and Testinfra.

The mission has three parts:

### WHT Range — Obstacle Course (Timed)

**Mission 1: Write the Role**
- 5 Testinfra tests are provided at `obstacle-course/mission-1/tests/test_ssh_hardening.py`
- Tests check: SSH root login disabled, SSH password auth disabled, SSH service running, telnet removed, ufw active
- Student creates `roles/ssh_hardening/` with tasks that satisfy all 5 tests
- Target: wht-ssh (Ubuntu, port 2241)

**Mission 2: Write the Tests**
- A `web_server` role is provided that installs/configures nginx
- Role has planted bugs: `server_tokens on` (info leak) and `autoindex on` on /data path
- Student writes `tests/test_web_server.py` with tests that catch the bugs
- Some tests should pass (basic checks), some should fail (catching bugs)
- Target: wht-web (Ubuntu, port 2242)

### Main Mission: Test Everything
- Student writes a complete Molecule test scenario for their fleet_hardening role from 1.5
- Creates molecule.yml, tests, inventory, and site.yml
- Tests must cover SSH, firewall, MOTD, services — at least 8 test functions
- Fleet: sdc-web (Ubuntu, 2221), sdc-db (Rocky, 2222), sdc-comms (Ubuntu, 2223)

## Review Focus Areas

For the **Submission Review** section, evaluate:
- **Obstacle Course 1**: Does the role satisfy all 5 tests? Is the implementation clean?
- **Obstacle Course 2**: Are tests meaningful? Do they use appropriate Testinfra helpers (host.package, host.service, host.file, host.socket)? Do they catch the planted bugs?
- **Main Mission**: Is the molecule.yml properly configured? Do tests cover all major hardening areas? Are tests specific and descriptive?

For the **Security Observations** section, look for:
- Tests that verify security properties (not just "service is running" but "root login is disabled")
- Whether students test for the absence of insecure configurations (not just presence of secure ones)
- Quality of assertions — specific string matching vs. just "file exists"

For the **Recommendations** section:
- Suggest parametrizing tests for multi-OS coverage
- Mention test naming conventions and docstrings
- Suggest testing edge cases (what happens if the role is run twice?)
- Note if test coverage has gaps (e.g., missing sysctl checks, permission checks)
