import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Check, Download, Package, RefreshCw, Trash2, X, AlertTriangle,
  Cloud, Fingerprint, Database, ListChecks, Code2, GitBranch, Filter,
} from 'lucide-react';
import { saveActiveImportJob, loadActiveImportJob, clearActiveImportJob } from '../../utils/activeImportJob';
import { useOnlineStatus } from '../../utils/useOnlineStatus';

interface CanonicalAsset {
  id: number;
  provider: string;
  provider_resource_id: string;
  canonical_type: string;
  display_name: string | null;
  account_id: string | null;
  region: string | null;
  owner: string | null;
  tags: Record<string, string> | null;
  status: string | null;
  details: Record<string, unknown> | null;
  discovered_at: string | null;
}

interface WarningEntry {
  service: string;
  action: string;
  resource: string;
  table: string;
  message: string;
}

interface BulkConfigResponse {
  aws_configured: boolean;
  azure_configured: boolean;
  okta_configured: boolean;
  github_configured: boolean;
  gitlab_configured: boolean;
  gcp_configured: boolean;
  bitbucket_configured: boolean;
  integrations_to_run: string[];
}

interface BulkImportProgress {
  job_id: string;
  status: string;
  progress: number;
  phase: string;
  message: string;
  current_integration: string;
  current_message: string;
  current_progress: number;
  results: Record<string, any>;
  error: string | null;
  warnings: WarningEntry[];
  started_at: string;
  completed_at: string | null;
  last_activity_at: string | null;
}

// Provider icons & labels
const PROVIDER_META: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
  aws: {
    label: 'AWS',
    icon: <Cloud size={18} />,
    description: 'Cloud resources (EC2, S3, RDS, etc.)',
  },
  azure: {
    label: 'Azure',
    icon: <Database size={18} />,
    description: 'Cloud resources (VMs, Storage, etc.)',
  },
  gcp: {
    label: 'GCP',
    icon: <Cloud size={18} />,
    description: 'Cloud resources (Compute, Storage, IAM, etc.)',
  },
  okta: {
    label: 'Okta',
    icon: <Fingerprint size={18} />,
    description: 'Identity assets (users, groups, apps)',
  },
  github: {
    label: 'GitHub',
    icon: <Code2 size={18} />,
    description: 'Repositories, teams, members, secrets, workflows',
  },
  gitlab: {
    label: 'GitLab',
    icon: <GitBranch size={18} />,
    description: 'Projects, groups, members, variables, pipelines',
  },
  bitbucket: {
    label: 'Bitbucket',
    icon: <GitBranch size={18} />,
    description: 'Repositories, projects, workspaces, members, branch restrictions',
  },
};

type ImportState =
  | { status: 'idle' }
  | { status: 'pick_providers' }
  | { status: 'importing'; jobId: string; progress: BulkImportProgress | null }
  | { status: 'success'; resources: number; stored: number; relationships: number; warnings: WarningEntry[]; providerResults: Record<string, any> }
  | { status: 'error'; message: string };

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_DURATION_MS = 15 * 60 * 1000;     // 15 minutes max import time
const STALE_THRESHOLD_MS = 3 * 60 * 1000;          // 3 minutes without progress update = stale

const CanonicalCategoryPage = () => {
  const { group, type } = useParams<{ group: string; type: string }>();
  const [assets, setAssets] = useState<CanonicalAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [importState, setImportState] = useState<ImportState>({ status: 'idle' });
  const [bulkConfig, setBulkConfig] = useState<BulkConfigResponse | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [selectedProviders, setSelectedProviders] = useState<Record<string, boolean>>({});
  const [activeProviderFilter, setActiveProviderFilter] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [connectionLost, setConnectionLost] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollStartRef = useRef<number>(0);
  const lastProgressRef = useRef<number>(0);
  const jobIdRef = useRef<string>('');
  // The providers requested for the current/last import — used by Retry (the
  // picker's selection is cleared once it closes).
  const lastProvidersRef = useRef<string[]>([]);

  const label = type || group || 'Assets';

  const getAuthHeaders = (): Record<string, string> => {
    const t = localStorage.getItem('token');
    return t ? { Authorization: `Bearer ${t}` } : {};
  };

  // Fetch bulk config to know which integrations are configured
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/integrations/bulk/config', { headers: getAuthHeaders() });
        const data: BulkConfigResponse = await res.json();
        setBulkConfig(data);
      } catch {
        setBulkConfig(null);
      } finally {
        setConfigLoading(false);
      }
    })();
  }, []);

  // Initial load — only re-fetch when route params change
  useEffect(() => {
    if (!group) return;
    setLoading(true);
    const params = type
      ? `type=${encodeURIComponent(type)}`
      : `category=${encodeURIComponent(group)}`;
    fetch(`/api/canonical-assets?${params}`, {
      headers: getAuthHeaders(),
    })
      .then((r) => r.json())
      .then(setAssets)
      .catch(() => setAssets([]))
      .finally(() => setLoading(false));
  }, [group, type]);

  const refetchAssets = useCallback(() => {
    if (!group) return;
    const params = type
      ? `type=${encodeURIComponent(type)}`
      : `category=${encodeURIComponent(group)}`;
    fetch(`/api/canonical-assets?${params}`, {
      headers: getAuthHeaders(),
    })
      .then((r) => r.json())
      .then(setAssets)
      .catch(() => {});
  }, [group, type]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const pollStatus = useCallback(async (jobId: string) => {
    const elapsed = Date.now() - pollStartRef.current;
    if (elapsed > POLL_MAX_DURATION_MS) {
      if (pollRef.current) clearInterval(pollRef.current);
      setImportState({
        status: 'error',
        message: 'Import timed out after 15 minutes. The connection may have been interrupted.',
      });
      return;
    }

    try {
      const res = await fetch(`/api/integrations/bulk/sync-status/${jobId}`, {
        headers: getAuthHeaders(),
      });

      // 404 = the job no longer exists (e.g. the server restarted). This is not
      // a network blip — stop polling and tell the user.
      if (res.status === 404) {
        if (pollRef.current) clearInterval(pollRef.current);
        clearActiveImportJob();
        jobIdRef.current = '';
        setReconnecting(false);
        setConnectionLost(false);
        setImportState({
          status: 'error',
          message: 'This import job no longer exists (the server may have restarted). Start a new import.',
        });
        return;
      }

      // If the server is unreachable (network error), check if we've been silent too long
      if (!res.ok) {
        const idleTime = Date.now() - lastProgressRef.current;
        if (idleTime > STALE_THRESHOLD_MS) {
          if (pollRef.current) clearInterval(pollRef.current);
          setReconnecting(false);
          setConnectionLost(true);
          setImportState({
            status: 'error',
            message:
              'Connection to the server was lost. The import may still be running in the background — click Reconnect to check again.',
          });
        } else {
          setReconnecting(true);
        }
        return;
      }

      const progress: BulkImportProgress = await res.json();
      lastProgressRef.current = Date.now();
      setReconnecting(false);

      if (progress.status === 'completed') {
        if (pollRef.current) clearInterval(pollRef.current);
        clearActiveImportJob();
        // Aggregate results across all integrations
        let totalDiscovered = 0;
        let totalStored = 0;
        let totalRelationships = 0;
        const allWarnings: WarningEntry[] = [];

        if (progress.results) {
          Object.values(progress.results).forEach((result: any) => {
            totalDiscovered += result.resources_discovered ?? 0;
            totalStored += result.assets_stored ?? 0;
            totalRelationships += result.relationships_created ?? 0;
            if (result.warnings) allWarnings.push(...result.warnings);
          });
        }
        if (progress.warnings) allWarnings.push(...progress.warnings);

        setImportState({
          status: 'success',
          resources: totalDiscovered || progress.resources_discovered || 0,
          stored: totalStored || progress.assets_stored || 0,
          relationships: totalRelationships || progress.relationships_created || 0,
          warnings: allWarnings,
          providerResults: progress.results || {},
        });
        // Auto-refresh assets after a short delay so the user sees the modal first
        setTimeout(() => refetchAssets(), 100);
      } else if (progress.status === 'error') {
        if (pollRef.current) clearInterval(pollRef.current);
        clearActiveImportJob();
        setImportState({ status: 'error', message: progress.error || 'Import failed' });
      } else if (progress.status === 'cancelled') {
        if (pollRef.current) clearInterval(pollRef.current);
        clearActiveImportJob();
        jobIdRef.current = '';
        setImportState({ status: 'idle' });
      } else {
        // Still running - update progress
        setImportState({ status: 'importing', jobId, progress });
      }
    } catch {
      const idleTime = Date.now() - lastProgressRef.current;
      if (idleTime > STALE_THRESHOLD_MS) {
        if (pollRef.current) clearInterval(pollRef.current);
        setReconnecting(false);
        setConnectionLost(true);
        setImportState({
          status: 'error',
          message:
            'Connection to the server was lost. The import may still be running in the background — click Reconnect to check again.',
        });
      } else {
        setReconnecting(true);
      }
    }
  }, []);

  // Re-attach to a bulk import still running in the background after a page
  // reload / navigation, so the user can keep watching progress.
  useEffect(() => {
    const storedJobId = loadActiveImportJob();
    if (!storedJobId) return;
    jobIdRef.current = storedJobId;
    pollStartRef.current = Date.now();
    lastProgressRef.current = Date.now();
    setImportState({ status: 'importing', jobId: storedJobId, progress: null });
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => pollStatus(storedJobId), POLL_INTERVAL_MS);
    pollStatus(storedJobId);
  }, [pollStatus]);

  // Open the provider picker — start with nothing selected
  const openProviderPicker = useCallback(() => {
    setSelectedProviders({});
    setImportState({ status: 'pick_providers' });
  }, []);

  const toggleProvider = (key: string) => {
    setSelectedProviders(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Start the import for the given providers using the bulk sync API
  const startImport = useCallback(async (providers: string[]) => {
    if (providers.length === 0) return;
    lastProvidersRef.current = providers;

    setIsCancelling(false);
    setImportState({ status: 'importing', jobId: '', progress: null });
    pollStartRef.current = Date.now();
    lastProgressRef.current = Date.now();

    try {
      const res = await fetch('/api/integrations/bulk/sync', {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ integrations: providers }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Import failed (${res.status})`);
      }
      const data = await res.json();
      const jobId: string = data.job_id;

      jobIdRef.current = jobId;
      saveActiveImportJob(jobId);
      setImportState({ status: 'importing', jobId, progress: null });

      // Start polling
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(() => pollStatus(jobId), POLL_INTERVAL_MS);
      // Also poll immediately
      pollStatus(jobId);
    } catch (err: any) {
      if (pollRef.current) clearInterval(pollRef.current);
      clearActiveImportJob();
      jobIdRef.current = '';
      setImportState({ status: 'error', message: err.message || 'Import failed' });
    }
  }, [pollStatus]);

  const handleImport = useCallback(async () => {
    const toImport = Object.entries(selectedProviders)
      .filter(([, checked]) => checked)
      .map(([key]) => key);
    await startImport(toImport);
  }, [selectedProviders, startImport]);

  // Retry the last import (same providers), e.g. after a network failure.
  // If nothing was started this session (e.g. a page reload followed by a 404),
  // fall back to opening the picker so the button never silently no-ops.
  const handleRetry = useCallback(async () => {
    if (lastProvidersRef.current.length === 0) {
      openProviderPicker();
      return;
    }
    await startImport(lastProvidersRef.current);
  }, [startImport, openProviderPicker]);

  // Providers that failed in the last job — used for the "Retry Failed" action.
  const failedProviders =
    importState.status === 'success'
      ? Object.entries(importState.providerResults)
          .filter(([, r]: [string, any]) => r?.status === 'error')
          .map(([k]) => k)
      : [];

  const handleCancelImport = useCallback(async () => {
    // Stop polling immediately, but keep the modal open so the user can see
    // that the cancellation was accepted (or that it failed and they can retry).
    const id = jobIdRef.current;
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
    if (!id) {
      jobIdRef.current = '';
      setImportState({ status: 'idle' });
      return;
    }
    setIsCancelling(true);
    try {
      const res = await fetch(`/api/integrations/bulk/cancel/${id}`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        throw new Error(`Cancel request failed (${res.status})`);
      }
      clearActiveImportJob();
      jobIdRef.current = '';
      setImportState({ status: 'idle' });
    } catch {
      setImportState({
        status: 'error',
        message: 'Failed to cancel the import. The import may still be running — please try again.',
      });
    } finally {
      setIsCancelling(false);
    }
  }, []);

  // Re-attach after the connection was lost — resume polling the same job.
  const handleReconnect = useCallback(() => {
    setReconnecting(false);
    setConnectionLost(false);
    const id = jobIdRef.current;
    if (!id) {
      setImportState({ status: 'idle' });
      return;
    }
    pollStartRef.current = Date.now();
    lastProgressRef.current = Date.now();
    setImportState({ status: 'importing', jobId: id, progress: null });
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => pollStatus(id), POLL_INTERVAL_MS);
    pollStatus(id);
  }, [pollStatus]);

  // Instant network detection: react as soon as the browser reports the
  // network dropped (instead of waiting for the next poll to fail), and
  // automatically resume polling when connectivity returns.
  const isOnline = useOnlineStatus();
  useEffect(() => {
    if (!isOnline) {
      // Network just dropped — surface it immediately if an import is visible.
      if (importState.status === 'importing') setReconnecting(true);
      return;
    }
    // Back online — clear the transient banner and stop counting failures.
    setReconnecting(false);
    lastProgressRef.current = Date.now();
    if (connectionLost) {
      if (jobIdRef.current) handleReconnect();
      else {
        setConnectionLost(false);
      }
    }
  }, [isOnline, importState.status, connectionLost, handleReconnect]);

  const handleSuccessClose = useCallback(() => {
    // Keep the persisted job when the connection was lost (the import may still
    // be running) so a later page load can re-attach to it.
    if (!connectionLost) clearActiveImportJob();
    jobIdRef.current = '';
    setImportState({ status: 'idle' });
    refetchAssets();
  }, [refetchAssets, connectionLost]);

  const handleExportCsv = useCallback(async () => {
    try {
      const res = await fetch('/api/canonical-assets/export-csv', { headers: getAuthHeaders() });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'canonical_assets.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Export failed');
    }
  }, []);

  const handleClear = useCallback(async () => {
    if (!confirm('Delete all imported assets? This cannot be undone.')) return;
    try {
      await fetch('/api/canonical-assets/clear', { method: 'DELETE', headers: getAuthHeaders() });
      setAssets([]);
    } catch {
      alert('Clear failed');
    }
  }, []);

  // Determine which providers are configured and available
  const configuredProviders = ['aws', 'azure', 'gcp', 'okta', 'github', 'gitlab', 'bitbucket'].filter(k =>
    bulkConfig?.[`${k}_configured` as keyof BulkConfigResponse]
  );
  const hasConfiguredProviders = configuredProviders.length > 0;

  // Compute provider counts for filter pills
  const providerCounts = assets.reduce<Record<string, number>>((acc, a) => {
    const p = a.provider || 'unknown';
    acc[p] = (acc[p] || 0) + 1;
    return acc;
  }, {});
  const uniqueProviders = Object.keys(providerCounts).sort();

  // Filter assets by selected provider
  const filteredAssets = activeProviderFilter
    ? assets.filter(a => (a.provider || 'unknown') === activeProviderFilter)
    : assets;

  const grouped = filteredAssets.reduce<Record<string, CanonicalAsset[]>>((acc, a) => {
    const key = a.canonical_type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(a);
    return acc;
  }, {});

  return (
    <div className="assets-page">
      <div className="assets-page-header">
        <Link to="/assets" className="back-link"><ArrowLeft size={18} /> All Assets</Link>
        <div className="assets-page-title">
          <h1>{label}</h1>
          {!loading && <span className="assets-count">{filteredAssets.length} asset{filteredAssets.length !== 1 ? 's' : ''}{activeProviderFilter ? ` (filtered)` : ''}</span>}
        </div>
      </div>

      {/* Toolbar with filter and actions */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        marginBottom: '1.25rem',
        flexWrap: 'wrap',
      }}>
        {/* Left: Filter dropdown */}
        {!loading && uniqueProviders.length > 0 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.375rem 0.75rem',
              borderRadius: '8px',
              background: 'rgba(14, 165, 233, 0.08)',
              color: 'var(--primary)',
              fontSize: '0.75rem',
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}>
              <Filter size={14} />
              Provider
            </div>
            <select
              value={activeProviderFilter || ''}
              onChange={e => setActiveProviderFilter(e.target.value || null)}
              style={{
                padding: '0.5rem 2.25rem 0.5rem 0.875rem',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--text-main)',
                fontSize: '0.8125rem',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
                minWidth: '175px',
                appearance: 'auto',
                transition: 'border-color 0.15s, box-shadow 0.15s',
              }}
              onFocus={e => {
                e.currentTarget.style.borderColor = 'var(--primary)';
                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(14, 165, 233, 0.15)';
              }}
              onBlur={e => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <option value="">All Providers ({assets.length})</option>
              {uniqueProviders.map(p => {
                const meta = PROVIDER_META[p.toLowerCase()];
                return (
                  <option key={p} value={p}>
                    {meta?.label || p} ({providerCounts[p]})
                  </option>
                );
              })}
            </select>
          </div>
        )}

        {/* Right: Action buttons */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {!configLoading && hasConfiguredProviders && (
            <button className="btn btn-primary" onClick={openProviderPicker} title="Import resources" disabled={importState.status === 'importing'} style={{ fontSize: '0.8125rem', padding: '0.5rem 0.875rem', ...(importState.status === 'importing' ? { opacity: 0.5, cursor: 'not-allowed' } : {}) }}>
              <ListChecks size={16} /> Import
            </button>
          )}
          {!configLoading && !hasConfiguredProviders && (
            <button className="btn btn-primary" disabled title="No integrations configured" style={{ opacity: 0.5, cursor: 'not-allowed', fontSize: '0.8125rem', padding: '0.5rem 0.875rem' }}>
              <RefreshCw size={16} /> Import
            </button>
          )}
          <button className="btn" onClick={handleExportCsv} title="Export as CSV" style={{ fontSize: '0.8125rem', padding: '0.5rem 0.875rem' }}>
            <Download size={16} /> CSV Export
          </button>
          <button className="btn btn-danger" onClick={handleClear} title="Delete all assets" style={{ fontSize: '0.8125rem', padding: '0.5rem 0.875rem' }}>
            <Trash2 size={16} /> Clear
          </button>
        </div>
      </div>

      {/* Import provider picker modal */}
      {importState.status === 'pick_providers' && (
        <div className="import-modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget) setImportState({ status: 'idle' });
        }}>
          <div className="import-modal" style={{ maxWidth: '420px' }}>
            <div className="import-modal-icon">
              <ListChecks size={28} />
            </div>
            <h2>Select Provider(s) to Import</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Choose which integrations to import. They will run one after another.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
              {configuredProviders.map(key => (
                <label
                  key={key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius)',
                    border: `1px solid ${selectedProviders[key] ? 'var(--primary)' : 'var(--border)'}`,
                    background: selectedProviders[key] ? 'rgba(14, 165, 233, 0.05)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={!!selectedProviders[key]}
                    onChange={() => toggleProvider(key)}
                    style={{
                      width: '18px',
                      height: '18px',
                      accentColor: 'var(--primary)',
                      cursor: 'pointer',
                    }}
                  />
                  <div style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center' }}>
                    {PROVIDER_META[key]?.icon || null}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem', flex: 1 }}>
                    {PROVIDER_META[key]?.label || key}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {PROVIDER_META[key]?.description || ''}
                  </span>
                </label>
              ))}
            </div>

            <div className="import-modal-actions">
              <button className="btn" onClick={() => setImportState({ status: 'idle' })}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
              >
                Import Selected ({Object.values(selectedProviders).filter(Boolean).length})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import progress modal */}
      {(importState.status === 'importing' || importState.status === 'success' || importState.status === 'error') && (
        <div className="import-modal-overlay" onClick={() => {
          if (importState.status === 'success' || importState.status === 'error') {
            handleSuccessClose();
          }
        }}>
          <div className="import-modal" onClick={(e) => e.stopPropagation()}>
            {importState.status === 'importing' && (
              <>
                <div className="import-modal-icon"><RefreshCw size={32} className="animate-spin" /></div>
                <h2>{isCancelling ? 'Cancelling Import...' : 'Importing Resources'}</h2>

                {isCancelling ? (
                  <p className="import-progress-message">Cancelling import... This may take a moment.</p>
                ) : importState.progress ? (
                  <>
                    {/* Current integration badge */}
                    {importState.progress.current_integration && (
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                        padding: '0.25rem 0.75rem',
                        background: 'rgba(14, 165, 233, 0.1)',
                        borderRadius: '999px',
                        fontSize: '0.8125rem',
                        color: 'var(--primary)',
                        fontWeight: 600,
                        marginBottom: '0.75rem',
                      }}>
                        {PROVIDER_META[importState.progress.current_integration]?.icon || null}
                        {PROVIDER_META[importState.progress.current_integration]?.label || importState.progress.current_integration}
                      </div>
                    )}

                    {/* Progress bar */}
                    <div className="import-progress-bar-track">
                      <div
                        className="import-progress-bar-fill"
                        style={{ width: `${Math.max(importState.progress.progress, 5)}%` }}
                      />
                    </div>
                    <span className="import-progress-pct">{importState.progress.progress}%</span>

                    {/* Phase and message */}
                    <p className="import-progress-message">
                      {importState.progress.current_message || importState.progress.message}
                    </p>
                  </>
                ) : (
                  <p>Starting import...</p>
                )}

                {reconnecting && (
                  <div style={{
                    padding: '0.625rem 0.75rem', marginBottom: '0.75rem',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.2)',
                    borderRadius: 'var(--radius)', color: 'var(--warning)',
                    fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
                  }}>
                    <RefreshCw size={14} className="animate-spin" />
                    Connection lost — retrying… The import continues in the background.
                  </div>
                )}

                <div className="import-modal-actions">
                  <button className="btn" onClick={handleCancelImport} disabled={isCancelling}>
                    {isCancelling ? 'Cancelling...' : 'Cancel'}
                  </button>
                </div>
              </>
            )}

            {importState.status === 'success' && (
              <>
                <div className="import-modal-icon import-success"><Check size={32} /></div>
                <h2>Import Complete</h2>
                <div className="import-summary">
                  <div className="import-stat">
                    <span className="import-stat-value">{importState.resources}</span>
                    <span className="import-stat-label">Discovered</span>
                  </div>
                  <div className="import-stat">
                    <span className="import-stat-value">{importState.stored}</span>
                    <span className="import-stat-label">Assets Stored</span>
                  </div>
                  <div className="import-stat">
                    <span className="import-stat-value">{importState.relationships}</span>
                    <span className="import-stat-label">Relationships</span>
                  </div>
                </div>

                {/* Results per provider */}
                {Object.keys(importState.providerResults).length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem', width: '100%' }}>
                    {Object.entries(importState.providerResults).map(([provider, result]: [string, any]) => (
                      <div
                        key={provider}
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: result.status === 'error' ? '0.25rem' : '0',
                          padding: '0.625rem 0.75rem',
                          background: result.status === 'error' ? 'rgba(239, 68, 68, 0.05)' : 'rgba(255,255,255,0.03)',
                          borderRadius: 'var(--radius)',
                          border: result.status === 'error' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid var(--border)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center' }}>
                            {PROVIDER_META[provider]?.icon || null}
                          </div>
                          <span style={{ fontWeight: 600, fontSize: '0.8125rem', flex: 1 }}>
                            {PROVIDER_META[provider]?.label || provider}
                          </span>
                          {result.status === 'error' ? (
                            <span style={{ fontSize: '0.75rem', color: 'var(--danger)', fontWeight: 500 }}>
                              Failed
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>
                              {result.assets_stored ?? 0} assets
                            </span>
                          )}
                        </div>
                        {/* Show error detail when a provider fails */}
                        {result.status === 'error' && result.error && (
                          <div style={{
                            fontSize: '0.6875rem',
                            color: 'var(--danger)',
                            marginTop: '0.25rem',
                            padding: '0.375rem 0.5rem',
                            background: 'rgba(239, 68, 68, 0.08)',
                            borderRadius: '4px',
                            lineHeight: 1.4,
                            wordBreak: 'break-word',
                          }}>
                            {result.error}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Warnings after completion */}
                {(() => {
                  const warnings = importState.warnings;
                  if (!warnings || warnings.length === 0) return null;
                  const grouped: Record<string, WarningEntry[]> = {};
                  for (const w of warnings) {
                    if (!grouped[w.service]) grouped[w.service] = [];
                    grouped[w.service].push(w);
                  }
                  const entries = Object.entries(grouped);
                  return (
                    <div style={{
                      marginTop: '0.75rem',
                      padding: '0.75rem',
                      backgroundColor: 'rgba(255, 159, 67, 0.08)',
                      border: '1px solid rgba(255, 159, 67, 0.2)',
                      borderRadius: 'var(--radius)',
                      textAlign: 'left',
                      maxHeight: '240px',
                      overflowY: 'auto',
                      width: '100%',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--warning)', fontWeight: 600, fontSize: '0.8125rem' }}>
                        <AlertTriangle size={14} /> Insufficient Permissions
                      </div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                        The following services reported permission errors during discovery. Some resources may not have been fully imported.
                      </p>
                      {entries.map(([svc, warns]) => (
                        <div key={svc} style={{ marginBottom: '0.75rem' }}>
                          <div style={{
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            color: 'var(--text-main)',
                            marginBottom: '0.35rem',
                            padding: '0.3rem 0.6rem',
                            backgroundColor: 'rgba(255, 159, 67, 0.08)',
                            borderRadius: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                          }}>
                            <span>{svc}</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                              {warns.length} action{warns.length !== 1 ? 's' : ''} denied
                            </span>
                          </div>
                          {warns.map((w, i) => (
                            <div key={i} style={{
                              fontSize: '0.75rem',
                              color: 'var(--text-muted)',
                              margin: '0 0 0.3rem 0.75rem',
                              lineHeight: 1.4,
                              paddingLeft: '0.5rem',
                              borderLeft: '2px solid rgba(255, 159, 67, 0.2)',
                            }}>
                              <div>
                                <span style={{
                                  fontFamily: 'monospace',
                                  fontSize: '0.75rem',
                                  color: 'var(--warning)',
                                  fontWeight: 500,
                                }}>
                                  {w.action}
                                </span>
                              </div>
                              {w.resource && (
                                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                                  Resource: {w.resource.length > 60 ? w.resource.slice(0, 60) + '...' : w.resource}
                                </div>
                              )}
                              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.1rem', opacity: 0.7 }}>
                                Table: {w.table}
                              </div>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  );
                })()}

                <div className="import-modal-actions">
                  {failedProviders.length > 0 && (
                    <button className="btn" onClick={() => startImport(failedProviders)}>
                      Retry Failed ({failedProviders.length})
                    </button>
                  )}
                  <button className="btn btn-primary" onClick={handleSuccessClose}>
                    View Assets
                  </button>
                </div>
              </>
            )}

            {importState.status === 'error' && (
              <>
                <div className="import-modal-icon import-error"><X size={32} /></div>
                <h2>Import Failed</h2>
                <p className="import-error-message">{importState.message}</p>
                <div className="import-modal-actions">
                  <button className="btn" onClick={handleSuccessClose}>Close</button>
                  {connectionLost && jobIdRef.current ? (
                    <button className="btn btn-primary" onClick={handleReconnect}>Reconnect</button>
                  ) : (
                    <>
                      <button className="btn btn-primary" onClick={handleRetry}>Retry Now</button>
                      <button className="btn" onClick={openProviderPicker}>Choose Providers</button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}



      {loading ? (
        <div className="loading">Loading assets...</div>
      ) : filteredAssets.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <Package size={48} />
            <h3>No {label} Assets Found</h3>
            <p>Import resources from a provider to see them here.</p>
          </div>
        </div>
      ) : (
        <div className="assets-page-body">
          {Object.entries(grouped).map(([typeName, items]) => (
            <div key={typeName} className="card" style={{ marginBottom: '1rem' }}>
              <div className="card-header">
                <h3>{typeName}</h3>
                <span className="assets-count">{items.length}</span>
              </div>
              <table className="assets-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Provider</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((asset) => (
                    <tr key={asset.id}>
                      <td className="asset-name-cell" title={asset.display_name || asset.provider_resource_id}>
                        {asset.display_name || asset.provider_resource_id}
                      </td>
                      <td>
                        {asset.provider && (
                          <span className="provider-badge">{asset.provider}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CanonicalCategoryPage;
