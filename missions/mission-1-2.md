## Mission Context: 1.2 — Lock the Door

The cadet's second mission. The SSH Root Fairy has left every fleet node with dangerous SSH misconfigurations: root login enabled, password authentication on, and no LoginGraceTime set. The cadet must write their first Ansible playbook to harden SSH across all 3 fleet nodes.

The cadet is provided with:
- A pre-filled inventory from Mission 1.1 (3 nodes: sdc-web, sdc-db, sdc-comms)
- A skeleton playbook (`workspace/playbook.yml`) with TODO markers

The cadet must:
1. **Complete the playbook** using `ansible.builtin.lineinfile` to:
   - Set `PermitRootLogin no` in `/etc/ssh/sshd_config`
   - Set `PasswordAuthentication no` in `/etc/ssh/sshd_config`
   - Set `LoginGraceTime 30` in `/etc/ssh/sshd_config`
2. **Write a handler** to restart the SSH service when configuration changes
3. **Add `notify`** to each task so the handler is triggered on changes
4. **Verify idempotency** — running the playbook a second time should show `changed=0`

## Review Focus Areas

For the **Submission Review** section, specifically evaluate:
- Correct use of `lineinfile` module (regexp, line, state, path)
- Whether regexp patterns are specific enough to avoid false matches
- Handler structure and naming convention
- Whether `notify` is present on all tasks that modify sshd_config
- Playbook formatting: consistent indentation, proper YAML syntax
- Whether `become: true` is set (required for modifying system files)

For the **Security Observations** section, look for:
- Whether the cadet used `validate` parameter on lineinfile (e.g., `validate: 'sshd -t -f %s'`)
- Whether backup is enabled (`backup: yes`)
- If the student hardcoded values vs using variables (variables are better but not required at this level)
- Whether the handler correctly restarts SSH (not just reloads)
- Any additional SSH hardening the student may have added beyond requirements

For the **Recommendations** section, consider suggesting:
- Adding `validate: 'sshd -t -f %s'` to lineinfile tasks for safer config changes
- Using `backup: yes` to keep copies of original config
- Moving hardcoded values to variables for future reuse (preview of Mission 1.4)
- Using `ansible.builtin.template` instead of multiple lineinfile tasks (preview of advanced patterns)
- Adding a final verification task that checks SSH connectivity still works after hardening
