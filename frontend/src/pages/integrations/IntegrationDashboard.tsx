import { useState, useEffect, useRef, useCallback } from 'react';
import { Cloud, Fingerprint, Database, Code2, GitBranch, MessageSquare, Loader2, CheckCircle, XCircle, ListChecks, Upload, Search, X } from 'lucide-react';
import api from '../../services/api';
import { saveActiveImportJob, loadActiveImportJob, clearActiveImportJob } from '../../utils/activeImportJob';
import { useOnlineStatus } from '../../utils/useOnlineStatus';

const ALL_INTEGRATIONS = ['aws', 'azure', 'gcp', 'okta', 'github', 'gitlab', 'bitbucket', 'microsoft365', 'slack'];

const INTEGRATION_META: Record<string, { label: string; icon: React.ReactNode; category: string; description: string }> = {
  aws: {
    label: 'AWS',
    icon: <Cloud size={18} />,
    category: 'Cloud Providers',
    description: 'IAM users, S3 buckets, EC2 instances, KMS keys, and more',
  },
  azure: {
    label: 'Azure',
    icon: <Database size={18} />,
    category: 'Cloud Providers',
    description: 'Virtual machines, Storage accounts, SQL servers, and more',
  },
  gcp: {
    label: 'GCP',
    icon: <Cloud size={18} />,
    category: 'Cloud Providers',
    description: 'Compute instances, Storage buckets, IAM roles, and more',
  },
  okta: {
    label: 'Okta',
    icon: <Fingerprint size={18} />,
    category: 'Identity Providers',
    description: 'Users, Groups, Applications, Auth Policies, Devices & more',
  },
  github: {
    label: 'GitHub',
    icon: <Code2 size={18} />,
    category: 'Version Control Systems',
    description: 'Repositories, teams, members, secrets, workflows, and more',
  },
  gitlab: {
    label: 'GitLab',
    icon: <GitBranch size={18} />,
    category: 'Version Control Systems',
    description: 'Projects, groups, members, variables, pipelines, and more',
  },
  bitbucket: {
    label: 'Bitbucket',
    icon: <GitBranch size={18} />,
    category: 'Version Control Systems',
    description: 'Repositories, projects, workspaces, members, and branch restrictions',
  },
  microsoft365: {
    label: 'Microsoft 365 Teams',
    icon: <Fingerprint size={18} />,
    category: 'Communication Platforms',
    description: 'Teams, team members, and Microsoft 365 resources',
  },
  slack: {
    label: 'Slack',
    icon: <MessageSquare size={18} />,
    category: 'Communication Platforms',
    description: 'Users, channels, user groups, access logs, and workspace connection',
  },
};

const POLL_INTERVAL_MS = 1500;
// Number of consecutive failed status checks (network/server blips) to tolerate
// before declaring the connection lost. At 1.5s/check this is ~9 seconds.
const MAX_POLL_FAILURES = 6;

const IntegrationDashboard = () => {
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [bulkConfig, setBulkConfig] = useState<Record<string, boolean> | null>(null);
  const [configLoading, setConfigLoading] = useState(true);

  // Picker state
  const [showPicker, setShowPicker] = useState(false);
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  // Job state
  const [jobId, setJobId] = useState<string | null>(null);
  const [showJob, setShowJob] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelFailed, setCancelFailed] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [connectionLost, setConnectionLost] = useState(false);
  const [jobStatus, setJobStatus] = useState('idle');
  const pollFailuresRef = useRef(0);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobMessage, setJobMessage] = useState('');
  const [jobCurrentIntegration, setJobCurrentIntegration] = useState('');
  const [jobCurrentMessage, setJobCurrentMessage] = useState('');
  const [jobResults, setJobResults] = useState<Record<string, any>>({});
  const [jobError, setJobError] = useState<string | null>(null);
  // The integrations that were requested for the current/last import. Used by
  // the Retry button (the picker's `selected` state is cleared once it closes,
  // so a plain handleImport call would have nothing to import).
  const lastImportIntegrationsRef = useRef<string[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/integrations/bulk/config');
        setBulkConfig(res.data);
      } catch {
        setBulkConfig(null);
      } finally {
        setConfigLoading(false);
      }
    })();
  }, []);

  useEffect(() => () => { if (pollingRef.current) clearInterval(pollingRef.current); }, []);

  const startPolling = useCallback((jId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/api/integrations/bulk/sync-status/${jId}`);
        const d = res.data;
        pollFailuresRef.current = 0;
        setReconnecting(false);
        setJobStatus(d.status);
        setJobProgress(d.progress);
        setJobMessage(d.message);
        setJobCurrentIntegration(d.current_integration);
        setJobCurrentMessage(d.current_message);
        setJobError(d.error);
        if (d.results && Object.keys(d.results).length > 0) setJobResults(d.results);
        if (d.status === 'completed' || d.status === 'error' || d.status === 'cancelled') {
          clearActiveImportJob();
          if (pollingRef.current) clearInterval(pollingRef.current);
          pollingRef.current = null;
          if (d.status === 'cancelled') {
            setShowJob(false);
          }
        }
      } catch (err: any) {
        // 404 = the job no longer exists (e.g. the server restarted). This is
        // not a network blip — stop polling and tell the user.
        if (err?.response?.status === 404) {
          clearActiveImportJob();
          if (pollingRef.current) clearInterval(pollingRef.current);
          pollingRef.current = null;
          setReconnecting(false);
          setConnectionLost(false);
          setJobStatus('error');
          setJobError('This import job no longer exists (the server may have restarted). Start a new import.');
          return;
        }
        // Transient network/server error — the import keeps running in the
        // background. Tolerate a few consecutive failures before giving up.
        pollFailuresRef.current += 1;
        if (pollFailuresRef.current >= MAX_POLL_FAILURES) {
          if (pollingRef.current) clearInterval(pollingRef.current);
          pollingRef.current = null;
          setReconnecting(false);
          setConnectionLost(true);
          setJobStatus('error');
          setJobError('Connection to the server was lost. The import may still be running in the background — click Reconnect to check again.');
        } else {
          setReconnecting(true);
        }
      }
    }, POLL_INTERVAL_MS);
  }, []);

  // Re-attach to a bulk import that is still running in the background after a
  // page reload / navigation, so the user can keep watching progress.
  useEffect(() => {
    const storedJobId = loadActiveImportJob();
    if (!storedJobId) return;
    setJobId(storedJobId);
    setShowJob(true);
    setJobStatus('pending');
    startPolling(storedJobId);
  }, [startPolling]);

  // Instant network detection: react as soon as the browser reports the
  // network dropped (instead of waiting for the next poll to fail ~1.5s
  // later), and automatically resume polling when connectivity returns.
  const isOnline = useOnlineStatus();
  useEffect(() => {
    if (!isOnline) {
      // Network just dropped — surface it immediately if an import is visible
      // (but don't overlap the explicit connection-lost error state).
      if (showJob && !connectionLost) setReconnecting(true);
      return;
    }
    // Back online — clear the transient banner and stop counting failures.
    setReconnecting(false);
    pollFailuresRef.current = 0;
    if (connectionLost) {
      setConnectionLost(false);
      setJobError(null);
      if (jobId) {
        setJobStatus('pending');
        setJobProgress(0);
        startPolling(jobId);
      }
    }
  }, [isOnline, showJob, connectionLost, jobId, startPolling]);

  const openPicker = () => {
    setSelected({});
    setShowPicker(true);
  };

  // Start a bulk import for the given integration list and begin polling it.
  const startImport = useCallback(async (toImport: string[]) => {
    if (toImport.length === 0) return;
    lastImportIntegrationsRef.current = toImport;

    setShowPicker(false);
    setShowJob(true);
    setCancelling(false);
    setCancelFailed(false);
    setReconnecting(false);
    setConnectionLost(false);
    pollFailuresRef.current = 0;
    setJobStatus('starting');
    setJobProgress(0);
    setJobMessage('Starting import...');
    setJobResults({});
    setJobError(null);

    try {
      const res = await api.post('/api/integrations/bulk/sync', { integrations: toImport });
      const jId = res.data.job_id;
      setJobId(jId);
      saveActiveImportJob(jId);
      startPolling(jId);
    } catch (err: any) {
      clearActiveImportJob();
      setJobStatus('error');
      setJobError(err.response?.data?.detail || 'Failed to start import');
    }
  }, [startPolling]);

  const handleImport = async () => {
    const toImport = Object.entries(selected).filter(([, v]) => v).map(([k]) => k);
    await startImport(toImport);
  };

  // Retry the last import (same integrations), e.g. after a network failure.
  // If nothing was started this session (e.g. a page reload followed by a 404),
  // fall back to opening the picker so the button never silently no-ops.
  const handleRetry = async () => {
    if (lastImportIntegrationsRef.current.length === 0) {
      openPicker();
      return;
    }
    await startImport(lastImportIntegrationsRef.current);
  };

  // Providers that failed in the last job — used for the "Retry Failed" action.
  const failedProviders = Object.entries(jobResults)
    .filter(([, r]: [string, any]) => r?.status === 'error')
    .map(([k]) => k);

  const handleCancelImport = async () => {
    // Stop polling immediately, but keep the modal open so the user can see
    // that the cancellation was accepted (or that it failed and they can retry).
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = null;
    const id = jobId;
    if (!id) {
      setShowJob(false);
      return;
    }
    setCancelling(true);
    try {
      await api.post(`/api/integrations/bulk/cancel/${id}`);
      clearActiveImportJob();
      setJobId(null);
      setShowJob(false);
    } catch {
      setCancelling(false);
      setCancelFailed(true);
      setJobStatus('error');
      setJobError('Failed to cancel the import. The import may still be running — please try again.');
    }
  };

  const handleReconnect = () => {
    setReconnecting(false);
    setConnectionLost(false);
    setJobError(null);
    pollFailuresRef.current = 0;
    if (jobId) {
      setJobStatus('pending');
      setJobProgress(0);
      startPolling(jobId);
    } else {
      setShowJob(false);
    }
  };

  const closeJob = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = null;
    setShowJob(false);
  };

  const configured = ALL_INTEGRATIONS.filter(k => bulkConfig?.[`${k}_configured`]);
  const hasConfigured = configured.length > 0;

  // Only integrations that are actually configured are shown on the dashboard.
  // Filter those by search query.
  const filteredIntegrations = searchQuery
    ? configured.filter(key => {
        const meta = INTEGRATION_META[key];
        const query = searchQuery.toLowerCase();
        return (
          meta.label.toLowerCase().includes(query) ||
          meta.description.toLowerCase().includes(query) ||
          meta.category.toLowerCase().includes(query)
        );
      })
    : configured;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
        <div style={{
          width: 48, height: 48, borderRadius: '12px',
          background: 'rgba(14, 165, 233, 0.1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Upload size={24} color="var(--primary)" />
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Import Dashboard</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Import resources from all your configured integrations
          </p>
        </div>
        {!configLoading && hasConfigured && (
          <button
            className="btn btn-primary"
            onClick={openPicker}
            disabled={jobStatus === 'running' || jobStatus === 'pending' || jobStatus === 'starting'}
            style={{ whiteSpace: 'nowrap' }}
          >
            <ListChecks size={16} />
            Import All ({configured.length})
          </button>
        )}
      </div>

      {/* Search bar */}
      {!configLoading && hasConfigured && (
        <div style={{ position: 'relative', marginBottom: '1.25rem', maxWidth: '400px' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '0.75rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
            }}
          />
          <input
            type="text"
            placeholder="Search integrations by name, description, or category..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem 0.5rem 2.25rem',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--text-main)',
              fontSize: '0.875rem',
              outline: 'none',
              transition: 'border-color 0.15s',
            }}
            onFocus={e => { e.currentTarget.style.borderColor = 'var(--primary)'; }}
            onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                padding: '0.25rem',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>
      )}

      {/* Integration cards */}
      {configLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
          <Loader2 size={24} className="animate-spin" />
        </div>
      ) : !hasConfigured ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
          <Upload size={40} color="var(--text-muted)" style={{ opacity: 0.4, marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.125rem', margin: '0 0 0.5rem' }}>No Integrations Configured</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: 0 }}>
            Go to the sidebar and configure an integration (e.g. AWS, Azure, GitHub, GitLab, Bitbucket, or Okta) to start importing.
          </p>
        </div>
      ) : filteredIntegrations.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <Search size={32} style={{ opacity: 0.3, marginBottom: '0.75rem', color: 'var(--text-muted)' }} />
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No integrations match "{searchQuery}"
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
          {filteredIntegrations.map(key => {
            const meta = INTEGRATION_META[key];
            return (
              <div
                key={key}
                className="card"
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '1rem',
                  padding: '1.25rem 1.5rem',
                  border: '1px solid var(--border)',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{
                  width: 44, height: 44, borderRadius: '10px',
                  background: 'rgba(14, 165, 233, 0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--primary)',
                  flexShrink: 0,
                }}>
                  {meta.icon}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9375rem' }}>{meta.label}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {meta.description}
                  </p>
                  <p style={{ margin: '0.25rem 0 0', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                    Category: {meta.category}
                  </p>
                </div>
                <CheckCircle size={16} color="var(--success)" style={{ flexShrink: 0 }} />
              </div>
            );
          })}
        </div>
      )}

      {/* Picker Modal */}
      {showPicker && (
        <div className="import-modal-overlay" onClick={e => { if (e.target === e.currentTarget) setShowPicker(false); }}>
          <div className="import-modal" style={{ maxWidth: '420px' }}>
            <div className="import-modal-icon"><ListChecks size={28} /></div>
            <h2>Select Provider(s) to Import</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Choose which integrations to import. They will run one after another.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
              {configured.map(key => (
                <label
                  key={key}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                    padding: '0.75rem 1rem', borderRadius: 'var(--radius)',
                    border: `1px solid ${selected[key] ? 'var(--primary)' : 'var(--border)'}`,
                    background: selected[key] ? 'rgba(14, 165, 233, 0.05)' : 'transparent',
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  <input type="checkbox" checked={!!selected[key]}
                    onChange={() => setSelected(prev => ({ ...prev, [key]: !prev[key] }))}
                    style={{ width: 18, height: 18, accentColor: 'var(--primary)', cursor: 'pointer' }} />
                  <div style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center' }}>
                    {INTEGRATION_META[key]?.icon || null}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem', flex: 1 }}>
                    {INTEGRATION_META[key]?.label || key}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {INTEGRATION_META[key]?.description || ''}
                  </span>
                </label>
              ))}
            </div>
            <div className="import-modal-actions">
              <button className="btn" onClick={() => setShowPicker(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleImport}>
                Import Selected ({Object.values(selected).filter(Boolean).length})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Job Progress Modal */}
      {showJob && (
        <div className="import-modal-overlay" onClick={e => {
          if (e.target === e.currentTarget && (jobStatus === 'completed' || jobStatus === 'error')) closeJob();
        }}>
          <div className="import-modal" style={{ maxWidth: '480px' }}>
            <div className={`import-modal-icon ${
              jobStatus === 'completed' ? 'import-success' : jobStatus === 'error' ? 'import-error' : ''
            }`}>
              {jobStatus === 'completed' ? <CheckCircle size={28} /> :
               jobStatus === 'error' ? <XCircle size={28} /> :
               <Loader2 size={28} className="animate-spin" />}
            </div>
            <h2>{jobStatus === 'completed' ? 'Import Complete' : jobStatus === 'error' ? 'Import Failed' : cancelling ? 'Cancelling Import...' : 'Importing Resources...'}</h2>

            {!cancelling && jobStatus !== 'completed' && jobStatus !== 'error' && (
              <>
                <div className="import-progress-bar-track">
                  <div className="import-progress-bar-fill" style={{ width: `${Math.max(jobProgress, 5)}%` }} />
                </div>
                <p className="import-progress-pct">{jobProgress}%</p>
              </>
            )}

            {reconnecting && (
              <div style={{
                padding: '0.625rem 0.75rem', marginBottom: '0.75rem',
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                border: '1px solid rgba(245, 158, 11, 0.2)',
                borderRadius: 'var(--radius)', color: 'var(--warning)',
                fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
              }}>
                <Loader2 size={14} className="animate-spin" />
                Connection lost — retrying… The import continues in the background.
              </div>
            )}

            {jobCurrentIntegration && (
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
                padding: '0.25rem 0.75rem', background: 'rgba(14, 165, 233, 0.1)',
                borderRadius: '999px', fontSize: '0.8125rem', color: 'var(--primary)',
                fontWeight: 600, marginBottom: '0.5rem',
              }}>
                {INTEGRATION_META[jobCurrentIntegration]?.icon}
                {INTEGRATION_META[jobCurrentIntegration]?.label || jobCurrentIntegration}
              </div>
            )}

            <p className="import-progress-message">
              {jobStatus === 'completed' ? 'Import complete!' :
               jobStatus === 'error' ? (jobError || 'An error occurred.') :
               cancelling ? 'Cancelling import... This may take a moment.' :
               jobCurrentMessage || jobMessage || 'Working...'}
            </p>

            {jobStatus === 'completed' && Object.keys(jobResults).length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {Object.entries(jobResults).map(([provider, result]: [string, any]) => (
                  <div key={provider} style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.5rem 0.75rem', background: 'rgba(255,255,255,0.03)',
                    borderRadius: 'var(--radius)', border: '1px solid var(--border)',
                  }}>
                    <div style={{ color: 'var(--primary)' }}>{INTEGRATION_META[provider]?.icon}</div>
                    <span style={{ fontWeight: 600, fontSize: '0.8125rem', flex: 1 }}>
                      {INTEGRATION_META[provider]?.label || provider}
                    </span>
                    {result.status === 'error' ? (
                      <XCircle size={14} color="var(--danger)" />
                    ) : (
                      <CheckCircle size={14} color="var(--success)" />
                    )}
                  </div>
                ))}
              </div>
            )}

            {jobStatus === 'completed' && failedProviders.length > 0 && (
              <p className="import-error-message" style={{ marginBottom: '0.75rem' }}>
                {failedProviders.length} provider(s) failed during import.
              </p>
            )}

            {jobError && jobStatus === 'error' && <p className="import-error-message">{jobError}</p>}

            <div className="import-modal-actions">
              {!cancelling && (jobStatus === 'running' || jobStatus === 'pending' || jobStatus === 'starting') && (
                <button className="btn" onClick={handleCancelImport} style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                  Cancel Import
                </button>
              )}
              {(jobStatus === 'completed' || jobStatus === 'error') && (
                <button className="btn btn-primary" onClick={closeJob}>
                  {jobStatus === 'completed' ? 'Done' : 'Close'}
                </button>
              )}
              {jobStatus === 'completed' && failedProviders.length > 0 && (
                <button className="btn btn-secondary" onClick={() => startImport(failedProviders)}>
                  Retry Failed ({failedProviders.length})
                </button>
              )}
              {jobStatus === 'error' && !cancelFailed && !connectionLost && <button className="btn btn-secondary" onClick={handleRetry}>Retry Now</button>}
              {jobStatus === 'error' && cancelFailed && <button className="btn btn-secondary" onClick={handleCancelImport}>Try Again</button>}
              {jobStatus === 'error' && connectionLost && <button className="btn btn-primary" onClick={handleReconnect}>Reconnect</button>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationDashboard;
