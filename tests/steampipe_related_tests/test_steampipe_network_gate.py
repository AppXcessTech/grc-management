"""Tests for the fail-fast network gate in ``app/services/steampipe_process.py``.

Behavior under test:
  - Permission / SQL / auth errors are skipped with a warning (never probed,
    never fail the import).
  - A one-off timeout / transport error on a HEALTHY network path is skipped
    with a warning (the probe succeeds).
  - A confirmed provider outage raises ``NetworkUnavailableError`` IMMEDIATELY
    (no pause, no auto-retry, no 120s window) so the bulk import stops right
    away and the UI can show "Retry Now".
"""
import time

import pytest

from app.services import steampipe_process as sp
from app.services.steampipe_process import NetworkUnavailableError, handle_query_failure


class TestFailFastNetworkGate:
    def test_permission_error_skipped_without_probe(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise AssertionError("probe must not run for permission errors")

        monkeypatch.setattr(sp, "probe_connectivity", _boom)
        assert handle_query_failure("AccessDenied: User is not authorized") is False

    def test_non_network_error_skipped(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise AssertionError("probe must not run for non-network errors")

        monkeypatch.setattr(sp, "probe_connectivity", _boom)
        assert handle_query_failure("syntax error at or near \"SELECT\"") is False

    def test_timeout_on_healthy_network_skipped(self, monkeypatch):
        monkeypatch.setattr(sp, "probe_connectivity", lambda *a, **k: True)
        assert handle_query_failure("", timed_out=True) is False

    def test_network_marker_but_probe_ok_skipped(self, monkeypatch):
        monkeypatch.setattr(sp, "probe_connectivity", lambda *a, **k: True)
        assert handle_query_failure("dial tcp: connection refused") is False

    def test_confirmed_outage_raises_immediately(self, monkeypatch):
        monkeypatch.setattr(sp, "probe_connectivity", lambda *a, **k: False)
        start = time.monotonic()
        with pytest.raises(NetworkUnavailableError) as exc_info:
            handle_query_failure("dial tcp: connection refused")
        # Fail-fast: must raise right away, not wait out a retry window
        assert time.monotonic() - start < 1.0
        assert "Retry Now" in str(exc_info.value)

    def test_timed_out_query_on_confirmed_outage_raises(self, monkeypatch):
        monkeypatch.setattr(sp, "probe_connectivity", lambda *a, **k: False)
        with pytest.raises(NetworkUnavailableError):
            handle_query_failure("", timed_out=True)
