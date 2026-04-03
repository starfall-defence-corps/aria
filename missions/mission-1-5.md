## Mission Context: 1.5 — Clean House

The cadet's fifth and final Module 1 mission. Colonel Hardcoded-Password has left plaintext credentials on every fleet node. The cadet must restructure all previous work (1.2–1.4) into a proper Ansible role, encrypt secrets with Vault, and follow Git workflow discipline.

The fleet is mixed-OS: sdc-web (Ubuntu 22.04), sdc-db (Rocky Linux 9), sdc-comms (Ubuntu 22.04). Each node has plaintext credentials at `/opt/fleet-db-creds.txt`.

The cadet is provided with:
- A pre-filled inventory with group_vars skeleton files
- A commented-out `site.yml` pointing to the role
- `ansible.cfg` with `vault_password_file = .vault-pass` pre-configured
- NO skeleton playbook or role — the cadet creates everything from scratch

The cadet must:
1. **Create a role** using `ansible-galaxy init roles/fleet_hardening` with:
   - `tasks/main.yml` — consolidated hardening tasks from 1.2–1.4
   - `handlers/main.yml` — SSH restart handler using `{{ ssh_service_name }}`
   - `templates/` — sshd_config.j2 and motd.j2
   - `defaults/main.yml` — default variable values (overridable)
   - `meta/main.yml` — role metadata
2. **Create and encrypt a vault file** (`vault.yml`) containing:
   - `vault_ssh_login_grace_time`
   - `vault_banner_message`
3. **Create `.vault-pass`** file with the vault password (gitignored)
4. **Uncomment `site.yml`** to call the role with `vars_files: vault.yml`
5. **Ensure no plaintext secrets** exist anywhere in the workspace
6. **Verify idempotency** on both OS families

## Review Focus Areas

For the **Submission Review** section, specifically evaluate:
- Role directory structure completeness (tasks, handlers, templates, defaults, meta)
- Whether tasks are properly consolidated from previous missions (not just copied blindly)
- Correct variable precedence usage (defaults vs vars vs group_vars)
- Whether `vault.yml` is properly encrypted (`$ANSIBLE_VAULT;` header)
- Whether `.vault-pass` is gitignored (should NOT be committed)
- Whether `site.yml` correctly references the role and vault
- Template content in the role's templates/ directory
- Handler uses variables for service names

For the **Security Observations** section, look for:
- **CRITICAL**: Any plaintext secrets in committed files (passwords, API keys, credentials)
- Whether vault variables are properly referenced (not re-hardcoded in the role)
- Whether `.gitignore` excludes sensitive files (.vault-pass, .ssh/, etc.)
- Whether the Colonel's credentials (`V01dborn_Hunter_2187`, `sk-sdc-*`) appear anywhere
- Whether the vault password itself is sufficiently strong (not just "password")
- Git commit history — are there any commits that contained secrets before encryption?

For the **Recommendations** section, consider suggesting:
- Using `ansible-lint` for role quality checking
- Separating role into smaller, focused roles (ssh_hardening, firewall, etc.)
- Using `meta/main.yml` dependencies for role composition
- Adding a `tests/` directory with basic Molecule scenario in the role
- Using `vars_prompt` or environment variables instead of `.vault-pass` files in production
- Pre-commit hooks to prevent accidental secret commits
