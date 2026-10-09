# Banking Performance Lab — Troubleshooting Notes

This document records practical commands used to investigate API behavior,
database connections, Redis, application logs, and performance-test failures.

All commands target the local Docker-based lab environment.

## 1. Check API Health and Endpoints

Check whether the API is responding:

```bash
curl -i http://localhost:5000/health
```

Inspect an account endpoint:

```bash
curl -i http://localhost:5000/accounts/1
```

For a quick request without printing the response body:

```bash
curl -s http://localhost:5000/accounts/1 > /dev/null
```

For an endpoint that requires authentication, use the login flow and token
expected by the application. Do not commit real tokens or passwords.

## 2. Inspect Application Logs

View the latest 100 lines:

```bash
docker logs --tail 100 banking-performance-lab-banking-api-1
```

Follow logs live while sending requests:

```bash
docker logs -f banking-performance-lab-banking-api-1
```

Filter for likely failures:

```bash
docker logs banking-performance-lab-banking-api-1 2>&1 \
  | grep -Ei "error|exception|traceback|500" | tail -30
```

Check recent application-specific trace markers, if enabled:

```bash
docker logs banking-performance-lab-banking-api-1 2>&1 \
  | grep "APM_TRACE" | tail -5
```

Inspect where a trace marker appears in the running container's code:

```bash
docker exec banking-performance-lab-banking-api-1 \
  grep -n "APM_TRACE" /app/app.py
```

**Troubleshooting approach:** correlate an API request or failed test with
the application logs around the same time. A matching HTTP 500 response and
traceback can help narrow down the failing code path.

## 3. Investigate JMeter HTTP 500 Errors

Run the JMeter test plan with 500 configured users and save results:

```bash
~/apache-jmeter/bin/jmeter -n \
  -t ~/banking-performance-lab/banking-performance-lab.jmx \
  -Jusers=500 \
  -l ~/banking-performance-lab/results.jtl \
  -e \
  -o ~/banking-performance-lab/report
```

Open the generated HTML report:

```bash
open ~/banking-performance-lab/report/index.html
```

Find a result row containing `500`:

```bash
grep "500" ~/banking-performance-lab/results.jtl | head -1
```

Inspect CSV rows whose fourth field is `500`:

```bash
awk -F',' '$4=="500" {print}' \
  ~/banking-performance-lab/results.jtl | head -1
```

**Important:** JTL format depends on the JMeter result configuration.
Confirm the CSV column order and header before assuming field `$4` is the
HTTP response code. Prefer the HTML report and the actual response-code
field when diagnosing failures.

If regenerating an HTML report, ensure its output directory does not already
contain an old report:

```bash
rm -rf ~/banking-performance-lab/report
```

Only remove the generated report directory when you are sure it contains
no files you need to keep.

## 4. Inspect PostgreSQL Connections

Check the PostgreSQL connection limit:

```bash
docker exec -it banking-performance-lab-postgres-1 \
  psql -U bank -d banking -c "SHOW max_connections;"
```

Count active PostgreSQL sessions:

```bash
docker exec -it banking-performance-lab-postgres-1 \
  psql -U bank -d banking \
  -c "SELECT count(*) AS connections FROM pg_stat_activity;"
```

Inspect database-related environment variable names in the API container:

```bash
docker exec banking-performance-lab-banking-api-1 \
  env | grep -Ei "pool|database|db"
```

Inspect PostgreSQL-related environment variable names:

```bash
docker exec banking-performance-lab-postgres-1 \
  env | grep -Ei "POSTGRES|PG"
```

**Troubleshooting approach:** compare the connection count and configured
limits with API errors and application logs during load. A connection count
alone does not prove pool exhaustion; correlate multiple sources of evidence.

## 5. Check Redis

Check Redis connectivity:

```bash
docker exec banking-performance-lab-redis-1 redis-cli ping
```

Check latency interactively:

```bash
docker exec -it banking-performance-lab-redis-1 redis-cli --latency
```

Inspect a test key:

```bash
docker exec banking-performance-lab-redis-1 redis-cli SET account:1 "Via Account"
docker exec banking-performance-lab-redis-1 redis-cli GET account:1
docker exec banking-performance-lab-redis-1 redis-cli EXISTS account:1
```

These commands modify Redis data. Use only disposable test keys in the lab.

## 6. Inspect Metrics

Check whether the application's Prometheus metrics endpoint responds:

```bash
curl -i http://localhost:5000/metrics
```

A successful HTTP response confirms that the endpoint is reachable; inspect
the response body to confirm which metrics are actually exposed.

## 7. Git Hygiene

Check which files are changed:

```bash
git status
```

Check the configured remote:

```bash
git remote -v
```

Verify that generated or backup files are ignored:

```bash
git check-ignore -v app.py.backup 900000 jmeter.log
```

Avoid committing large raw JMeter results, generated reports, credentials,
tokens, or unrelated local files. Keep only artifacts useful for reviewing
the project.

## 8. General Investigation Workflow

1. Reproduce the behavior with a health check or API request.
2. Run the relevant JMeter scenario and inspect its HTML report and result data.
3. Correlate failures with application logs.
4. Check database connection counts, limits, and relevant configuration.
5. Check Redis connectivity and metrics when relevant.
6. Record the observed cause, code change, and before/after test evidence.
7. Rerun the same test conditions before claiming that a fix resolved the issue.

## Notes

- Commands and container names assume the local Docker Compose setup used in
  this lab; names may differ in other environments.
- Do not claim that a diagnostic command proved a root cause unless the
  supporting logs, code, or test results confirm it.
- Keep real credentials and sensitive environment values out of this file.
