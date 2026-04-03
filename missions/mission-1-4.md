## Mission Context: 1.4 — One Playbook, Many Ships

The cadet's fourth mission. Voidborn operative Corporal Copy-Paste has written 47 separate playbooks for the fleet. The cadet must replace them with ONE playbook that works on both Ubuntu and Rocky Linux using variables, Jinja2 templates, and conditionals.

The fleet is now **mixed-OS**: sdc-web (Ubuntu 22.04), sdc-db (Rocky Linux 9), sdc-comms (Ubuntu 22.04).

The cadet is provided with:
- A pre-filled inventory with `debian` and `redhat` groups
- Skeleton `group_vars/` files with TODO markers (all.yml, debian.yml, redhat.yml)
- Pre-written Jinja2 templates (`templates/sshd_config.j2`, `templates/motd.j2`)
- A skeleton playbook with TODO markers

The cadet must:
1. **Define variables** in group_vars:
   - `all.yml`: SSH settings (`ssh_permit_root_login`, `ssh_password_authentication`, `ssh_login_grace_time`, `ssh_max_auth_tries`), `banner_message`
   - `debian.yml`: `ssh_service_name: ssh`, `firewall_pkg: ufw`
   - `redhat.yml`: `ssh_service_name: sshd`, `firewall_pkg: firewalld`
2. **Deploy SSH configuration** using `ansible.builtin.template` with `sshd_config.j2`
3. **Deploy login banner** using `ansible.builtin.template` with `motd.j2`
4. **Install firewall** using conditional `apt`/`dnf` tasks with `when: ansible_os_family`
5. **Configure firewall** — ufw on Debian, firewalld on RedHat (both via conditionals)
6. **Write a handler** that uses `{{ ssh_service_name }}` variable for the service name
7. **Verify idempotency** on both OS families

## Review Focus Areas

For the **Submission Review** section, specifically evaluate:
- Whether the cadet uses variables from group_vars instead of hardcoding OS-specific values
- Correct use of `template` module (src, dest, owner, group, mode, validate)
- Whether `when` conditionals use `ansible_os_family` (not hostname checks)
- Whether conditional tasks cover BOTH OS families (not just one)
- Whether the handler uses `{{ ssh_service_name }}` variable
- Template syntax in .j2 files (correct `{{ }}` usage)
- Group_vars structure: shared values in all.yml, OS-specific in debian.yml/redhat.yml
- Playbook formatting and consistent indentation

For the **Security Observations** section, look for:
- Whether `validate: 'sshd -t -f %s'` is used on the SSH template deployment
- Whether firewall rules are applied before enabling (lockout prevention on both OS families)
- Whether the MOTD template reveals too much system information
- Whether variable values are appropriate (e.g., LoginGraceTime not too long)
- Any additional multi-OS hardening beyond requirements

For the **Recommendations** section, consider suggesting:
- Using `ansible.builtin.package` module for OS-agnostic package management
- Using `block`/`when` to group OS-specific tasks instead of individual `when` clauses
- Moving towards roles for better organisation (preview of Mission 1.5)
- Adding host_vars for node-specific overrides
- Using Jinja2 filters in templates (e.g., `| default()`, `| int`)
