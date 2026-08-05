"""
Shared process tracking for Steampipe subprocesses.

Allows the cancel endpoint (bulk.py) to kill any running Steampipe query
processes immediately, rather than waiting for them to complete.

Also hosts the *network gate*: when a Steampipe query fails because the
backend has lost connectivity to the provider API, the import stops
immediately (fail-fast) instead of skipping tables one-by-one and
"completing" with zero assets. The job is marked failed and the user retries
manually once connectivity is restored.
"""
import subprocess
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ImportCancelledError(Exception):
    """Raised when a user requests cancellation of a running bulk import."""
    pass


class NetworkUnavailableError(Exception):
    """Raised when the backend cannot reach the provider API — the import
    stops immediately (fail-fast) and the user retries manually."""
    pass


# ---------------------------------------------------------------------------
# Network gate configuration
# ---------------------------------------------------------------------------
NETWORK_PROBE_TIMEOUT_SEC = 5       # Per-probe HTTP timeout
MAX_QUERY_ATTEMPTS = 5              # Max attempts per query before giving up
DEFAULT_PROBE_URL = "https://api.github.com"

_NETWORK_ERROR_MARKERS = (
    "connection refused",
    "connection reset",
    "connection timed out",
    "connect: connection",
    "network is unreachable",
    "no route to host",
    "no such host",
    "name or service not known",
    "temporary failure in name resolution",
    "i/o timeout",
    "io timeout",
    "tls handshake",
    "context deadline exceeded",
    "dial tcp",
    "dial udp",
    "unable to connect",
    "socket hang up",
    "broken pipe",
    "gateway timeout",
    "bad gateway",
    "service unavailable",
    "timed out",
    "timeout",
)

_network_probe_url = DEFAULT_PROBE_URL


def set_network_probe_url(url: str) -> None:
    """Point the network gate at the provider being imported.

    Called once per import (e.g. GitLab's base URL, GitHub's API root) so a
    connectivity probe checks the *same* network path the Steampipe plugin
    uses.
    """
    global _network_probe_url
    if url:
        _network_probe_url = url


def _looks_like_network_error(stderr: str) -> bool:
    """Heuristic: does this query error look transport/network-related?

    Permission errors, bad SQL and auth failures do NOT match, so they keep
    today's skip-with-warning behaviour. The connectivity probe that follows
    is the source of truth, so false positives here are harmless.
    """
    if not stderr:
        return False
    low = stderr.lower()
    return any(marker in low for marker in _NETWORK_ERROR_MARKERS)


def probe_connectivity(url: Optional[str] = None) -> bool:
    """Lightweight reachability probe to the provider API.

    Any HTTP response (even 4xx/5xx) means the network path works — only
    transport-level exceptions (DNS, connect, timeout) mean it is down.
    """
    target = url or _network_probe_url
    try:
        import httpx
        with httpx.Client(timeout=NETWORK_PROBE_TIMEOUT_SEC, follow_redirects=True) as client:
            client.get(target, headers={"User-Agent": "grc-platform/1.0"})
        return True
    except Exception:
        return False


def handle_query_failure(stderr: str, timed_out: bool = False) -> bool:
    """Decide what to do after a failed Steampipe query.

    Returns ``True`` when the caller should RETRY the query — never today;
    the retry loops in the services keep this contract for future use.

    Returns ``False`` when the failure is not network-related and the caller
    should skip with a warning as usual (permission / SQL / auth errors).

    Raises ``NetworkUnavailableError`` when the failure is transport-level
    AND the provider endpoint is unreachable — the import stops right away
    (fail-fast) instead of pausing and auto-retrying.
    """
    if not timed_out and not _looks_like_network_error(stderr or ""):
        # Permission / SQL / auth failures — never fail for these
        return False

    if probe_connectivity(_network_probe_url):
        # Network path works — this was a one-off timeout / slow query
        return False

    # Network is genuinely down — stop the import immediately. The user
    # retries manually once connectivity is restored.
    raise NetworkUnavailableError(
        "Network connection lost during import — the import was stopped. "
        "Check the connection and click Retry Now."
    )


# Maps thread_id -> list of Popen objects
_running_procs: dict[int, list[subprocess.Popen]] = {}
_procs_lock = threading.Lock()


def register(proc: subprocess.Popen) -> None:
    """Register a running Steampipe subprocess for the current thread."""
    tid = threading.get_ident()
    with _procs_lock:
        if tid not in _running_procs:
            _running_procs[tid] = []
        _running_procs[tid].append(proc)


def unregister(proc: subprocess.Popen) -> None:
    """Remove a completed/crashed subprocess from the registry."""
    tid = threading.get_ident()
    with _procs_lock:
        procs = _running_procs.get(tid, [])
        if proc in procs:
            procs.remove(proc)


def kill_all() -> int:
    """Kill every running Steampipe subprocess across all threads.

    Returns the number of processes killed.
    """
    count = 0
    with _procs_lock:
        for tid, procs in list(_running_procs.items()):
            for proc in procs:
                try:
                    proc.kill()
                    logger.info(
                        "Killed Steampipe process PID %d (thread %d)",
                        proc.pid, tid,
                    )
                    count += 1
                except Exception:
                    pass
        _running_procs.clear()
    if count:
        logger.warning("Killed %d running Steampipe process(es)", count)
    return count
