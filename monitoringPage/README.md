# Fusion Job Monitor

A standalone web page that monitors Oracle Fusion Cloud scheduled processes
(ESS job requests) over the last 24 hours.

## What it shows

- **Job runs in last 24 hours** — total request count and distinct job count
- **Failed** — requests in `ERROR`, `ERROR_AUTO_RETRY`, `ERROR_MANUAL_RECOVERY`,
  `VALIDATION_FAILED`
- **Succeeded / Running or queued** — remaining state buckets
- **Jobs by execution count** — each job with how many times it ran, its
  succeeded/failed split, and last run state. Click a row to see every
  individual run (request ID, state, submitted, started, duration, submitter).

## Data source

`GET {base}/ess/rest/scheduler/v1/requests?q=submissionTime gt "<24h ago>"`
— the Scheduler REST API available in Fusion Cloud Applications **23B and
later**, using Basic authentication. The user needs a role that allows
viewing scheduled process requests (the same access as the Scheduled
Processes work area).

## How to run

Browsers block a local page from calling Fusion directly (CORS), so the
easiest way is the bundled helper:

- **Mac:** double-click `start-fusion-job-monitor.command`
- **Windows:** double-click `start-fusion-job-monitor.bat` (needs Python 3
  from python.org, with "Add to PATH" checked during install)
- **Any OS:** `python3 cors-proxy.py`

All three start the local relay on `http://localhost:8765`, open the page in
your browser automatically, and need nothing beyond Python's standard library.

Enter your Fusion base URL (e.g. `https://yourpod.fa.ocs.oraclecloud.com`),
username, and password, then click **Apply**. Optionally tick
*Auto-refresh every 60s*.

The proxy binds to 127.0.0.1 only, forwards only to `*.oraclecloud.com`
(use `--allow-host your.domain.com` for a vanity domain), and logs nothing.

Opening `fusion-job-monitor.html` directly (double-click) also works **if**
your Fusion pod has your page's origin in its CORS allowlist — otherwise the
page shows a clear error explaining the proxy option.

## Security notes

- Credentials are kept in page memory only and sent solely as the
  `Authorization` header to the host you enter. They are never stored
  (only the base URL and username are remembered for the browser session).
- Prefer a dedicated integration user with least-privilege scheduler access
  over a personal admin account.
