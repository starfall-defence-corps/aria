## Mission Context: Gateway Simulation — Operation First Contact

The Gateway Simulation is the **capstone assessment** for Module 1 (Basic Training). The cadet must combine every skill from missions 1.1–1.5 to secure a compromised forward observation post under a 75-minute time limit. No step-by-step guidance is provided — only a briefing.

The forward observation post is a mixed-OS fleet: sdc-fwd-web (Ubuntu 22.04), sdc-fwd-db (Rocky Linux 9), sdc-fwd-comms (Ubuntu 22.04). All nodes are compromised with combined misconfigurations from the entire module: SSH root login enabled, password auth enabled, telnet/xinetd on Ubuntu, firewall inactive, weak file permissions, hardcoded credentials at `/opt/fleet-db-creds.txt`, no kernel hardening, no login banners.

The cadet is provided with:
- `ansible.cfg` (pre-configured, vault_password_file commented out)
- `RECON.md` template (to fill in)
- `files/sysctl-hardened.conf` (pre-written kernel hardening)
- `site.yml` (commented out skeleton)
- **NO inventory** — the cadet writes it from scratch
- **NO role** — the cadet creates it with `ansible-galaxy init`

The assessment has three missions:

### Mission 1: Reconnaissance
- Write `inventory/hosts.yml` with `debian` and `redhat` groups
- Create `inventory/group_vars/` with OS-specific variables (at least `debian.yml` and `redhat.yml`)
- Use ad-hoc commands to assess the post
- Document findings in `RECON.md`

### Mission 2: Hardening
- Create `roles/fleet_hardening/` with tasks, handlers, templates, defaults
- Build role with: SSH hardening, firewall (ufw/firewalld), service cleanup (remove telnet), MOTD template, sysctl hardening
- Write `site.yml` to call the role
- Deploy and verify idempotency

### Mission 3: Secure & Submit
- Create `.vault-pass` with password `first-contact`
- Create and encrypt `vault.yml` with sensitive values
- Update `site.yml` with `vars_files: [vault.yml]`
- Ensure no plaintext secrets in workspace

## Review Focus Areas

For the **Submission Review** section, evaluate comprehensiveness:
- Does the inventory correctly define groups matching the OS families?
- Are group_vars populated with OS-specific service names and packages?
- Is RECON.md actually filled in with findings, not just the empty template?
- Does the role cover ALL required hardening (SSH, firewall, services, sysctl, MOTD, permissions)?
- Is the role structure complete (tasks, handlers, templates, defaults)?
- Does `when` conditionals correctly handle both Debian and RedHat?
- Is `vault.yml` properly encrypted?
- Does `site.yml` reference both the role and vault?

For the **Security Observations** section, look for:
- **CRITICAL**: Any plaintext secrets (passwords, API keys, credentials) in committed files
- Whether the Colonel's credentials (`V01dborn_Hunter_2187`, `sk-sdc-*`) appear anywhere
- Whether `.vault-pass` is properly gitignored
- Whether `/etc/shadow` permissions are being fixed (should be 0640, not 0644)
- Whether telnet is being removed (not just stopped)
- Whether sysctl hardening disables IP forwarding

For the **Recommendations** section:
- This is an assessment — be direct about what's missing or wrong
- Note if the solution is fragile (hard-coded paths, missing error handling)
- Comment on code quality (naming, organization, use of variables)
- Note performance tier if timing information is available
- Emphasize readiness (or lack thereof) for Module 2
