## Mission Context: 2.3 — Fleet-Wide Operations (Multi-Host & Orchestration)

Lieutenant rank mission. No step-by-step guide — students get a briefing and figure out the implementation. This mission teaches fleet-scale operations: rolling updates, delegation, error handling.

The mission is an "Adventure Simulation" with three phases that build on each other:

### Phase 1: Rolling Update Basics
- Student writes `rolling-update.yml` that deploys to 4 app servers using `serial: 1`
- Deploys `templates/index.html.j2` to each server, restarts nginx
- Load balancer must remain serving throughout
- Target: sdc-app-1 through sdc-app-4 (Ubuntu, ports 2261-2264)

### Phase 2: Orchestrated Deployment
- Student creates `roles/fleet_deploy/` with full deployment lifecycle
- Role must use `delegate_to` for LB drain/enable operations
- Health checks included (uri, curl, or wait_for)
- `site.yml` calls the role with `serial` for rolling deploys
- LB: sdc-lb (HAProxy, port 2265), Monitor: sdc-monitor (Rocky, port 2266)

### Phase 3: Failure Handling
- Role must use `block/rescue/always` for error handling
- `max_fail_percentage` set to allow one server to fail
- sdc-app-4 has a planted failure (broken flag file)
- Rescue block must drain the failed server from the LB
- Deployment must succeed overall despite one server failing

## Review Focus Areas

For the **Submission Review** section, evaluate:
- **Phase 1**: Is serial used correctly? Does the template deploy correctly?
- **Phase 2**: Are delegate_to operations correct? Does the role handle the full lifecycle (drain → deploy → enable)?
- **Phase 3**: Is block/rescue/always structured correctly? Does the rescue actually protect the fleet?

For the **Security Observations** section, look for:
- Whether the deployment maintains availability throughout
- Whether failed servers are properly drained (not left serving broken content)
- Whether health checks are meaningful (not just "curl localhost")

For the **Recommendations** section:
- Suggest canary deployment patterns (serial: [1, 2, "100%"])
- Mention ansible-pull for autonomous hardening
- Note fact caching for fleet performance
- Suggest testing the rescue path explicitly
