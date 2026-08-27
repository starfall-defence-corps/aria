## Mission Context: 1.6 — Inventory from Nothing

The cadet's final Foundation mission. Unlike Mission 1.1 (which hands over the host list), here the cadet is given **only** the subnet `172.30.0.0/24` and must discover the fleet themselves, then build an inventory that survives an adversary — **Nyx, the Signal Ghost** — who rotates the fleet's addressing. Purely defensive: the cadet maps infrastructure they are authorised to map (their own range); there is no offensive scanning of third parties.

Hidden on the subnet are **3 managed fleet nodes** (each answers on SSH port 22 plus one service port) and **1 decoy** (answers on 8080 only, no SSH — NOT fleet). Node hostnames are opaque tokens, so role can be inferred **only** from the open service port. Node IPs are randomised each `make setup`. The cadet works from a recon node (`sdc-ops`).

The cadet must:

1. **Recon sweep** (`workspace/recon/live-hosts.txt`) — discover live hosts with `nmap -sn 172.30.0.0/24` (excluding the gateway `.1` and the recon node `.10`).
2. **Service fingerprint** (`workspace/recon/services.yml`) — map each host's open ports and infer role from the service port: `80`→`web_servers`, `5432`→`db_servers`, `6379`→`comms_relays`. A host with no SSH that only serves `8080` is the decoy → `unmanaged`.
3. **Grouped static inventory** (`workspace/inventory/hosts.yml`) — list the managed nodes by IP, grouped `web_servers`/`db_servers`/`comms_relays` (parent `fleet`). The decoy must be excluded. Connection vars are pre-wired in `workspace/ansible.cfg`.
4. **Facts sweep → fleet report** (`workspace/reports/fleet-report.yml`) — a `fleet:` list with `ip`, `hostname`, `role`, `os`, `os_version`, `memtotal_mb`, and `nonce`. The nonce is a live local fact (`ansible_local.sdc.nonce`) that proves the cadet actually contacted each node.
5. **Dynamic inventory (capstone)** (`workspace/inventory/live_subnet.py`, executable — or an `inventory/nmap.yml` using the `community.general.nmap` plugin) — re-discovers the fleet live and groups by role, so it **survives Nyx's IP rotation** where the static `hosts.yml` goes stale.

## Review Focus Areas

For the **Submission Review** section, evaluate:
- Correct grouping keyed to **port evidence** (role inferred from the service port, not guessed from names)
- The decoy correctly excluded from the managed inventory
- Whether the dynamic inventory is genuinely **discovery-based** (re-scans live) rather than a static host list renamed
- Clean YAML structure and connection hygiene (no per-host secrets; relies on `ansible.cfg`)

For the **Security Observations** section, look for:
- Any hardcoded IPs or credentials committed into the repo (the whole point is that addresses are discovered, not hardcoded)
- Authorised-recon framing — the cadet is mapping their own range; flag any language or technique that implies scanning third-party infrastructure
- Whether the fleet report unnecessarily leaks the range nonce beyond what the exercise asks

For the **Recommendations** section, consider suggesting:
- Preferring inventory plugins / dynamic inventory over static files for fleets whose addressing changes
- Using `keyed_groups`/`groups` (or an executable inventory) to derive role groups from live service evidence
- Documenting the port→role fingerprint legend alongside the inventory
