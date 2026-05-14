# LAB10 - Helm Package Manager

## 1. Chart Overview

This lab converts the Kubernetes manifests from Lab 9 into reusable Helm charts and adds environment-specific configuration, lifecycle hooks, and a shared library chart for template reuse.

Helm value proposition for this project:

- one chart definition can be reused across `dev` and `prod`
- runtime settings move from hardcoded YAML into structured values files
- releases become versioned, upgradeable, and rollbackable
- hooks make install-time validation and smoke checks repeatable
- shared helpers eliminate duplicated naming and label logic across charts

Implemented chart layout:

```text
solution/k8s/
  HELM.md
  common-lib/
    Chart.yaml
    templates/_helpers.tpl
  devops-info-service/
    Chart.yaml
    values.yaml
    values-dev.yaml
    values-prod.yaml
    templates/
      _helpers.tpl
      deployment.yaml
      service.yaml
      ingress.yaml
      NOTES.txt
      hooks/
        pre-install-job.yaml
        post-install-job.yaml
  devops-info-service-rust/
    Chart.yaml
    values.yaml
    templates/
      _helpers.tpl
      deployment.yaml
      service.yaml
```

Key template responsibilities:

- `deployment.yaml`: parametrized Deployment with replicas, image, resources, probes, env vars, rolling update strategy, and security context.
- `service.yaml`: parametrized service type and ports, including optional `nodePort`.
- `ingress.yaml`: optional ingress for future reuse, disabled by default.
- `hooks/pre-install-job.yaml`: validates critical chart values before install.
- `hooks/post-install-job.yaml`: performs smoke-test HTTP call after install.
- `common-lib/templates/_helpers.tpl`: shared naming, labels, selector labels, probe rendering, and env list rendering helpers.

Values organization strategy:

- `values.yaml` contains stable defaults close to the original Lab 9 manifests.
- `values-dev.yaml` contains low-cost development overrides.
- `values-prod.yaml` contains higher replica/resource settings and `LoadBalancer` service mode.
- app-specific charts keep only app-specific settings while generic helper logic lives in `common-lib`.

## 2. Fundamentals And Setup

### Helm installation

Helm was installed as a local repository binary to avoid changing the global system `PATH`.

Command:

```powershell
.\helm.exe version
```

Observed output:

```text
version.BuildInfo{Version:"v4.0.1", GitCommit:"12500dd401faa7629f30ba5d5bff36287f3e94d3", GitTreeState:"clean", GoVersion:"go1.25.4", KubeClientVersion:"v1.34"}
```

### Cluster verification

Commands:

```powershell
.\kubectl.exe cluster-info
.\kubectl.exe get nodes -o wide
```

Observed output:

```text
Kubernetes control plane is running at https://127.0.0.1:55253
CoreDNS is running at https://127.0.0.1:55253/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

```text
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION                     CONTAINER-RUNTIME
minikube   Ready    control-plane   7d    v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.6.87.2-microsoft-standard-WSL2   docker://29.2.1
```

### Repository and public chart exploration

Commands:

```powershell
.\helm.exe repo add prometheus-community https://prometheus-community.github.io/helm-charts
.\helm.exe repo update
.\helm.exe show chart prometheus-community/prometheus
```

Observed output:

```text
"prometheus-community" has been added to your repositories
```

```text
name: prometheus
version: 28.15.0
type: application
appVersion: v3.11.0
description: Prometheus is a monitoring system and time series database.
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
```

## 3. Configuration Guide

### Important values

Main chart defaults in `solution/k8s/devops-info-service/values.yaml` expose:

- `replicaCount`
- `image.repository`, `image.tag`, `image.pullPolicy`
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`
- `resources.requests`, `resources.limits`
- `livenessProbe.*`
- `readinessProbe.*`
- `env[]`
- `podSecurityContext`
- `containerSecurityContext`
- `hooks.*`
- `ingress.*`

The chart deliberately keeps health checks active at all times. Probes are never commented out and remain configurable through values files.

### Environment-specific values

Development file: `solution/k8s/devops-info-service/values-dev.yaml`

- `replicaCount: 1`
- `image.tag: latest`
- `service.type: NodePort`
- `service.nodePort: 30081`
- reduced CPU and memory requests/limits
- faster probe timings

Production file: `solution/k8s/devops-info-service/values-prod.yaml`

- `replicaCount: 5`
- `image.tag: 0.1.0`
- `service.type: LoadBalancer`
- stronger CPU and memory requests/limits
- more conservative probe timings

### Commands used

Dependency refresh:

```powershell
.\helm.exe dependency update solution\k8s\devops-info-service
.\helm.exe dependency update solution\k8s\devops-info-service-rust
```

Validation:

```powershell
.\helm.exe lint solution\k8s\devops-info-service
.\helm.exe template test-main solution\k8s\devops-info-service --namespace devops-lab10
.\helm.exe install --dry-run --debug devops-info-dev solution\k8s\devops-info-service --namespace devops-lab10 --create-namespace -f solution\k8s\devops-info-service\values-dev.yaml
```

Install and upgrade:

```powershell
.\helm.exe install devops-info-dev solution\k8s\devops-info-service --namespace devops-lab10 --create-namespace -f solution\k8s\devops-info-service\values-dev.yaml --wait --wait-for-jobs --timeout 5m
.\helm.exe upgrade devops-info-dev solution\k8s\devops-info-service --namespace devops-lab10 -f solution\k8s\devops-info-service\values-prod.yaml --wait --timeout 5m
```

Bonus chart install:

```powershell
.\helm.exe install devops-info-rust solution\k8s\devops-info-service-rust --namespace devops-lab10 --wait --timeout 5m
```

### Dry-run verification

Observed output excerpt from `helm install --dry-run --debug`:

```text
NAME: devops-info-dev
NAMESPACE: devops-lab10
STATUS: pending-install
USER-SUPPLIED VALUES:
image:
  tag: latest
replicaCount: 1
service:
  nodePort: 30081
  type: NodePort
HOOKS:
# Source: devops-info-service/templates/hooks/post-install-job.yaml
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
MANIFEST:
# Source: devops-info-service/templates/service.yaml
# Source: devops-info-service/templates/deployment.yaml
```

This confirms that both hook resources and main Kubernetes resources render correctly before touching the cluster.

## 4. Hook Implementation

Implemented hooks:

- `pre-install`: a validation `Job` that checks required image values and prints the target image.
- `post-install`: a smoke-test `Job` that calls the service `/health` endpoint after deployment.

Execution order and weights:

- `pre-install` weight: `-5`
- `post-install` weight: `5`

Deletion policy:

- both hooks use `hook-succeeded`
- successful jobs are automatically removed after completion

Hook definitions stored by Helm:

```powershell
.\helm.exe get hooks devops-info-dev -n devops-lab10
```

Observed output excerpt:

```text
metadata:
  name: "devops-info-dev-devops-info-service-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": "hook-succeeded"
```

```text
metadata:
  name: "devops-info-dev-devops-info-service-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": "hook-succeeded"
```

Live hook execution evidence:

```powershell
.\kubectl.exe get jobs -n devops-lab10
.\kubectl.exe describe job devops-info-dev-devops-info-service-pre-install -n devops-lab10
.\kubectl.exe get events -n devops-lab10 --sort-by=.lastTimestamp
```

Observed output while the pre-install job was running:

```text
NAME                                              STATUS    COMPLETIONS   DURATION   AGE
devops-info-dev-devops-info-service-pre-install   Running   0/1           3s         3s
```

Observed `kubectl describe job` excerpt:

```text
Name:             devops-info-dev-devops-info-service-pre-install
Namespace:        devops-lab10
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: -5
Pods Statuses:    1 Active (0 Ready) / 0 Succeeded / 0 Failed
Command:
  sh
  -c
  test -n "xrixis/devops-i-lobazov" && test -n "latest" && sleep 5 && echo "Pre-install validation passed for release devops-info-dev" && echo "Image=xrixis/devops-i-lobazov:latest"
```

Observed events showing both hook jobs completed:

```text
SuccessfulCreate    job/devops-info-dev-devops-info-service-pre-install   Created pod: devops-info-dev-devops-info-service-pre-install-wkk89
Completed           job/devops-info-dev-devops-info-service-pre-install   Job completed
SuccessfulCreate    job/devops-info-dev-devops-info-service-post-install  Created pod: devops-info-dev-devops-info-service-post-install-px8bf
Completed           job/devops-info-dev-devops-info-service-post-install  Job completed
```

Deletion-policy verification:

```powershell
.\kubectl.exe get jobs -n devops-lab10
```

Observed output:

```text
No resources found in devops-lab10 namespace.
```

## 5. Installation Evidence

### Helm releases

Command:

```powershell
.\helm.exe list -n devops-lab10
```

Observed output:

```text
NAME             NAMESPACE    REVISION  UPDATED                               STATUS    CHART                          APP VERSION
devops-info-dev  devops-lab10 4         2026-04-03 00:23:33.4222804 +0300 MSK deployed  devops-info-service-0.1.0      0.1.0
devops-info-rust devops-lab10 1         2026-04-03 00:24:41.3352039 +0300 MSK deployed  devops-info-service-rust-0.1.0 0.1.0
```

### Deployed Kubernetes resources

Command:

```powershell
.\kubectl.exe get all -n devops-lab10
```

Observed output:

```text
NAME                                                             READY   STATUS    RESTARTS   AGE
pod/devops-info-dev-devops-info-service-5c95548dd6-b2pzm         1/1     Running   0          86s
pod/devops-info-dev-devops-info-service-5c95548dd6-m58dh         1/1     Running   0          61s
pod/devops-info-dev-devops-info-service-5c95548dd6-r2875         1/1     Running   0          50s
pod/devops-info-dev-devops-info-service-5c95548dd6-tckx2         1/1     Running   0          72s
pod/devops-info-dev-devops-info-service-5c95548dd6-wcr5x         1/1     Running   0          39s
pod/devops-info-rust-devops-info-service-rust-6fd97498db-59x2h   1/1     Running   0          18s
pod/devops-info-rust-devops-info-service-rust-6fd97498db-xfddf   1/1     Running   0          18s

NAME                                                TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-dev-devops-info-service         LoadBalancer   10.108.98.2     <pending>     80:30081/TCP   4m51s
service/devops-info-rust-devops-info-service-rust   ClusterIP      10.98.119.200   <none>        80/TCP         18s

NAME                                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-dev-devops-info-service         5/5     5            5           4m51s
deployment.apps/devops-info-rust-devops-info-service-rust   2/2     2            2           18s
```

### Deployment details

Command:

```powershell
.\kubectl.exe describe deployment devops-info-dev-devops-info-service -n devops-lab10
```

Observed output excerpt:

```text
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Image:      xrixis/devops-i-lobazov:0.1.0
Limits:
  cpu:     500m
  memory:  512Mi
Requests:
  cpu:      200m
  memory:   256Mi
Liveness:   http-get http://:http/health delay=30s timeout=2s period=5s #success=1 #failure=3
Readiness:  http-get http://:http/health delay=10s timeout=2s period=3s #success=1 #failure=3
```

### Dev vs prod configuration evidence

Dev values after first install:

```powershell
.\helm.exe get values devops-info-dev -n devops-lab10
```

Observed dev install values:

```text
image:
  tag: latest
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30081
  type: NodePort
```

Observed prod values after upgrade:

```text
image:
  tag: 0.1.0
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  nodePort: null
  type: LoadBalancer
```

The resulting production service object:

```text
spec:
  ports:
  - name: http
    nodePort: 30081
    port: 80
    protocol: TCP
    targetPort: http
  type: LoadBalancer
status:
  loadBalancer: {}
```

On local Minikube, `EXTERNAL-IP` remains pending until `minikube tunnel` is started. The service is still valid and ready for a LoadBalancer environment.

### Application accessibility verification

FastAPI chart verification through `kubectl port-forward`:

```text
{"status":"healthy","timestamp":"2026-04-02 21:21:25","uptime_seconds":45}
```

```text
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-dev-devops-info-service-749c97d669-x5m7c","platform":"Linux","platform_version":"6.6.87.2-microsoft-standard-WSL2","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":45,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-02 21:21:25","timezone":""},"request":{"client_ip":"127.0.0.1","user_agent":"Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.26100.7920","method":"GET","path":"/"},"endpoints":[{"path":"/openapi.json","method":"GET","description":""},{"path":"/openapi.json","method":"HEAD","description":""},{"path":"/docs","method":"GET","description":""},{"path":"/docs","method":"HEAD","description":""},{"path":"/docs/oauth2-redirect","method":"GET","description":""},{"path":"/docs/oauth2-redirect","method":"HEAD","description":""},{"path":"/redoc","method":"GET","description":""},{"path":"/redoc","method":"HEAD","description":""},{"path":"/","method":"GET","description":"System and service info about the server"},{"path":"/health","method":"GET","description":"Service health-chek"}]}
```

Rust bonus chart verification:

```text
{"status":"healthy","timestamp":"2026-04-02 21:25:32","uptime_seconds":50}
```

## 6. Operations

### Install

Development install:

```powershell
.\helm.exe install devops-info-dev solution\k8s\devops-info-service --namespace devops-lab10 --create-namespace -f solution\k8s\devops-info-service\values-dev.yaml --wait --wait-for-jobs --timeout 5m
```

Observed output:

```text
NAME: devops-info-dev
NAMESPACE: devops-lab10
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### Upgrade

Production upgrade:

```powershell
.\helm.exe upgrade devops-info-dev solution\k8s\devops-info-service --namespace devops-lab10 -f solution\k8s\devops-info-service\values-prod.yaml --wait --timeout 5m
```

Observed rollout:

```text
Waiting for deployment "devops-info-dev-devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-dev-devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
deployment "devops-info-dev-devops-info-service" successfully rolled out
```

### Rollback

Rollback command used:

```powershell
.\helm.exe rollback devops-info-dev 1 -n devops-lab10 --wait --timeout 5m
```

Observed output:

```text
Rollback was a success! Happy Helming!
```

Release was then restored to the final production state with another `helm upgrade`.

Final release history:

```powershell
.\helm.exe history devops-info-dev -n devops-lab10
```

Observed output:

```text
REVISION  UPDATED                  STATUS      CHART                     APP VERSION  DESCRIPTION
1         Fri Apr  3 00:19:54 2026 superseded  devops-info-service-0.1.0 0.1.0        Install complete
2         Fri Apr  3 00:21:39 2026 superseded  devops-info-service-0.1.0 0.1.0        Upgrade complete
3         Fri Apr  3 00:23:00 2026 superseded  devops-info-service-0.1.0 0.1.0        Rollback to 1
4         Fri Apr  3 00:23:33 2026 deployed    devops-info-service-0.1.0 0.1.0        Upgrade complete
```

### Uninstall

Commands to remove lab resources:

```powershell
.\helm.exe uninstall devops-info-rust -n devops-lab10
.\helm.exe uninstall devops-info-dev -n devops-lab10
.\kubectl.exe delete namespace devops-lab10
```

## 7. Testing And Validation

Validation commands:

```powershell
.\helm.exe lint solution\k8s\devops-info-service
.\helm.exe lint solution\k8s\devops-info-service-rust
.\helm.exe template test-main solution\k8s\devops-info-service --namespace devops-lab10
.\helm.exe template test-rust solution\k8s\devops-info-service-rust --namespace devops-lab10
.\helm.exe install --dry-run --debug devops-info-dev solution\k8s\devops-info-service --namespace devops-lab10 --create-namespace -f solution\k8s\devops-info-service\values-dev.yaml
```

Observed lint output:

```text
==> Linting solution\k8s\devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```text
==> Linting solution\k8s\devops-info-service-rust
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Template rendering succeeded for both charts and produced the expected `Service` and `Deployment` resources, plus hook `Job` resources for the main chart.

Operational validation summary:

- `dev` install succeeded with a single replica and `NodePort`.
- `prod` upgrade succeeded with five replicas and `LoadBalancer`.
- both probes remained active and configurable through values.
- pre-install and post-install hooks both executed and were deleted after success.
- Helm rollback was demonstrated successfully.
- both application charts were installed successfully in the same namespace.

## 8. Bonus - Library Chart

A shared library chart was added in `solution/k8s/common-lib/`.

Implemented shared templates:

- `common.name`
- `common.fullname`
- `common.chart`
- `common.labels`
- `common.selectorLabels`
- `common.extraLabels`
- `common.envList`
- `common.httpProbe`

Both application charts consume the library as a file dependency.

Dependency verification:

```powershell
.\helm.exe dependency list solution\k8s\devops-info-service
.\helm.exe dependency list solution\k8s\devops-info-service-rust
```

Observed output:

```text
NAME       VERSION  REPOSITORY           STATUS
common-lib 0.1.0    file://../common-lib ok
```

Benefits of the library approach:

- DRY naming and labeling logic
- consistent selector semantics across charts
- one probe-rendering implementation for both applications
- simpler maintenance when label strategy or naming rules change

## 9. Conclusion

The Lab 10 objective was completed by packaging the Lab 9 Kubernetes manifests into reusable Helm charts, separating environment-specific values, implementing lifecycle hooks, and validating installation, upgrade, rollback, and accessibility with real CLI evidence. The bonus requirement was also completed by adding a `common-lib` Helm library chart and using it from both the FastAPI and Rust application charts.
