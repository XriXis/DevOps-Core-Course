# LAB12 - ConfigMaps And Persistent Volumes

## 1. Overview

This lab extends the FastAPI service and Helm chart from Labs 10-11 with:

- a persisted visits counter stored in `/data/visits`
- a new `GET /visits` endpoint
- a file-based ConfigMap mounted at `/config/config.json`
- an environment-variable ConfigMap injected through `envFrom`
- a `PersistentVolumeClaim` mounted at `/data`
- checksum-based rollout on ConfigMap changes

Implementation targets:

- keep configuration outside the image
- keep visit data across container and pod restarts
- prove mounted ConfigMap access and injected environment variables
- document persistence with real CLI evidence instead of screenshots

Updated scope:

```text
solution/app_python/
  app.py
  Dockerfile
  docker-compose.yml
  README.md
  tests/test_app.py

solution/k8s/devops-info-service/
  files/config.json
  values.yaml
  values-dev.yaml
  values-prod.yaml
  templates/
    _helpers.tpl
    configmap.yaml
    deployment.yaml
    pvc.yaml
```

## 2. Application Changes

### 2.1 Visits counter implementation

Implemented behavior:

- every request to `GET /` increments the counter
- the counter is stored in `VISITS_FILE` and defaults to `/data/visits`
- `GET /visits` returns the current persisted counter without incrementing it
- the counter file is initialized with `0` if it does not exist
- writes use an in-process lock plus atomic file replace

Relevant application behavior:

- configuration file path comes from `CONFIG_PATH` and defaults to `/config/config.json`
- if the config file is missing, the app falls back to safe built-in defaults
- the `GET /` response now includes:
  - loaded configuration file path and content
  - environment variables relevant to runtime configuration
  - current visits counter and visits file path

### 2.2 Local automated test results

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Observed output:

```text
........................................
40 passed in 1.28s
```

Lint verification:

```powershell
.\.venv\Scripts\python.exe -m flake8 app.py tests\test_app.py
```

Observed output:

```text
<no output>
```

## 3. Local Docker Persistence Verification

### 3.1 Docker Compose setup

Created `solution/app_python/docker-compose.yml` with:

- local image build
- port mapping `5000:5000`
- volume mount `./data:/data`
- `VISITS_FILE=/data/visits`

### 3.2 Local persistence evidence

Command pattern used:

```powershell
cd solution/app_python
docker compose up --build -d
Invoke-RestMethod http://localhost:5000/
Invoke-RestMethod http://localhost:5000/
Invoke-RestMethod http://localhost:5000/visits
Get-Content .\data\visits
docker compose restart
Invoke-RestMethod http://localhost:5000/visits
Get-Content .\data\visits
```

Observed output summary:

```json
{
  "first_root_visits": 2,
  "second_root_visits": 3,
  "before_restart_visits": 3,
  "after_restart_visits": 3
}
```

File evidence after restart:

```json
{
  "visits_endpoint": 3,
  "file_before": "3",
  "file_after": "3"
}
```

Conclusion:

- the root endpoint increments the counter
- the counter is written to the host-mounted file
- container restart does not reset the counter

## 4. ConfigMap Implementation

### 4.1 File-based ConfigMap

Chart file added:

```text
solution/k8s/devops-info-service/files/config.json
```

Template added:

```text
solution/k8s/devops-info-service/templates/configmap.yaml
```

Config file content:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsEndpoint": true,
    "configFromConfigMap": true,
    "hotReloadViaChecksumRestart": true
  },
  "settings": {
    "welcomeMessage": "Hello from ConfigMap",
    "documentation": "Lab 12 configuration mounted from a Helm-managed ConfigMap"
  }
}
```

The template loads this file using `.Files.Get` and exposes it as `config.json` in a ConfigMap.

### 4.2 Environment-variable ConfigMap

The same template file also creates a second ConfigMap with key-value pairs from `values.yaml`:

```yaml
configMaps:
  env:
    data:
      APP_ENV: dev
      LOG_LEVEL: info
      FEATURE_VISITS: "true"
      FEATURE_CONFIG_RELOAD: checksum-restart
```

These keys are injected through `envFrom.configMapRef`.

### 4.3 Deployment integration

Deployment changes:

- mounted the file ConfigMap as a volume at `/config`
- injected the env ConfigMap through `envFrom`
- added runtime env vars:
  - `CONFIG_PATH=/config/config.json`
  - `VISITS_FILE=/data/visits`
- added checksum annotations so Helm upgrades trigger rollout when ConfigMaps change

### 4.4 Verification output

Command:

```powershell
.\kubectl.exe get configmap,pvc -n devops-lab12
```

Observed output:

```text
NAME                                                     DATA   AGE
configmap/devops-info-lab12-devops-info-service-config   1      69s
configmap/devops-info-lab12-devops-info-service-env      4      7m32s
configmap/kube-root-ca.crt                               1      7m54s

NAME                                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-lab12-devops-info-service-data   Bound    pvc-c5a3fef4-fa5e-4eb3-bf07-00d6cc43619e   100Mi      RWO            standard       <unset>                 7m32s
```

File inside pod:

```powershell
.\kubectl.exe exec -n devops-lab12 <pod> -- cat /config/config.json
```

Observed output:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsEndpoint": true,
    "configFromConfigMap": true,
    "hotReloadViaChecksumRestart": true
  },
  "settings": {
    "welcomeMessage": "Hello from ConfigMap",
    "documentation": "Lab 12 configuration mounted from a Helm-managed ConfigMap"
  }
}
```

Environment variables inside pod:

```powershell
.\kubectl.exe exec -n devops-lab12 <pod> -- /bin/sh -c 'printenv | sort | grep ...'
```

Observed output:

```text
APP_ENV=dev
LOG_LEVEL=trace
FEATURE_VISITS=true
FEATURE_CONFIG_RELOAD=checksum-restart
HOST=0.0.0.0
PORT=5000
DEBUG=false
RELEASE_VERSION=v1
VISITS_FILE=/data/visits
CONFIG_PATH=/config/config.json
```

## 5. Persistent Volume Implementation

### 5.1 PVC configuration

Added `solution/k8s/devops-info-service/templates/pvc.yaml` with:

- `ReadWriteOnce`
- configurable storage size
- configurable storage class
- default size `100Mi`

Values used:

```yaml
persistence:
  enabled: true
  mountPath: /data
  accessModes:
    - ReadWriteOnce
  size: 100Mi
  storageClass: ""
```

### 5.2 Why `ReadWriteOnce`

`ReadWriteOnce` is appropriate for this lab because:

- the app persists a single shared file-based counter
- the chart defaults to one replica to avoid multi-writer inconsistencies
- Minikube's default storage class provisions a single-node hostPath-backed volume

This is the correct tradeoff for a lab focused on persistence, not horizontal scale. A file-based counter is not a good multi-replica production design.

### 5.3 Pod mount configuration

Deployment volume setup:

- PVC volume mounted at `/data`
- application writes `VISITS_FILE=/data/visits`

### 5.4 Persistence test evidence

HTTP verification before and after pod replacement:

```json
{
  "root1_visits": 1,
  "root2_visits": 2,
  "visits_endpoint": 2,
  "config_file_exists": true,
  "config_environment": "dev"
}
```

Pod deletion test:

```powershell
.\kubectl.exe delete pod devops-info-lab12-devops-info-service-558bdb6db6-ntx4l -n devops-lab12
```

Observed output:

```text
pod "devops-info-lab12-devops-info-service-558bdb6db6-ntx4l" deleted from devops-lab12 namespace
```

Before/after evidence:

```json
{
  "old_pod": "devops-info-lab12-devops-info-service-558bdb6db6-ntx4l",
  "before_delete_visits": 2,
  "new_pod": "devops-info-lab12-devops-info-service-558bdb6db6-7blks",
  "after_restart_visits": 2,
  "file_after_restart": "2"
}
```

Conclusion:

- the pod was replaced
- the visits counter remained `2`
- the file persisted on the PVC and was visible in the new pod

## 6. Helm Validation

Lint:

```powershell
.\helm.exe lint solution\k8s\devops-info-service
```

Observed output:

```text
==> Linting solution\k8s\devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Install command used for the validated run:

```powershell
.\helm.exe upgrade --install devops-info-lab12 solution\k8s\devops-info-service `
  --namespace devops-lab12 `
  --set partOf=devops-lab12 `
  --set service.type=ClusterIP `
  --set image.repository=devops-info-service `
  --set image.tag=lab12 `
  --set image.pullPolicy=IfNotPresent `
  --set secret.data.username=lab12-user `
  --set secret.data.password=Lab12-Password-123 `
  --wait --timeout 10m
```

Observed output:

```text
NAME: devops-info-lab12
NAMESPACE: devops-lab12
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

## 7. ConfigMap Vs Secret

Use ConfigMap when:

- data is not sensitive
- values can safely be exposed to app operators and logs
- examples: app mode, log level, feature flags, non-secret JSON config

Use Secret when:

- data is sensitive
- examples: passwords, API tokens, credentials, certificates

Key differences:

- `ConfigMap` is for plain configuration
- `Secret` is for confidential data
- both are Kubernetes objects, but only `Secret` is intended for sensitive values
- Secrets should still be protected with RBAC and encryption at rest because base64 encoding is not encryption

## 8. Bonus - ConfigMap Hot Reload

### 8.1 Default mounted-file update behavior

Method:

- updated the file ConfigMap in-place
- watched `/config/config.json` from the running pod
- measured when the new content became visible without restarting the pod

Observed result:

```json
{
  "pod": "devops-info-lab12-devops-info-service-558bdb6db6-7blks",
  "update_visible": true,
  "elapsed_seconds": 21.4
}
```

Interpretation:

- the running pod saw the updated file automatically
- the change was not instantaneous
- in this run, propagation took about `21.4` seconds

### 8.2 Why `subPath` was avoided

`subPath` mounts do not receive ConfigMap updates because Kubernetes places a one-time file projection at container start instead of the symlink-based directory projection used by regular ConfigMap volume mounts.

Practical rule:

- use full directory mounts when you want file updates to propagate
- avoid `subPath` for hot-reload scenarios

### 8.3 Chosen reload approach

Implemented approach:

- checksum annotation on the Deployment pod template
- whenever `templates/configmap.yaml` changes during `helm upgrade`, the pod template hash changes
- Deployment rolls out a new pod automatically

Implemented annotation:

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

### 8.4 Rollout proof on Helm upgrade

Upgrade verification:

```json
{
  "old_pod": "devops-info-lab12-devops-info-service-7689fb954c-nczgw",
  "new_pod": "devops-info-lab12-devops-info-service-674f95df99-k2c2g",
  "restarted": true,
  "log_level_after_upgrade": "trace"
}
```

Conclusion:

- changing Helm-managed ConfigMap content through `helm upgrade` triggered a new pod
- the new pod picked up the updated environment configuration
- this is a practical reload strategy when the application does not watch files itself

## 9. System Changes And Rollback

### 9.1 What changed on the local system

Performed changes:

- built local Docker image `devops-info-service:lab12`
- started local Docker Compose stack in `solution/app_python`
- started local `minikube`
- created namespace `devops-lab12`
- loaded the local image into Minikube
- installed Helm release `devops-info-lab12`

### 9.2 Rollback commands

Remove local Docker test stack:

```powershell
cd solution/app_python
docker compose down -v
Remove-Item -Recurse -Force .\data
```

Remove Lab 12 Kubernetes resources:

```powershell
.\helm.exe uninstall devops-info-lab12 -n devops-lab12
.\kubectl.exe delete namespace devops-lab12
```

Stop local Minikube cluster:

```powershell
minikube stop
```

Delete the whole local Minikube cluster:

```powershell
minikube delete
```

## 10. Conclusion

The lab objective was completed by externalizing application configuration through Kubernetes ConfigMaps, persisting the visits counter on a PVC-backed volume, and proving that data survives pod replacement. The chart now mounts `config.json` as a file, injects environment configuration through `envFrom`, stores visits in `/data/visits`, and uses checksum annotations to trigger controlled rollouts when Helm-managed configuration changes.
