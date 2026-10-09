# Banking API Performance Testing Lab

A personal performance-testing project that simulates a banking API using Python, Flask, PostgreSQL, Redis, Apache JMeter, and k6.

## Project Objectives

- Evaluate API response times, throughput, and error rates.
- Investigate database connection pool exhaustion under concurrent load.
- Validate the effectiveness of a code-level fix.
- Run a short endurance test to observe performance stability.

## Technology Stack

- **API:** Python, Flask
- **Database:** PostgreSQL
- **Cache:** Redis
- **Performance testing:** Apache JMeter, k6
- **Monitoring:** Prometheus
- **Environment:** Docker Compose

## Performance Testing Approach

1. Run concurrent requests against the API using JMeter.
2. Review response times, throughput, error rates, and application logs.
3. Investigate HTTP 500 errors and database connection pool exhaustion.
4. Increase the connection pool size as an initial troubleshooting step.
5. Inspect database connection handling and fix the connection lifecycle.
6. Rerun the load test and perform a five-minute endurance test.

## Key Finding and Resolution

The initial test produced HTTP 500 errors on the accounts endpoint. Application logs showed database connection pool exhaustion.

Increasing the connection pool size alone did not resolve the issue. Further investigation identified that connections acquired from the pool were being closed instead of returned to the pool.

The connection lifecycle was corrected using `try/finally`, ensuring cursors were closed and connections were returned to the pool with `putconn()`.

## Results

### Before and After the Fix

| Metric | Before fix | After fix |
|---|---:|---:|
| Test duration | 30 seconds | 30 seconds |
| Concurrent users | 10 | 10 |
| Requests completed | — | 8,680 |
| Throughput | ~253 req/s | ~288.6 req/s |
| Average response time | ~33 ms | ~29 ms |
| Maximum response time | ~160 ms | ~84 ms |
| Error rate | ~49.7% | 0% |

### Five-Minute Endurance Test

| Metric | Result |
|---|---:|
| Test duration | 5 minutes |
| Concurrent users | 10 |
| Total requests | 101,165 |
| Throughput | ~337.2 req/s |
| Average response time | ~29 ms |
| Maximum response time | ~135 ms |
| Error rate | 0% |
The five-minute test completed without observed request errors. These results apply to this local test environment and are not a guarantee of production capacity.

## Key Takeaways

- Use application logs alongside load-test metrics to investigate failures.
- Increasing connection pool size is not a substitute for correct connection management.
- Validate fixes by rerunning comparable tests.
- Use endurance testing to observe behavior over a longer period.

## Disclaimer

This is a personal learning and portfolio project using a simulated banking API and dummy credentials. It is not affiliated with a real bank and contains no real customer data. Results are specific to the local test environment.
