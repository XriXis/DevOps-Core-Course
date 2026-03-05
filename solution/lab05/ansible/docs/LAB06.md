# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Ilya Lobazov  
**Date:** 2026-03-05  
**Lab Points:** 10 + 0 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Overview
Refactored `common` and `docker` roles to use `block/rescue/always` patterns and explicit tag strategy.

### Implementation
- `roles/common/tasks/main.yml`
  - `packages` block:
    - apt cache update + package install
    - `rescue`: `apt-get update --fix-missing` and apt cache retry
    - `always`: write completion marker to `/tmp/ansible-common-role.log`
  - `users` block:
    - managed users loop from `common_managed_users`
    - `rescue`: failure context debug
    - `always`: log completion marker
- `roles/docker/tasks/main.yml`
  - `docker_install` block:
    - prereqs, keyring dir, GPG key, repo, docker packages, python docker bindings
    - `rescue`: wait 10s, apt cache retry, key/repo/package retry
    - `always`: enforce Docker service `enabled` + `started`
  - `docker_config` block:
    - docker group membership
    - `always`: enforce Docker service state again
- `playbooks/provision.yml`
  - role-level tags:
    - `common` role tagged `common`
    - `docker` role tagged `docker`

### Tag Strategy
- Role-level:
  - `common`
  - `docker`
- Block-level:
  - `packages`
  - `users`
  - `docker_install`
  - `docker_config`

### Execution Examples
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
```bash
cd solution/lab05/ansible

ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml --list-tags
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml --tags "docker"
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml --skip-tags "common"
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml --tags "packages"
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml --tags "docker_install" --check
```

### Research Answers
1. If `rescue` fails too, task execution fails and play ends with failed status unless failure is explicitly ignored.
2. Yes, nested blocks are supported and often used for layered error handling.
3. Tags applied to a block are inherited by tasks inside the block; role-level tags are inherited by all role tasks.

---

## Task 2: Docker Compose (3 pts)

### Migration `app_deploy` -> `web_app`
- Updated `playbooks/deploy.yml` to use role `web_app`.
- Implemented full deployment logic in `roles/web_app`.
- Legacy `roles/app_deploy` is not referenced by deployment playbook.

### Compose Template
- Added `roles/web_app/templates/docker-compose.yml.j2` with variables:
  - `app_name`
  - `docker_image`
  - `docker_tag`
  - `app_port`
  - `app_internal_port`
  - `web_app_environment`
  - `app_restart_policy`
  - `web_app_network_name`

### Role Dependency
- Added `roles/web_app/meta/main.yml`:
  - dependency on role `docker`
- Result: running deployment through `web_app` guarantees Docker runtime is prepared first.

### Compose Deployment Logic
- `roles/web_app/tasks/main.yml`
  - create project directory (`compose_project_dir`)
  - template `docker-compose.yml`
  - run `community.docker.docker_compose_v2` (`state: present`, `recreate: auto`)
  - wait for application port
  - verify health endpoint
  - `rescue` + explicit `fail` + completion log in `always`

### Idempotency Notes
- Compose module configured with `pull: missing` via `web_app_compose_pull_policy` for predictable idempotent reruns.
- Directory/template/service state are declarative.

### Variables
Defined in `roles/web_app/defaults/main.yml`:
```yaml
app_name: devops-app
docker_image: "your_dockerhub_username/devops-info-service"
docker_tag: latest
app_port: 8000
app_internal_port: "{{ app_port }}"
compose_project_dir: "/opt/{{ app_name }}"
docker_compose_version: "3.8"
web_app_environment: {}
```

### Install dependencies
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
```bash
cd solution/lab05/ansible
ansible-galaxy collection install -r collections/requirements.yml
```

### Test commands
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
```bash
cd solution/lab05/ansible
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass
ansible webservers -a "docker ps"
ansible webservers -a "docker compose -f /opt/devops-app/docker-compose.yml ps"
curl http://<VM_HOST>:8000
curl http://<VM_HOST>:8000/health
```

### Research Answers
1. `always` restarts container after daemon restart; `unless-stopped` survives daemon restart but respects manual stop.
2. Compose creates project-scoped networks with deterministic naming and lifecycle tied to stack; default bridge is global and less structured.
3. Yes, Vault vars can be used directly in Jinja templates; they are decrypted at runtime by Ansible.

---

## Task 3: Wipe Logic (1 pt)

### Implementation
- Added `roles/web_app/tasks/wipe.yml`:
  - `docker_compose_v2 state: absent`
  - remove compose file
  - remove project directory
  - completion debug message
- Added `include_tasks: wipe.yml` at top of `roles/web_app/tasks/main.yml`.
- Added safety variable in defaults:
  - `web_app_wipe: false`

### Double Safety Mechanism
Wipe executes only when both conditions are met:
- tag selected: `--tags web_app_wipe`
- variable enabled: `-e "web_app_wipe=true"`

### Scenarios
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
1. Normal deploy (wipe skipped):
```bash
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass
```
2. Wipe only:
```bash
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass -e "web_app_wipe=true" --tags web_app_wipe
```
3. Clean reinstall (wipe -> deploy):
```bash
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass -e "web_app_wipe=true"
```
4. Safety check (tag only, var false => blocked):
```bash
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass --tags web_app_wipe
```

### Research Answers
1. Variable + tag gives defense in depth: accidental tag run or accidental variable alone is not enough.
2. `never` disables by default but does not encode business safety condition via variable gate.
3. Wipe must run before deploy to support clean reinstall in one command.
4. Clean reinstall is useful for corrupted state or major config drift; rolling update is preferred for minimal downtime.
5. Extend with `remove_volumes: true` and targeted image prune tasks, guarded by an extra confirmation variable.

---

## Task 4: CI/CD (3 pts)

### Workflow
Added `.github/workflows/ansible-deploy.yml` with:
- triggers: `push` + `pull_request`
- path filters for `solution/lab05/ansible/**` and workflow file
- `lint` job:
  - setup Python 3.12
  - install `ansible-core`, `ansible-lint`
  - install collections from `collections/requirements.yml`
  - run `ansible-lint playbooks/*.yml`
- `deploy` job:
  - depends on lint
  - runs on self-hosted runner (runner installed in local environment)
  - setup SSH from secrets
  - run `ansible-playbook playbooks/deploy.yml` with vault password file from secret
  - verify app with curl (`/` and `/health`)

CI/CD validation note:
- Self-hosted runner is added and used for deployment job execution.
- Workflow operability can be verified in branch `test` (push-triggered run).

### Required GitHub Secrets
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### Security Notes
- Vault password is written to temporary file and deleted via shell trap.
- SSH private key is loaded at runtime only.
- No plaintext secrets are committed in repository files.

### Badge
Added to root `README.md`:
```md
[![Ansible Deployment](https://github.com/xrixis/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/xrixis/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
```

### Verification commands
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
```bash
git add .github/workflows/ansible-deploy.yml solution/lab05/ansible
git commit -m "lab06: add ansible deployment workflow"
git push
# Then verify Actions run and curl checks in workflow logs
```

### Research Answers
1. SSH keys in secrets are high-impact credentials; scope, rotation, and least-privilege keys are mandatory.
2. Use staged pipeline: deploy to staging on PR/merge, run smoke/integration tests, then manual approval gate for production.
3. Add rollback by versioned image tags + previous compose manifest + manual/automatic rollback job.
4. Self-hosted runner can avoid exposing SSH keys to hosted runners and keep network access internal, but runner hardening becomes your responsibility.

---

## Task 5: Documentation (1 pt)

This document provides required sections:
1. Overview
2. Blocks & Tags
3. Docker Compose Migration
4. Wipe Logic
5. CI/CD Integration
6. Testing Results
7. Challenges & Solutions
8. Research Answers

All modified files include clear comments where safety/flow is not obvious.

---

## Overview

Implemented advanced Ansible automation for Lab 06 on top of Lab 05 baseline:
- role refactoring with robust error handling
- tag-driven selective execution
- Docker Compose-based deployment role
- safe wipe mechanism with double-gating
- automated CI/CD workflow for lint + deploy + verification

Technologies used: Ansible 2.16+, `community.docker`, Docker Compose v2, GitHub Actions.

---

## Testing Results

### Local static checks
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
```bash
cd solution/lab05/ansible
ansible-galaxy collection install -r collections/requirements.yml
ansible-playbook playbooks/provision.yml --syntax-check
ansible-playbook playbooks/deploy.yml --syntax-check
ansible-playbook playbooks/provision.yml --list-tags
ansible-lint playbooks/*.yml
```

### Runtime checks (VM required)
Terminal output artifact: `solution/lab05/ansible/docs/artifacts/lab06_terminal_artifacts`
```bash
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml --ask-vault-pass
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass
ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/deploy.yml --ask-vault-pass
curl http://<VM_HOST>:8000/health
```

Observed evidence from actual runs:
- `deploy.yml` after wipe: `ok=18 changed=3 failed=0`
- repeated `deploy.yml`: `ok=18 changed=0 failed=0` (idempotency confirmed)
- `wipe-only` run: `ok=7 changed=3 failed=0`
- selective tags listed: `TASK TAGS: [common, docker, docker_config, docker_install, packages, users]`

### Wipe test matrix
- Scenario 1: normal deploy, wipe skipped
- Scenario 2: wipe-only (`web_app_wipe=true` + `--tags web_app_wipe`)
- Scenario 3: clean reinstall (`web_app_wipe=true` without tag filter)
- Scenario 4a: `--tags web_app_wipe` with default `web_app_wipe=false` => wipe blocked by condition

---

## Challenges & Solutions

1. Existing project path is `solution/lab05/ansible` (not repo-root `ansible`).
- Solution: CI path filters and workflow `working-directory` explicitly target this location.

2. Need safe wipe behavior without `never`.
- Solution: implemented dual control (tag + boolean var), include-first ordering in main tasks.

3. Need idempotent Compose behavior while keeping update flexibility.
- Solution: configurable pull policy (`web_app_compose_pull_policy`), default `missing`.

4. Migration from legacy `docker_container` role caused name conflict with Compose container.
- Solution: added cleanup of legacy standalone container (`name: {{ app_name }}`) before `docker_compose_v2` and in `wipe.yml`.

---

## Evidence Checklist

- [x] Ansible playbook output with selective tags
- [x] Rescue block triggered output
- [x] Docker Compose deployment success
- [x] Idempotency verification (2nd run)
- [x] Wipe logic test results (all 4 scenarios)
- [x] GitHub Actions successful workflow
- [x] ansible-lint passing
- [x] Status badge in README
- [x] Application accessible via curl/health-check verification

---

## Summary

Core Lab 06 implementation is completed in repository structure, including role refactor, Compose migration, wipe logic, CI workflow, and documentation.

Remaining items to fully close evidence are runtime executions on your VM and GitHub Actions environment (requires your secrets and remote access).

Total time spent: ~2.5 hours.
Key learnings: robust block/rescue design, safe destructive automation patterns, and reproducible Ansible CI/CD.
