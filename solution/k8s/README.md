# Lab 9 - Kubernetes Fundamentals

## Architecture Overview

Chosen local cluster: `minikube`.

Why `minikube`:
- Simple single-node local Kubernetes environment for manual labs.
- Built-in ingress addon makes the bonus task straightforward.
- Works well with `kubectl`, `port-forward`, and direct cluster inspection.

Namespace used for all resources: `devops-lab9`.

Architecture:

```text
Local client
    |
    +--> NodePort service devops-info-service:80
    |      -> Deployment devops-info-service (3 FastAPI Pods)
    |
    +--> Ingress local.example.com
           +--> /app1 -> Service devops-info-service -> FastAPI Pods
           +--> /app2 -> Service devops-info-service-rust -> Actix-web Pods
```

Networking flow:
- Required part uses `NodePort` for the main application.
- Bonus part uses `Ingress` with path-based routing and TLS termination.

Resource allocation strategy:
- Each container requests `100m CPU` and `128Mi memory`.
- Each container is limited to `200m CPU` and `256Mi memory`.
- These values are small but realistic for lightweight local HTTP services.

Security hardening:
- Images run as non-root users.
- Kubernetes pod security context enforces numeric `runAsUser: 122`, `runAsGroup: 122`, `fsGroup: 122`.
- `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, dropped Linux capabilities, and `RuntimeDefault` seccomp profile are enabled.
- `automountServiceAccountToken: false` is set because these pods do not need Kubernetes API access.

## Manifest Files

Files:
- `k8s/namespace.yml` - dedicated namespace for resource isolation.
- `k8s/deployment.yml` - main FastAPI application deployment.
- `k8s/service.yml` - `NodePort` service for the main application.
- `k8s/rust-deployment.yml` - second application deployment for the bonus task.
- `k8s/rust-service.yml` - internal service for the Rust application.
- `k8s/ingress.yml` - Ingress with TLS and path-based routing.

Key configuration choices:
- `replicas: 3` for the main app to satisfy the mandatory HA requirement.
- `RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0` to preserve availability during rollout.
- `readinessProbe` and `livenessProbe` both use `/health` because both applications expose a fast health endpoint.
- `imagePullPolicy: IfNotPresent` avoids unnecessary pulls in local Minikube runs.
- Bonus Rust service is exposed only with `ClusterIP` because external access is handled by the Ingress layer.

## Cluster Setup Evidence

### `minikube status`

```text
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

### `kubectl cluster-info`

```text
Kubernetes control plane is running at https://127.0.0.1:56426
CoreDNS is running at https://127.0.0.1:56426/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

### `kubectl get nodes -o wide`

```text
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION                     CONTAINER-RUNTIME
minikube   Ready    control-plane   80m   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.6.87.2-microsoft-standard-WSL2   docker://29.2.1
```

## Deployment Evidence

### `kubectl get all -n devops-lab9`

```text
NAME                                           READY   STATUS    RESTARTS   AGE
pod/devops-info-service-697bff94db-phcx7       1/1     Running   0          59s
pod/devops-info-service-697bff94db-qzfz6       1/1     Running   0          72s
pod/devops-info-service-697bff94db-wz6pf       1/1     Running   0          46s
pod/devops-info-service-rust-9fdc4dcd5-887cn   1/1     Running   0          4m24s
pod/devops-info-service-rust-9fdc4dcd5-j7q2b   1/1     Running   0          4m33s

NAME                               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service        NodePort    10.104.9.18     <none>        80:30080/TCP   76m
service/devops-info-service-rust   ClusterIP   10.107.53.127   <none>        80/TCP         76m

NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service        3/3     3            3           76m
deployment.apps/devops-info-service-rust   2/2     2            2           76m

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-697bff94db        3         3         3       4m33s
replicaset.apps/devops-info-service-6cb85bc657        0         0         0       62m
replicaset.apps/devops-info-service-7447f566f8        0         0         0       68m
replicaset.apps/devops-info-service-7b69b874c9        0         0         0       76m
replicaset.apps/devops-info-service-cd47f9df9         0         0         0       2m20s
replicaset.apps/devops-info-service-rust-5474d5f6c9   0         0         0       68m
replicaset.apps/devops-info-service-rust-58b8cc6584   0         0         0       76m
replicaset.apps/devops-info-service-rust-9fdc4dcd5    2         2         2       4m33s
```

### `kubectl get pods,svc -n devops-lab9 -o wide`

```text
NAME                                           READY   STATUS    RESTARTS   AGE     IP            NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-697bff94db-phcx7       1/1     Running   0          59s     10.244.0.45   minikube   <none>           <none>
pod/devops-info-service-697bff94db-qzfz6       1/1     Running   0          72s     10.244.0.44   minikube   <none>           <none>
pod/devops-info-service-697bff94db-wz6pf       1/1     Running   0          46s     10.244.0.46   minikube   <none>           <none>
pod/devops-info-service-rust-9fdc4dcd5-887cn   1/1     Running   0          4m24s   10.244.0.34   minikube   <none>           <none>
pod/devops-info-service-rust-9fdc4dcd5-j7q2b   1/1     Running   0          4m33s   10.244.0.32   minikube   <none>           <none>

NAME                               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-service        NodePort    10.104.9.18     <none>        80:30080/TCP   76m   app=devops-info-service
service/devops-info-service-rust   ClusterIP   10.107.53.127   <none>        80/TCP         76m   app=devops-info-service-rust
```

### `kubectl describe deployment devops-info-service -n devops-lab9`

```text
Name:                   devops-info-service
Namespace:              devops-lab9
CreationTimestamp:      Fri, 27 Mar 2026 00:06:46 +0300
Labels:                 app=devops-info-service
                        app.kubernetes.io/name=devops-info-service
                        app.kubernetes.io/part-of=devops-lab9
Annotations:            deployment.kubernetes.io/revision: 7
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
           app.kubernetes.io/name=devops-info-service
           app.kubernetes.io/part-of=devops-lab9
  Containers:
   devops-info-service:
    Image:      xrixis/devops-i-lobazov:0.1.0
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:http/health delay=15s timeout=2s period=10s #success=1 #failure=3
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
    Environment:
      HOST:             0.0.0.0
      PORT:             5000
      DEBUG:            false
      RELEASE_VERSION:  v1
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
```

### Runtime security verification

The image-level user and Kubernetes security context were verified at runtime with:

```powershell
kubectl exec -n devops-lab9 deploy/devops-info-service -- id
```

Observed output:

```text
uid=122(appuser) gid=122(appgroup) groups=122(appgroup),122(appgroup)
```

### Service verification

`NodePort` is configured as required. For deterministic verification on the current Windows setup, service requests were executed through `kubectl port-forward`.

Commands used:

```powershell
kubectl port-forward service/devops-info-service 8080:80 -n devops-lab9
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/
```

`/health` output:

```json
{"status":"healthy","timestamp":"2026-03-26 22:23:48","uptime_seconds":96}
```

`/` output:

```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-697bff94db-qzfz6","platform":"Linux","platform_version":"6.6.87.2-microsoft-standard-WSL2","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":96,"uptime_human":"0 hours, 1 minutes","current_time":"2026-03-26 22:23:48","timezone":""},"request":{"client_ip":"127.0.0.1","user_agent":"Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.26100.7920","method":"GET","path":"/"},"endpoints":[{"path":"/openapi.json","method":"HEAD","description":""},{"path":"/openapi.json","method":"GET","description":""},{"path":"/docs","method":"HEAD","description":""},{"path":"/docs","method":"GET","description":""},{"path":"/docs/oauth2-redirect","method":"HEAD","description":""},{"path":"/docs/oauth2-redirect","method":"GET","description":""},{"path":"/redoc","method":"HEAD","description":""},{"path":"/redoc","method":"GET","description":""},{"path":"/","method":"GET","description":"System and service info about the server"},{"path":"/health","method":"GET","description":"Service health-chek"}]}
```

## Operations Performed

### Initial deployment

Commands:

```powershell
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/rust-deployment.yml
kubectl apply -f k8s/rust-service.yml
kubectl rollout status deployment/devops-info-service -n devops-lab9
kubectl rollout status deployment/devops-info-service-rust -n devops-lab9
```

### Scaling demonstration

Commands:

```powershell
kubectl scale deployment/devops-info-service -n devops-lab9 --replicas=5
kubectl rollout status deployment/devops-info-service -n devops-lab9
kubectl get pods -n devops-lab9 -l app=devops-info-service -o wide
```

Observed output:

```text
deployment.apps/devops-info-service scaled
Waiting for deployment "devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
deployment "devops-info-service" successfully rolled out
```

After scaling, five replicas were running successfully.

### Rolling update demonstration

Update method:
- Changed deployment configuration by updating `RELEASE_VERSION` from `v1` to `v2`.
- For the live demo this was done with `kubectl set env`, while the baseline manifest was later restored to `v1`.
- The application does not expose this variable in HTTP responses, so the update was validated through Kubernetes rollout state and revision history.

Commands:

```powershell
kubectl set env deployment/devops-info-service -n devops-lab9 RELEASE_VERSION=v2
kubectl rollout status deployment/devops-info-service -n devops-lab9
kubectl rollout history deployment/devops-info-service -n devops-lab9
```

Observed rollout output:

```text
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

Zero-downtime verification:
- During the rollout, 15 consecutive requests were sent to `/health` through the service.
- All 15 requests returned `HTTP 200`.

Observed request table:

```text
Attempt StatusCode
------- ----------
1       200
2       200
3       200
4       200
5       200
6       200
7       200
8       200
9       200
10      200
11      200
12      200
13      200
14      200
15      200
```

### Rollback demonstration

Commands:

```powershell
kubectl rollout undo deployment/devops-info-service -n devops-lab9
kubectl rollout status deployment/devops-info-service -n devops-lab9
kubectl scale deployment/devops-info-service -n devops-lab9 --replicas=3
kubectl rollout status deployment/devops-info-service -n devops-lab9
kubectl rollout history deployment/devops-info-service -n devops-lab9
```

Observed history after rollback:

```text
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
6         <none>
7         <none>
```

After the rollback demo, the deployment was returned to the baseline state:
- `replicas: 3`
- `RELEASE_VERSION: v1`

## Bonus - Ingress With TLS

### Bonus deployment scope

Second application:
- Rust Actix-web service deployed with its own Deployment and Service.

Ingress controller setup:

```powershell
minikube addons enable ingress
kubectl get pods -n ingress-nginx
```

Controller verification:

```text
NAME                                        READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-77nmn        0/1     Completed   0          59m
ingress-nginx-admission-patch-spjlt         0/1     Completed   1          59m
ingress-nginx-controller-596f8778bc-62z2s   1/1     Running     0          59m
```

### TLS certificate generation

TLS certificate and key are generated locally and are not stored in the repository. The `k8s/certs/` directory is ignored by Git.

Commands used:

```powershell
New-Item -ItemType Directory -Force k8s/certs
"C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout k8s/certs/local.example.com.key `
  -out k8s/certs/local.example.com.crt `
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls devops-info-ingress-tls -n devops-lab9 `
  --key k8s/certs/local.example.com.key `
  --cert k8s/certs/local.example.com.crt
```

TLS secret verification:

```text
NAME                      TYPE                DATA   AGE
devops-info-ingress-tls   kubernetes.io/tls   2      57m
```

### Ingress resource

Applied with:

```powershell
kubectl apply -f k8s/ingress.yml
kubectl get ingress -n devops-lab9 -o wide
```

Observed output:

```text
NAME                  CLASS   HOSTS               ADDRESS        PORTS     AGE
devops-info-ingress   nginx   local.example.com   192.168.49.2   80, 443   57m
```

Routing rules:
- `/app1` -> `devops-info-service`
- `/app2` -> `devops-info-service-rust`

### HTTPS verification

Commands used:

```powershell
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8443:443
curl -ksS --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app1/
curl -ksS --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app2/
```

`/app1` response:

```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-697bff94db-wz6pf","platform":"Linux","platform_version":"6.6.87.2-microsoft-standard-WSL2","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":72,"uptime_human":"0 hours, 1 minutes","current_time":"2026-03-26 22:23:48","timezone":""},"request":{"client_ip":"10.244.0.31","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/openapi.json","method":"GET","description":""},{"path":"/openapi.json","method":"HEAD","description":""},{"path":"/docs","method":"GET","description":""},{"path":"/docs","method":"HEAD","description":""},{"path":"/docs/oauth2-redirect","method":"GET","description":""},{"path":"/docs/oauth2-redirect","method":"HEAD","description":""},{"path":"/redoc","method":"GET","description":""},{"path":"/redoc","method":"HEAD","description":""},{"path":"/","method":"GET","description":"System and service info about the server"},{"path":"/health","method":"GET","description":"Service health-chek"}]}
```

`/app2` response:

```json
{"endpoints":[{"description":"System and service info about the server","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.244.0.31","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-03-26 22:23:48","timezone":"UTC","uptime_human":"0 hours, 5 minutes","uptime_seconds":307},"service":{"description":"DevOps course info service","framework":"Actix-web","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"devops-info-service-rust-9fdc4dcd5-j7q2b","platform":"Linux","platform_version":"6.6.87.2-microsoft-standard-WSL2","rust_version":"unknown"}}
```

Why Ingress is better than direct NodePort services:
- One external entry point for multiple applications.
- Centralized TLS termination.
- URL/path-based routing.
- Closer to real production traffic management than exposing each service separately.

## Production Considerations

Health checks:
- `/health` is used for both readiness and liveness because it is fast and deterministic.
- Readiness removes pods from service endpoints before they receive traffic.
- Liveness enables Kubernetes to restart a stuck container automatically.

Resource limits rationale:
- Requests are high enough for lightweight FastAPI and Actix-web services in a local cluster.
- Limits prevent one pod from consuming excessive resources on the Minikube node.

Security considerations:
- Numeric UID/GID in the pod security context eliminate ambiguity around non-root enforcement.
- Service account tokens are not mounted because the applications do not need cluster credentials.
- TLS key material is generated locally and excluded from version control.

Production improvements:
- Use immutable CI-generated image tags for every deployment.
- Add `startupProbe` if application startup time becomes less predictable.
- Add `HorizontalPodAutoscaler`.
- Add `PodDisruptionBudget` and anti-affinity for multi-node environments.
- Move application configuration to `ConfigMaps` and sensitive values to `Secrets`.
- Add network policies and, for future traffic management, evaluate the Gateway API.

Monitoring and observability strategy:
- Scrape `/metrics` from the Python application.
- Build dashboards and alerts for latency, error rate, restart count, and readiness failures.
- Aggregate structured logs in Loki/Grafana.

## Challenges And Solutions

Issue encountered:
- Initial hardening relied on a named image user (`appuser`) while Kubernetes enforced `runAsNonRoot: true`.

Root cause:
- Kubernetes non-root validation is more reliable when the runtime identity is numeric and deterministic.
- Creating users without fixed IDs in the Docker image can produce environment-dependent UID/GID values, which makes the pod security context brittle.

Debug process:
- Used `kubectl describe pod ...` to read pod events.
- Verified the effective container UID with `kubectl exec ... -- id`.

Final solution:
- Updated both Docker images to create `appuser:appgroup` with fixed `UID/GID = 122`.
- Switched the container runtime user to `USER 122:122` in the Dockerfiles.
- Kept numeric `runAsUser`, `runAsGroup`, and `fsGroup` values in Kubernetes so the manifests and images use the same explicit identity contract.
- Retained container hardening with `allowPrivilegeEscalation: false`, dropped capabilities, and `RuntimeDefault` seccomp.

What I learned:
- Strong container security in Kubernetes should be explicit, deterministic, and runtime-verifiable.
- It is better to define the UID/GID contract in the image build itself than to depend on auto-assigned user IDs.
- Rollouts can be validated cleanly at the Kubernetes level even when the changed variable is not exposed by the application itself.
- Evidence in lab reports should be captured from one real run and kept internally consistent.
