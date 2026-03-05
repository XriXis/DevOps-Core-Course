# LAB 05 - Ansible Fundamentals

## 1. Architecture Overview
- Ansible version: `2.16.3`
- Target VM OS: Ubuntu 24.04
- Inventory model: static inventory (`inventory/hosts.ini`)

Role structure:
- `roles/common` - base packages
- `roles/docker` - Docker engine + service setup
- `roles/app_deploy` - image pull + container deployment + health check

## 2. Roles Documentation
### common
- Purpose: install baseline OS packages.
- Variables:
  - `common_packages`
- Handlers: none
- Dependencies: none

### docker
- Purpose: configure Docker repository and install Docker runtime.
- Variables:
  - `docker_packages`
  - `docker_users`
- Handlers:
  - `restart docker`
- Dependencies: common packages role should run first

### app_deploy
- Purpose: login to Docker Hub, pull image, recreate container, verify health endpoint.
- Variables:
  - `dockerhub_username`, `dockerhub_password`
  - `docker_image`, `docker_image_tag`
  - `app_port`, `app_container_name`, `app_env`
- Handlers:
  - `restart application container`
- Dependencies: Docker must already be installed on target host

## 3. Idempotency Demonstration
Paste terminal output from first `provision.yml` run (changed > 0):

```bash
$ ANSIBLE_CONFIG=./ansible.cfg ansible-playbook playbooks/provision.yml
```
```text
PLAY [Provision web servers] ***************************************************************

TASK [Gathering Facts] *********************************************************************
ok: [devopsmachine]

TASK [common : Update apt cache] ***********************************************************
ok: [devopsmachine]

TASK [common : Install common packages] ****************************************************
changed: [devopsmachine]

TASK [docker : Ensure apt prerequisites are installed] *************************************
ok: [devopsmachine]

TASK [docker : Ensure apt keyrings directory exists] ***************************************
ok: [devopsmachine]

TASK [docker : Add Docker official GPG key] ************************************************
changed: [devopsmachine]

TASK [docker : Add Docker apt repository] **************************************************
changed: [devopsmachine]

TASK [docker : Install Docker packages] ****************************************************
changed: [devopsmachine]

TASK [docker : Ensure Docker service is enabled and started] *******************************
ok: [devopsmachine]

TASK [docker : Add users to docker group] **************************************************
changed: [devopsmachine] => (item=xrixis)

TASK [docker : Install Python docker bindings] *********************************************
changed: [devopsmachine]

RUNNING HANDLER [docker : restart docker] **************************************************
changed: [devopsmachine]

PLAY RECAP *********************************************************************************
devopsmachine              : ok=12   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Provisioning 2nd ran

```text
PLAY [Provision web servers] ***************************************************************

TASK [Gathering Facts] *********************************************************************
ok: [devopsmachine]

TASK [common : Update apt cache] ***********************************************************
ok: [devopsmachine]

TASK [common : Install common packages] ****************************************************
ok: [devopsmachine]

TASK [docker : Ensure apt prerequisites are installed] *************************************
ok: [devopsmachine]

TASK [docker : Ensure apt keyrings directory exists] ***************************************
ok: [devopsmachine]

TASK [docker : Add Docker official GPG key] ************************************************
ok: [devopsmachine]

TASK [docker : Add Docker apt repository] **************************************************
ok: [devopsmachine]

TASK [docker : Install Docker packages] ****************************************************
ok: [devopsmachine]

TASK [docker : Ensure Docker service is enabled and started] *******************************
ok: [devopsmachine]

TASK [docker : Add users to docker group] **************************************************
ok: [devopsmachine] => (item=xrixis)

TASK [docker : Install Python docker bindings] *********************************************
ok: [devopsmachine]

PLAY RECAP *********************************************************************************
devopsmachine              : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Analysis:
- First run changed state by installing packages/repo/service/user group changes.
- Second run is totaly `ok` due to idempotent Ansible modules and desired-state model.

## 4. Ansible Vault Usage
- Sensitive vars are stored in `inventory/group_vars/all.yml` and are encrypted.
- Commands used:

```bash
ansible-vault encrypt inventory/group_vars/all.yml
ansible-vault view inventory/group_vars/all.yml
```

- Vault password strategy: run with `--ask-vault-pass` for each command. `.vault_pass` is gitignored and not committed.

Example encrypted header:

```text
$ANSIBLE_VAULT;1.1;AES256
...
```

## 5. Deployment Verification
```bash
$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

```text
Vault password:

PLAY [Deploy application] ******************************************************************

TASK [Gathering Facts] *********************************************************************
ok: [devopsmachine]

TASK [app_deploy : Log in to Docker Hub] ***************************************************
changed: [devopsmachine]

TASK [app_deploy : Pull application image] *************************************************
changed: [devopsmachine]

TASK [app_deploy : Stop existing container if running] *************************************
ok: [devopsmachine]

TASK [app_deploy : Remove existing container if present] ***********************************
ok: [devopsmachine]

TASK [app_deploy : Run application container] **********************************************
changed: [devopsmachine]

TASK [app_deploy : Wait for application port to be ready] **********************************
ok: [devopsmachine]

TASK [app_deploy : Verify health endpoint] *************************************************
ok: [devopsmachine]

RUNNING HANDLER [app_deploy : restart application container] *******************************
changed: [devopsmachine]

PLAY RECAP *********************************************************************************
devopsmachine              : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Container status:
```bash
ansible webservers -a "docker ps" --ask-vault-pass
```
```text
Vault password:
devopsmachine | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                            COMMAND           CREATED         STATUS         PORTS                    NAMES
90cc16606c6e   xrixis/devops-i-lobazov:latest   "python app.py"   9 minutes ago   Up 9 minutes   0.0.0.0:5000->5000/tcp   devops-i-lobazov
```

Health check:

```bash
curl http://10.247.1.39:5000/health
```

```text
{"status":"healthy","timestamp":"2026-02-26 19:25:40","uptime_seconds":736}
```

## 6. Key Decisions
- Why roles instead of plain playbooks?
Roles enforce modularity and clear ownership of tasks, defaults, and handlers. This keeps playbooks short and reusable.

- How do roles improve reusability?
A role can be applied to different hosts/projects with only variable overrides, without rewriting tasks.

- What makes a task idempotent?
It declares state (present/absent/started) and converges to it, so repeated runs do not keep changing resources.

- How do handlers improve efficiency?
Handlers run only when notified, preventing unnecessary service restarts on every run.

- Why is Ansible Vault necessary?
It allows storing secrets in Git safely by encrypting sensitive variables at rest.

## 7. Challenges
- Unavailability to utilize `.vault_pass` using ansible (host) via WSL - cannot clean the file from execution rights, what is rad by ansible as malformed project.
  - Fix: use `--ask-vault-pass` on runs instead of a local executable password file.
- Vault/group variables were not loaded when files were outside inventory scope.
  - Fix: move variables to `inventory/group_vars` and host connection vars to `inventory/host_vars`.
