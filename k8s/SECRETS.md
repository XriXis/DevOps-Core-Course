# LAB11 - Kubernetes Secrets And HashiCorp Vault

## 1. Overview

This lab extends the Helm chart from Lab 10 with two secret-management layers:

- native Kubernetes `Secret` objects for simple secret injection through environment variables
- HashiCorp Vault with Kubernetes authentication and Vault Agent Injector for file-based secret delivery

Implementation targets:

- keep real secrets out of Git
- make Kubernetes-native secret consumption reproducible through Helm
- demonstrate why base64 encoding is not encryption
- prove Vault sidecar injection with real CLI evidence
- keep the chart DRY with named templates in `_helpers.tpl`

Updated chart scope:

```text
solution/k8s/devops-info-service/
  values.yaml
  templates/
    _helpers.tpl
    deployment.yaml
    secret.yaml
    serviceaccount.yaml
```

## 2. Kubernetes Secrets Fundamentals

### 2.1 Secret creation

Command used:

```powershell
.\kubectl.exe create secret generic app-credentials -n devops-lab11 `
  --from-literal=username=demo-user `
  --from-literal=password='S3cret!42'
```

Observed output:

```text
secret/app-credentials created
```

### 2.2 Secret inspection

Command:

```powershell
.\kubectl.exe get secret app-credentials -n devops-lab11 -o yaml
```

Observed output:

```yaml
apiVersion: v1
data:
  password: UzNjcmV0ITQy
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T18:29:28Z"
  name: app-credentials
  namespace: devops-lab11
  resourceVersion: "61935"
  uid: 38b79b3c-01df-4cec-81d8-5dc007be76e0
type: Opaque
```

### 2.3 Base64 decoding proof

Commands:

```powershell
$secret = .\kubectl.exe get secret app-credentials -n devops-lab11 -o json | ConvertFrom-Json
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($secret.data.username))
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($secret.data.password))
```

Observed output:

```text
demo-user
S3cret!42
```

### 2.4 Encoding vs encryption

Base64 is only a transport-safe representation of bytes. It is reversible without a key, so it does not provide confidentiality.

Encryption requires a cryptographic process and a key. Without the key, the stored data should remain unreadable.

Practical conclusion:

- Kubernetes `Secret.data` is base64-encoded
- base64 does not protect the secret from anyone who can read the object
- access control and at-rest encryption are separate security layers

### 2.5 Security implications

Important points:

- Kubernetes Secrets are not meaningfully protected by base64 alone
- if etcd encryption at rest is not enabled, secret values are stored in etcd in a form that cluster administrators or backups can recover easily
- RBAC limits who can read the Secret through the Kubernetes API, but RBAC does not encrypt the stored data

What is etcd encryption:

- Kubernetes can encrypt selected resources before writing them to etcd
- Secrets are the most common resource type to protect this way
- this is configured by the cluster administrator through an encryption provider config on the API server

When to enable etcd encryption:

- always for any cluster that stores real credentials, tokens, database passwords, or certificates
- especially when etcd backups are retained outside the cluster
- especially in shared, long-lived, or production environments

## 3. Helm Secret Integration

### 3.1 Chart changes

Implemented changes:

- added `templates/secret.yaml` for chart-managed Kubernetes Secrets
- added `templates/serviceaccount.yaml` for Vault role binding
- updated `templates/deployment.yaml` to:
  - consume the Secret via `envFrom.secretRef`
  - use resource requests and limits from values
  - attach Vault annotations when enabled
- added named templates in [`solution/k8s/devops-info-service/templates/_helpers.tpl`](c:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/k8s/devops-info-service/templates/_helpers.tpl):
  - `devops-info-service.envVars`
  - `devops-info-service.secretName`
  - `devops-info-service.serviceAccountName`
  - `devops-info-service.vaultAnnotations`

### 3.2 Values strategy

The chart keeps only placeholders in Git:

```yaml
secret:
  create: true
  type: Opaque
  data:
    username: "change-me-user"
    password: "change-me-password"
```

Real values were injected only at deploy time:

```powershell
.\helm.exe install devops-info-secrets solution\k8s\devops-info-service `
  --namespace devops-lab11 `
  --set partOf=devops-lab11 `
  --set service.type=ClusterIP `
  --set secret.data.username=lab11-user `
  --set secret.data.password=Lab11-Password-123 `
  --wait --wait-for-jobs --timeout 5m
```

Observed output:

```text
NAME: devops-info-secrets
NAMESPACE: devops-lab11
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### 3.3 Deployment verification

Command:

```powershell
.\kubectl.exe get all -n devops-lab11
```

Observed output:

```text
NAME                                                           READY   STATUS    RESTARTS   AGE
pod/devops-info-secrets-devops-info-service-84797dff4d-62qct   1/1     Running   0          74s
pod/devops-info-secrets-devops-info-service-84797dff4d-c8gnv   1/1     Running   0          74s
pod/devops-info-secrets-devops-info-service-84797dff4d-ptlrb   1/1     Running   0          74s

NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/devops-info-secrets-devops-info-service   ClusterIP   10.109.100.33   <none>        80/TCP    74s

NAME                                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-secrets-devops-info-service   3/3     3            3           74s
```

### 3.4 Secret injection into environment variables

Command:

```powershell
$pod = .\kubectl.exe get pods -n devops-lab11 `
  -l app.kubernetes.io/instance=devops-info-secrets,app.kubernetes.io/name=devops-info-service `
  -o jsonpath='{.items[0].metadata.name}'

.\kubectl.exe exec -n devops-lab11 $pod -- /bin/sh -c `
  'printenv | sort | grep username; printenv | sort | grep password; printenv | sort | grep HOST; printenv | sort | grep PORT; printenv | sort | grep DEBUG; printenv | sort | grep RELEASE_VERSION'
```

Observed output:

```text
username=lab11-user
password=Lab11-Password-123
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_SERVICE_HOST=10.109.100.33
HOST=0.0.0.0
HOSTNAME=devops-info-secrets-devops-info-service-84797dff4d-62qct
KUBERNETES_SERVICE_HOST=10.96.0.1
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_PORT=tcp://10.109.100.33:80
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_PORT_80_TCP=tcp://10.109.100.33:80
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_PORT_80_TCP_ADDR=10.109.100.33
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_PORT_80_TCP_PORT=80
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_PORT_80_TCP_PROTO=tcp
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_SERVICE_PORT=80
DEVOPS_INFO_SECRETS_DEVOPS_INFO_SERVICE_SERVICE_PORT_HTTP=80
KUBERNETES_PORT=tcp://10.96.0.1:443
KUBERNETES_PORT_443_TCP=tcp://10.96.0.1:443
KUBERNETES_PORT_443_TCP_ADDR=10.96.0.1
KUBERNETES_PORT_443_TCP_PORT=443
KUBERNETES_PORT_443_TCP_PROTO=tcp
KUBERNETES_SERVICE_PORT=443
KUBERNETES_SERVICE_PORT_HTTPS=443
PORT=5000
DEBUG=false
RELEASE_VERSION=v1
```

### 3.5 Secrets are not printed by `kubectl describe pod`

Command:

```powershell
.\kubectl.exe describe deployment devops-info-secrets-devops-info-service -n devops-lab11
```

Observed excerpt:

```text
Environment Variables from:
  devops-info-secrets-devops-info-service-secret  Secret  Optional: false
Environment:
  HOST:             0.0.0.0
  PORT:             5000
  DEBUG:            false
  RELEASE_VERSION:  v1
```

This proves the pod spec references the Secret object, but the actual secret values are not printed in the `describe` output.

## 4. Resource Management

### 4.1 Implemented configuration

Current chart defaults:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

Runtime verification:

```text
Limits:
  cpu:     200m
  memory:  256Mi
Requests:
  cpu:      100m
  memory:   128Mi
```

### 4.2 Requests vs limits

Requests:

- define the minimum resources the scheduler reserves for the container
- affect pod placement and baseline QoS

Limits:

- define the maximum resources the container is allowed to consume
- CPU is throttled above the limit
- memory overuse can cause OOM termination

### 4.3 Why these values were chosen

- `100m / 128Mi` is sufficient for a small FastAPI service with health checks in Minikube
- `200m / 256Mi` leaves some burst room without letting the pod monopolize the single-node lab cluster
- the values match the light-weight nature of the app and remain easy to scale up in `values-prod.yaml`

## 5. HashiCorp Vault Integration

### 5.1 Installation

Commands:

```powershell
.\helm.exe repo add hashicorp https://helm.releases.hashicorp.com
.\helm.exe repo update
.\kubectl.exe create namespace vault
.\helm.exe install vault hashicorp/vault `
  --namespace vault `
  --set server.dev.enabled=true `
  --set injector.enabled=true `
  --wait --timeout 10m
```

Observed output:

```text
NAME: vault
NAMESPACE: vault
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### 5.2 Vault pod verification

Command:

```powershell
.\kubectl.exe get pods -n vault -o wide
```

Observed output:

```text
NAME                                   READY   STATUS    RESTARTS   AGE   IP             NODE       NOMINATED NODE   READINESS GATES
vault-0                                1/1     Running   0          21m   10.244.0.100   minikube   <none>           <none>
vault-agent-injector-8c76487db-5n2gw   1/1     Running   0          21m   10.244.0.99    minikube   <none>           <none>
```

### 5.3 Vault configuration

Vault status and enabled secret engines:

```powershell
.\kubectl.exe exec -n vault vault-0 -- /bin/sh -c "vault status && echo --- && vault secrets list -detailed"
```

Observed excerpt:

```text
Initialized     true
Sealed          false
Version         1.21.2
Storage Type    inmem
---
Path      Plugin  Options
secret/   kv      map[version:2]
```

Application secret written to Vault:

```powershell
vault kv put secret/devops-info-service/config username="vault-user" password="Vault-Password-456"
```

Observed output:

```text
============= Secret Path =============
secret/data/devops-info-service/config

======= Metadata =======
version            1
```

Readback proof:

```powershell
vault kv get secret/devops-info-service/config
```

Observed output:

```text
====== Data ======
Key         Value
---         -----
password    Vault-Password-456
username    vault-user
```

### 5.4 Kubernetes auth configuration

RBAC required for token review:

```powershell
.\kubectl.exe create clusterrolebinding vault-token-reviewer `
  --clusterrole=system:auth-delegator `
  --serviceaccount=vault:vault
```

Observed output:

```text
clusterrolebinding.rbac.authorization.k8s.io/vault-token-reviewer created
```

Auth config verification:

```powershell
.\kubectl.exe exec -n vault vault-0 -- /bin/sh -c "vault read auth/kubernetes/config"
```

Observed output excerpt:

```text
disable_iss_validation    true
kubernetes_host           https://10.96.0.1:443
token_reviewer_jwt_set    true
```

Policy used for the app:

```hcl
path "secret/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Policy verification:

```powershell
vault policy read devops-info-service
```

Observed output:

```hcl
path "secret/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Role verification:

```powershell
vault read auth/kubernetes/role/devops-info-service
```

Observed sanitized output:

```text
bound_service_account_names                 [devops-info-secrets-devops-info-service]
bound_service_account_namespaces            [devops-lab11]
policies                                    [devops-info-service]
token_ttl                                   24h
ttl                                         24h
```

### 5.5 Vault Agent injection in the application chart

Helm upgrade used:

```powershell
.\helm.exe upgrade devops-info-secrets solution\k8s\devops-info-service `
  --namespace devops-lab11 `
  --set partOf=devops-lab11 `
  --set service.type=ClusterIP `
  --set secret.data.username=lab11-user `
  --set secret.data.password=Lab11-Password-123 `
  --set vault.enabled=true `
  --set vault.role=devops-info-service `
  --set vault.secretPath=secret/data/devops-info-service/config `
  --set vault.authPath=auth/kubernetes `
  --wait --timeout 10m
```

Observed output:

```text
Release "devops-info-secrets" has been upgraded. Happy Helming!
NAME: devops-info-secrets
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
```

Deployment verification:

```powershell
.\kubectl.exe get pods -n devops-lab11 -o wide
```

Observed output:

```text
NAME                                                      READY   STATUS    RESTARTS   AGE   IP             NODE       NOMINATED NODE   READINESS GATES
devops-info-secrets-devops-info-service-6b7c4899c-5jdx6   2/2     Running   0          55s   10.244.0.103   minikube   <none>           <none>
devops-info-secrets-devops-info-service-6b7c4899c-9w56d   2/2     Running   0          41s   10.244.0.104   minikube   <none>           <none>
devops-info-secrets-devops-info-service-6b7c4899c-lbpvn   2/2     Running   0          26s   10.244.0.105   minikube   <none>           <none>
```

Pod proof showing the init container and sidecar:

```text
Init Containers:
  vault-agent-init:
    State:          Terminated
      Reason:       Completed
      Exit Code:    0

Containers:
  devops-info-service:
    State:          Running
    Ready:          True
  vault-agent:
    State:          Running
    Ready:          True
```

### 5.6 File injection proof

Command:

```powershell
$pod = .\kubectl.exe get pods -n devops-lab11 `
  -l app.kubernetes.io/instance=devops-info-secrets,app.kubernetes.io/name=devops-info-service `
  -o jsonpath='{.items[0].metadata.name}'

.\kubectl.exe exec -n devops-lab11 $pod -c devops-info-service -- /bin/sh -c `
  'ls -la /vault/secrets && echo --- && cat /vault/secrets/app.env && echo --- && sed -n "1,20p" /vault/secrets/app-secrets.txt'
```

Observed output:

```text
total 12
drwxrwsrwt    2 root     appgroup        80 Apr  9 18:52 .
drwxr-xr-x    3 root     root          4096 Apr  9 18:52 ..
-rw-r--r--    1 100      appgroup       181 Apr  9 18:52 app-secrets.txt
-rw-r--r--    1 100      appgroup        56 Apr  9 18:52 app.env
---
APP_USERNAME=vault-user
APP_PASSWORD=Vault-Password-456
---
data: map[password:Vault-Password-456 username:vault-user]
metadata: map[created_time:2026-04-09T18:34:34.521026522Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

This confirms:

- the injector created files under `/vault/secrets`
- `app.env` was rendered from a custom template
- a second file was injected from the same Vault path

## 6. Sidecar Injection Pattern

How it works in this deployment:

- the mutating webhook sees Vault annotations on the pod template
- it injects `vault-agent-init` and `vault-agent`
- `vault-agent-init` authenticates to Vault before the main container starts
- the template engine renders secret files into the shared in-memory volume at `/vault/secrets`
- the sidecar keeps running to renew the token and refresh templates when leased data changes

Why this is useful:

- the application container does not need to call Vault directly
- the secret never has to be baked into the container image
- the app can read files from a local path instead of implementing Vault client logic

## 7. Bonus - Vault Agent Templates And DRY Helm

### 7.1 Template annotation

The chart implements a custom template annotation through [`solution/k8s/devops-info-service/templates/_helpers.tpl`](c:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/k8s/devops-info-service/templates/_helpers.tpl):

```yaml
vault.hashicorp.com/agent-inject-template-app.env: |
  {{- with secret "secret/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end }}
```

Result:

- multiple Vault keys are rendered into one `.env`-style file
- the app gets a format that is immediately usable by shell tooling or config loaders

### 7.2 Named template for common environment variables

Implemented named template:

```yaml
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: DEBUG
  value: {{ .Values.env.debug | quote }}
- name: RELEASE_VERSION
  value: {{ .Values.env.releaseVersion | quote }}
{{- end -}}
```

Why this matters:

- common env vars are defined in one place
- the Deployment template stays shorter
- future reuse across workload templates becomes simpler

### 7.3 Secret refresh behavior

How Vault Agent handles updates:

- the sidecar keeps the Vault token valid
- for rotating or leased secrets, the agent re-renders templates when data changes or leases renew
- applications that read from files can reload configuration after file change detection or restart hooks

About `vault.hashicorp.com/agent-inject-command`:

- this annotation runs a command after the agent writes or refreshes an injected file
- common uses:
  - reload nginx or another proxy
  - send `SIGHUP` to an application
  - adjust file permissions
- the chart exposes this as `vault.injectCommand`; it is intentionally optional and was left empty in the validated run to keep the demo minimal

## 8. Security Analysis

### 8.1 Kubernetes Secrets vs Vault

Kubernetes Secrets:

- simple and built into the platform
- good for basic apps or low-complexity clusters
- still stored in the cluster control plane
- often exposed through Helm values, manifests, or backup workflows if teams are careless

Vault:

- purpose-built for secret management
- supports fine-grained policies, auditability, and dynamic secrets
- keeps the source of truth outside application manifests
- scales better for production-grade secret rotation and separation of duties

### 8.2 When to use each approach

Use Kubernetes Secrets when:

- the environment is small and controlled
- secret lifecycle is simple
- you need the fastest native setup for local or educational workloads

Use Vault when:

- multiple teams or apps need controlled secret access
- rotation and audit trails matter
- you want short-lived credentials or externalized secret ownership

### 8.3 Production recommendations

- enable etcd encryption at rest for Secrets
- restrict secret access through RBAC
- avoid passing real secrets through committed Helm values files
- prefer external secret managers for production
- avoid Vault dev mode outside learning environments
- audit who can read Helm release metadata because Helm itself can expose values used at deploy time

## 9. Validation Summary

What was completed:

- Kubernetes Secret created imperatively and decoded
- Helm chart extended with `Secret` and `ServiceAccount`
- application consumes Kubernetes Secret through `envFrom`
- resource requests and limits remain configurable through values
- Vault installed with injector enabled
- KV v2 secret created and read back
- Kubernetes auth method configured
- Vault policy and role created
- Vault Agent injection verified with real files inside the pod
- bonus template rendering and named Helm templates implemented

## 10. Operations And Rollback

### 10.1 What changed on the system

Local cluster changes performed:

- started local `minikube`
- created namespace `devops-lab11`
- created namespace `vault`
- installed Helm release `devops-info-secrets`
- installed Helm release `vault`
- created cluster-wide RBAC binding `vault-token-reviewer`

### 10.2 Rollback commands

Remove Lab 11 application resources:

```powershell
.\helm.exe uninstall devops-info-secrets -n devops-lab11
.\kubectl.exe delete secret app-credentials -n devops-lab11
.\kubectl.exe delete namespace devops-lab11
```

Remove Vault resources:

```powershell
.\helm.exe uninstall vault -n vault
.\kubectl.exe delete namespace vault
.\kubectl.exe delete clusterrolebinding vault-token-reviewer
```

Stop the local cluster without deleting it:

```powershell
minikube stop
```

Delete the entire local cluster:

```powershell
minikube delete
```

## 11. Conclusion

The lab objective was completed by implementing both native Kubernetes Secrets and HashiCorp Vault integration in the existing Helm-based Kubernetes deployment. The chart now supports secure secret injection through `envFrom`, Vault-authenticated sidecar injection through annotations, custom Vault Agent template rendering for `.env` files, and DRY named templates for common environment variables. Real CLI evidence confirms that the app can consume both Kubernetes-managed and Vault-managed secrets in a working Minikube environment.
