## Mission Context: 2.5 — Noise Storm (Sustained IOC / Defensive Hardening)

Lieutenant rank mission (Module 2). Adversary: **The Storm** — opaque range
infrastructure that hammers every node's SSH and web ports from a fixed source
address, and can rotate that address mid-engagement. Purely defensive: the cadet
writes and applies Ansible against their own three-node fleet only, never
against the Storm. The mission's core lesson is *generalisation* — blocking an
indicator as a variable, not a hardcoded literal, so the defence survives the
Storm changing address.

The fleet is `sdc-app` / `sdc-web` / `sdc-db` (172.30.0.11–13). The mission has
five sequential phases:

### Phase 1: Key-Only Auth
- Disable password authentication fleet-wide (sshd `PasswordAuthentication no`)
- Stops the Storm's credential guessing; SSH becomes key-only on all three nodes

### Phase 2: Rate-Limit & Ban
- Stand up fail2ban against the SSH hammering
- Repeat offenders are dropped at the TCP level, fleet-wide

### Phase 3: See the Storm (Observability)
- Triage the attack into a report naming the live IOC (the Storm's current source address)
- Forward all fleet logs to the SOC collector (centralised logging)

### Phase 4: Block the IOC
- Firewall-drop the Storm's traffic to the whole host, fleet-wide, on every port
- The blocked address must be handled as a variable/inventory value, not a literal

### Phase 5: Hold the Line (capstone)
- Withstand the Storm rotating to a new source address
- A defence that memorised one IP fails here; one built on a parameterised indicator holds

Student work lives entirely in `workspace/` (site.yml, collect-triage.yml,
block-ioc.yml, and roles under `workspace/roles/`). `.docker/` is range
infrastructure and is off-limits. `make test` exercises all five phases every
run and, in Phase 5, triggers the Storm's rotation — an all-skipped result means
the range stalled (reset), not a failure.

## Review Focus Areas

For the **Submission Review** section, evaluate:
- **Fleet-wide coverage**: Is every control applied to all three nodes, or does a node slip through? A hardened `sdc-app` with an exposed `sdc-web` is not a hardened fleet.
- **Generalisation**: Is the blocked IOC a variable (group_vars / inventory / registered fact), or a hardcoded IP literal? This is the mission's central test.
- **Layering**: Are auth-hardening, rate-limiting, observability, and the firewall block all present, or has the cadet leaned on a single layer?

For the **Security Observations** section, look for:
- Whether password auth is genuinely disabled (not just key auth added alongside)
- Whether fail2ban is actually active and jailed on SSH, not merely installed
- Whether log forwarding is real (destination configured) rather than stubbed
- Whether the firewall rule drops all ports for the IOC, not just SSH

For the **Recommendations** section:
- Encourage sourcing the IOC from a registered fact / inventory var so address rotation is a data change, not a code change
- Suggest idempotence checks — re-running should report no changes once the fleet is hardened
- Note that observability (Phase 3) is what lets an operator *find* the next rotated address; treat it as a first-class control, not an afterthought
- Mention that rate-limiting complements, not replaces, the firewall block
