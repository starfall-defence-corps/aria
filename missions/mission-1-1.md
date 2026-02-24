## Mission Context: 1.1 — Fleet Census

The cadet's first mission. The fleet's asset registry is in disarray after Agent Chmod-777 left classified files with world-readable permissions (777) across fleet nodes. The cadet must:

1. **Build an Ansible inventory** (`workspace/inventory/hosts.yml`) cataloguing 3 fleet nodes:
   - `sdc-web` (web server, port 2221)
   - `sdc-db` (database server, port 2222)
   - `sdc-comms` (communications relay, port 2223)
   - All connect via `localhost` as `ansible_host`, SSH user `cadet`, SSH key auth
   - Hosts should be organised into logical groups (e.g., `web_servers`, `db_servers`, `comms_relays`)

2. **Verify connectivity** using `ansible all -m ping`

3. **Gather facts** using `ansible all -m setup` to identify OS, IPs, memory per node

4. **Run ad-hoc commands** to inspect disk, services, and discover the 777-permission files in `/opt/fleet-data/`

5. **Filter facts** to extract specific system information

## Review Focus Areas

For the **Submission Review** section, specifically evaluate:
- Correct YAML structure and indentation in the inventory
- Appropriate grouping of hosts (web, db, comms)
- Correct connection variables (`ansible_host`, `ansible_port`, `ansible_user`, `ansible_ssh_private_key_file`)
- Whether `ansible_connection: ssh` is explicitly set (not required but shows awareness)

For the **Security Observations** section, look for:
- Hardcoded passwords or credentials in the inventory
- Whether the inventory structure is appropriate for a classified fleet
- Any observations about the 777-permission files if the test output references them

For the **Recommendations** section, consider suggesting:
- Using `group_vars/` instead of inline variables
- Vault-encrypting sensitive values in future missions
- Using `ansible_ssh_common_args` for SSH hardening
