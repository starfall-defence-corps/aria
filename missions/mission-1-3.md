## Mission Context: 1.3 — Clean Sweep

The cadet's third mission. The fleet has been neglected: unnecessary packages installed (telnet, xinetd), firewall inactive, kernel parameters unhardened, and file permissions too loose. The cadet must write a playbook to sweep every node clean.

The cadet is provided with:
- A pre-filled inventory from Mission 1.1 (3 Ubuntu nodes: sdc-web, sdc-db, sdc-comms)
- A skeleton playbook (`workspace/playbook.yml`) with TODO markers
- A pre-written hardened sysctl configuration (`workspace/files/sysctl-hardened.conf`)

The cadet must:
1. **Remove unnecessary packages** using `ansible.builtin.apt`:
   - Remove `telnet` (cleartext protocol)
   - Remove `xinetd` (legacy super-server daemon)
   - Ensure `ufw` is present
2. **Configure the firewall** using `community.general.ufw`:
   - Allow SSH (port 22/tcp) BEFORE enabling — order is critical
   - Enable ufw
3. **Deploy hardened kernel parameters** using `ansible.builtin.copy`:
   - Copy `files/sysctl-hardened.conf` to `/etc/sysctl.d/99-fleet.conf`
   - Notify a handler to apply settings via `sysctl --system`
4. **Fix file permissions** using `ansible.builtin.file`:
   - Set `/etc/shadow` to mode 0640, owner root, group shadow
5. **Write a handler** for applying sysctl settings when the config file changes
6. **Verify idempotency** — second run should show `changed=0`

## Review Focus Areas

For the **Submission Review** section, specifically evaluate:
- Correct use of `apt` module (`state: absent` for removal, `state: present` for installation)
- Whether firewall tasks are in the correct order (allow SSH before enable)
- Correct use of `copy` module (src, dest, owner, group, mode)
- Correct use of `file` module for `/etc/shadow` permissions
- Handler structure — should use `command` module with `sysctl --system`
- Whether `notify` is present on the copy task
- Playbook formatting: consistent indentation, proper YAML syntax
- Whether `become: true` is set

For the **Security Observations** section, look for:
- Whether the cadet removed ALL unnecessary packages or just some
- Whether firewall rules are appropriately restrictive (only SSH allowed, not wide open)
- Whether the sysctl settings are deployed with correct file permissions (0644)
- Whether `/etc/shadow` permissions are correct (0640, not 0600 or 0644)
- Any additional hardening the student may have added beyond requirements
- Whether the student considered the order of operations (firewall lockout risk)

For the **Recommendations** section, consider suggesting:
- Using `apt` with a list of packages instead of separate tasks for each
- Adding more firewall rules beyond SSH (e.g., deny by default)
- Moving towards templates instead of static file copy (preview of Mission 1.4)
- Adding `validate` parameter where applicable
- Considering `changed_when` for command/shell tasks to improve idempotency
