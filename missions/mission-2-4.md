## Mission Context: 2.4 — The Automated Defence Line (CI/CD Pipelines)

Lieutenant rank mission. Villain: Private YOLO-Deploy (final confrontation). Students learn to build CI/CD pipelines that enforce quality gates: lint, test, scan. This is the only mission focused on GitHub Actions workflow YAML, not Ansible targeting infrastructure.

The mission has three phases:

### Phase 1: Obstacle Course — CI Workflow
- Student writes `.github/workflows/ci.yml` for a provided SSH hardening role
- Workflow must have lint (ansible-lint) and test (Molecule) jobs
- Matrix strategy for multi-OS testing (Ubuntu + Rocky)
- Test job depends on lint job (needs keyword)

### Phase 2: Obstacle Course — Pipeline Stages + Drift Detection
- Student writes a Makefile with lint, test, scan targets
- Student writes a scheduled drift detection workflow
- Drift workflow uses cron schedule trigger

### Phase 3: Main Mission — Complete Pipeline
- Student creates full CI pipeline for fleet_hardening role
- CI workflow with lint → test stages
- Drift detection workflow with schedule
- ansible-lint configuration
- Makefile with local pipeline targets
- PIPELINE.md documenting branch protection plan

## Review Focus Areas

For the **Submission Review** section, evaluate:
- **Workflow Structure**: Are jobs properly chained with `needs`? Is matrix configured correctly?
- **Pipeline Stages**: Are lint, test, scan stages meaningful? Do they use appropriate tools?
- **Drift Detection**: Is the schedule sensible? Does it include failure notification?

For the **Security Observations** section, look for:
- Whether CI secrets are handled properly (not hardcoded in workflows)
- Whether the pipeline would catch the issues from previous missions (SSH misconfig, CIS violations)
- Whether branch protection rules in PIPELINE.md would prevent YOLO-Deploy scenarios

For the **Recommendations** section:
- Suggest caching for faster CI runs
- Mention reusable workflows for shared pipeline logic
- Note the importance of fail-fast vs fail-slow in matrix jobs
- Suggest adding a deploy stage with approval gates
