# LAB08 Manual Evidence

Save all screenshots to:

- [screenshots/lab08](C:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/monitoring/docs/screenshots/lab08)

## 1. Screenshot: `/metrics`
- File name:
  - [lab08-metrics-endpoint.png](C:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/monitoring/docs/screenshots/lab08/lab08-metrics-endpoint.png)
- How to open:
  - start the stack from `solution/monitoring`
  - open `http://localhost:8000/metrics`
- What should be visible:
  - Prometheus text output
  - custom metrics like `app_http_requests_total`
- Already connected in main report:
  - `LAB08.md` already references this exact file path

## 2. Screenshot: Prometheus targets
- File name:
  - [lab08-prometheus-targets.png](C:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/monitoring/docs/screenshots/lab08/lab08-prometheus-targets.png)
- How to open:
  - open `http://localhost:9090/targets`
- What should be visible:
  - configured targets
  - target state `UP` where expected
- Already connected in main report:
  - `LAB08.md` already references this exact file path

## 3. Screenshot: PromQL query
- File name:
  - [lab08-promql-query.png](C:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/monitoring/docs/screenshots/lab08/lab08-promql-query.png)
- How to open:
  - open `http://localhost:9090/query`
  - run:

```promql
sum(rate(app_http_requests_total[5m]))
```

- What should be visible:
  - successful query result with time series data
- Already connected in main report:
  - `LAB08.md` already references this exact file path

## 4. Screenshot: Grafana dashboard
- File name:
  - [lab08-grafana-dashboard.png](C:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/monitoring/docs/screenshots/lab08/lab08-grafana-dashboard.png)
- How to open:
  - open `http://localhost:3000`
  - log in with the credentials from `solution/monitoring/.env`
  - open dashboard `Lab08 Prometheus Monitoring`
- What should be visible:
  - populated dashboard panels
  - request rate, error rate, latency, active requests, status distribution, uptime
- Already connected in main report:
  - `LAB08.md` already references this exact file path

## 5. Screenshot: Persistence check
- File name:
  - [lab08-persistence-check.png](C:/Users/xzsay/PycharmProjects/DevOps-Core-Course/solution/monitoring/docs/screenshots/lab08/lab08-persistence-check.png)
- How to open:
  - create or edit a dashboard in Grafana
  - run `docker compose down`
  - run `docker compose up -d`
  - open Grafana again and verify the dashboard still exists
- What should be visible:
  - the dashboard after restart
- Already connected in main report:
  - `LAB08.md` already references this exact file path

## 6. Terminal Output Required
You should also capture terminal output for:

- `docker compose ps`

How to get it:

```powershell
cd C:\Users\xzsay\PycharmProjects\DevOps-Core-Course\solution\monitoring
docker compose ps
```

Where to place it:

- paste into `LAB08.md` under `TODO_MANUAL_COMMAND_OUTPUT`

Format:

```text
Paste as a fenced code block.
```

## 7. Short Manual Notes Required
Add a short note for the persistence check.

What to write:

- 2-4 sentences
- whether the dashboard stayed after restart
- whether any extra action was needed

Where to place it:

- `LAB08.md` under `TODO_MANUAL_VERIFICATION`
