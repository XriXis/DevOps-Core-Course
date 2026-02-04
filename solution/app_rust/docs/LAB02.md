# LAB02 — Containerizing a Compiled Application with Multi-Stage Builds

## Objective

The goal of this lab is to containerize a compiled language application (Rust) using a **multi-stage Docker build**.  
The purpose of a multi-stage build is to separate the **build environment** from the **runtime environment**, producing a significantly smaller and more secure final container image.


## Multi-Stage Build Strategy

The Dockerfile is divided into **two stages**:

1. **Builder stage**
2. **Runtime stage**

Each stage has a distinct responsibility.

---

## Stage 1 — Builder

```dockerfile
FROM rust:1.91.0-alpine3.20 AS builder
````

### Purpose

* Provide a full Rust toolchain
* Compile the application into a single optimized binary
* Keep build tools out of the final image

### Key Characteristics

* Includes:

    * Rust compiler and Cargo
    * GCC and musl-dev for native compilation
* Uses a **non-root user** (`appuser`)
* Caches dependencies using:

  ```dockerfile
  RUN cargo fetch
  ```
* Produces a release binary:

  ```dockerfile
  RUN cargo build --release --bin devops-info-service
  ```

### Result

* Large image size
* Contains compilers and build dependencies
* A lot of useless things for production runtime

---

## Stage 2 — Runtime

```dockerfile
FROM alpine:3.20
```

### Purpose

* Run the precompiled binary
* Contain **only what is strictly necessary**

### Key Characteristics

* No compiler or build tools
* Minimal Alpine base image
* Runs as a **non-root user**
* Copies only the compiled binary:

  ```dockerfile
  COPY --from=builder /app/target/release/devops-info-service ./devops-info-service
  ```

---

## Build Process Output

### Docker Build Command

```bash
docker build -t devops-i-lobazov-rust:0.1.0 .
```

### Build Output

```text
[+] Building 428.0s (19/19) FINISHED                                                                    docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                    0.0s
 => => transferring dockerfile: 885B                                                                                    0.0s
 => [internal] load metadata for docker.io/library/alpine:3.20                                                          0.3s
 => [internal] load metadata for docker.io/library/rust:1.91.0-alpine3.20                                               0.3s
 => [internal] load .dockerignore                                                                                       0.0s
 => => transferring context: 226B                                                                                       0.0s
 => CACHED [builder 1/9] FROM docker.io/library/rust:1.91.0-alpine3.20@sha256:55905a107df49e2ca919ebceb11bdc35471b3436  0.1s
 => => resolve docker.io/library/rust:1.91.0-alpine3.20@sha256:55905a107df49e2ca919ebceb11bdc35471b3436d9f08c179c3c51e  0.1s
 => [internal] load build context                                                                                       0.0s
 => => transferring context: 293B                                                                                       0.0s
 => [stage-1 1/4] FROM docker.io/library/alpine:3.20@sha256:a4f4213abb84c497377b8544c81b3564f313746700372ec4fe84653e4f  0.1s 
 => => resolve docker.io/library/alpine:3.20@sha256:a4f4213abb84c497377b8544c81b3564f313746700372ec4fe84653e4fb03805    0.1s 
 => [builder 2/9] RUN apk add --no-cache      shadow      musl-dev     gcc     && addgroup -S appgroup      && adduser  1.9s 
 => [builder 3/9] WORKDIR /app                                                                                          0.1s 
 => [builder 4/9] COPY ./Cargo.toml ./Cargo.toml                                                                        0.1s 
 => [builder 5/9] COPY ./Cargo.lock ./Cargo.lock                                                                        0.1s 
 => [builder 6/9] RUN cargo fetch                                                                                     251.6s 
 => [builder 7/9] COPY ./src ./src                                                                                      0.2s 
 => [builder 8/9] RUN cargo build --release --bin devops-info-service                                                  97.9s 
 => [builder 9/9] RUN cargo install --path .                                                                           74.4s 
 => CACHED [stage-1 2/4] RUN apk add --no-cache shadow     && groupadd -r appgroup     && useradd -r -g appgroup -m ap  0.0s 
 => CACHED [stage-1 3/4] WORKDIR /app                                                                                   0.0s 
 => [stage-1 4/4] COPY --from=builder /app/target/release/devops-info-service ./devops-info-service                     0.1s 
 => exporting to image                                                                                                  0.7s 
 => => exporting layers                                                                                                 0.4s 
 => => exporting manifest sha256:f29b9f515b31eb34b36300fa5050d8d6eddd1b5199daa3529b965436af3f6adb                       0.0s 
 => => exporting config sha256:e982ad32f755186f32b53e4b737adfbbe66487d573adca4a3f698cdc864514a2                         0.0s 
 => => exporting attestation manifest sha256:f47c2262266a302c0b8b106ec0817edb11a61f3809e0e492776f8d64c5d7c8be           0.0s 
 => => exporting manifest list sha256:46ead51211f51a41807a49d0ff402cb39aad3335170814f6b7e275cee8573d27                  0.0s 
 => => naming to docker.io/library/devops-i-lobazov-rust:0.1.0                                                          0.0s 
 => => unpacking to docker.io/library/devops-i-lobazov-rust:0.1.0                                                       0.1s 
                                                                                                                             
What's next:
    View a summary of image vulnerabilities and recommendations → docker scout quickview
```

### Check for semantic equivalence

- Host output:
  ```bash
  > docker run -p 5000:5000 -e DEBUG=true devops-i-lobazov-rust:0.1.0                                                                                                                 
  [2026-02-04T21:00:24Z INFO  devops_info_service] Starting DevOps Info Service on 0.0.0.0:5000 at 2026-02-04 21:00:24.535045895 UTC
  [2026-02-04T21:00:24Z INFO  actix_server::builder] starting 12 workers
  [2026-02-04T21:00:24Z INFO  actix_server::server] Actix runtime found; starting in Actix runtime
  [2026-02-04T21:00:24Z INFO  actix_server::server] starting service: "actix-web-service-0.0.0.0:5000", workers: 12, listening on: 0.0.0.0:5000
  [2026-02-04T21:01:52Z DEBUG devops_info_service::routes] Health check request
  [2026-02-04T21:01:52Z INFO  actix_web::middleware::logger] 172.17.0.1 "GET /health HTTP/1.1" 200 74 "-" "Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.26100.7462" 0.000179
  [2026-02-04T21:02:00Z DEBUG devops_info_service::routes] Request: GET /
  [2026-02-04T21:02:00Z INFO  actix_web::middleware::logger] 172.17.0.1 "GET / HTTP/1.1" 200 745 "-" "Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.26100.7462" 0.023157
  ```
- Curl output
  ```ps
  PS C:\Users\xzsay\PycharmProjects\DevOps-Core-Course\solution\app_rust> (curl -UseBasicParsing http://localhost:5000/health).Content | ConvertFrom-Json | ConvertTo-Json
  {                                                                                                                            
  "status":  "healthy",                                                                                                    
  "timestamp":  "2026-02-04 21:01:52",                                                                                     
  "uptime_seconds":  87                                                                                                    
  }
  PS C:\Users\xzsay\PycharmProjects\DevOps-Core-Course\solution\app_rust> (curl -UseBasicParsing http://localhost:5000/).Content | ConvertFrom-Json | ConvertTo-Json      
  {
  "endpoints":  [
  {
  "description":  "System and service info about the server",
  "method":  "GET",
  "path":  "/"
  },
  {
  "description":  "Health check",
  "method":  "GET",
  "path":  "/health"
  }
  ],
  "request":  {
  "client_ip":  "172.17.0.1",
  "method":  "GET",
  "path":  "/",
  "user_agent":  "Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.26100.7462"
  },
  "runtime":  {
  "current_time":  "2026-02-04 21:02:00",
  "timezone":  "UTC",
  "uptime_human":  "0 hours, 1 minutes",
  "uptime_seconds":  96
  },
  "service":  {
  "description":  "DevOps course info service",
  "framework":  "Actix-web",
  "name":  "devops-info-service",
  "version":  "1.0.0"
  },
  "system":  {
  "architecture":  "x86_64",
  "cpu_count":  12,
  "hostname":  "9b36c0bf0df8",
  "platform":  "Linux",
  "platform_version":  "6.6.87.2-microsoft-standard-WSL2",
  "rust_version":  "unknown"
  }
  }
  ```
---

## Image Size Comparison

### Docker Images Command

```bash
docker images | grep devops-i-lobazov-rust
```

### Results

```text
devops-i-lobazov-rust     0.1.0       3bcb0abba752   29 minutes ago   24.8MB
devops-i-lobazov-rust     builder     79f447ef6057   31 minutes ago   2.55GB
```

### Size Analysis

| Image Stage | Approximate Size |
|-------------|------------------|
| Builder     | 2.55GB           |
| Final Image | 24.8MB           |

### Reduction - 10.000%!

---

## Why Multi-Stage Builds Matter for Compiled Languages

Compiled languages such as **Rust, Go, and C++** are ideal candidates for multi-stage builds because:

* They produce **self-contained binaries**
* Runtime does not require:

    * Compilers
    * Package managers
    * Header files
* Final image can be extremely small

Benefits include:

* Faster image pulls
* Lower storage usage
* Reduced attack surface
* Cleaner production environment

---

## Security Implications

Multi-stage builds improve security by:

* Removing build tools from the runtime image
* Reducing the number of installed packages
* Limiting the attack surface

A smaller image means:

* Fewer known vulnerabilities
* Lower risk of privilege escalation
* Easier vulnerability scanning

---

## Trade-offs and Design Decisions

### Trade-offs

* Slightly longer (first) build time
* More complex Dockerfile
* Debugging requires rebuilding the image

### Decisions Made

* Alpine Linux chosen for minimal size
* Non-root user for runtime security
* Separate build and runtime stages for clarity and safety

---

## Conclusion

This lab demonstrates how multi-stage Docker builds enable:

* Clean separation of concerns
* Significant image size reduction
* Improved security posture
* Production-ready container images for compiled applications

Multi-stage builds are a **best practice** for containerizing compiled languages.

