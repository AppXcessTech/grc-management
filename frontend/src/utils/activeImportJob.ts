// ---------------------------------------------------------------------------
// Active bulk-import job persistence.
//
// The bulk import runs in a background thread on the server, so a page reload
// or navigation does NOT stop it. These helpers persist the active job id in
// localStorage so any Import surface can re-attach to the running job on mount
// and keep showing progress (instead of leaving the user blind).
// ---------------------------------------------------------------------------

const JOB_STORAGE_KEY = 'activeBulkImportJob';
// Don't re-attach to jobs started more than an hour ago — they're almost
// certainly finished (or the process died); stale entries are cleaned up.
const STALE_JOB_MS = 60 * 60 * 1000;

export function saveActiveImportJob(jobId: string): void {
  try {
    localStorage.setItem(JOB_STORAGE_KEY, JSON.stringify({ jobId, startedAt: Date.now() }));
  } catch {
    // localStorage unavailable — re-attach simply won't work; ignore.
  }
}

export function loadActiveImportJob(): string | null {
  try {
    const raw = localStorage.getItem(JOB_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { jobId?: string; startedAt?: number } | null;
    if (!parsed || typeof parsed.jobId !== 'string' || !parsed.jobId) return null;
    if (Date.now() - (parsed.startedAt || 0) > STALE_JOB_MS) {
      localStorage.removeItem(JOB_STORAGE_KEY);
      return null;
    }
    return parsed.jobId;
  } catch {
    return null;
  }
}

export function clearActiveImportJob(): void {
  try {
    localStorage.removeItem(JOB_STORAGE_KEY);
  } catch {
    // ignore
  }
}
