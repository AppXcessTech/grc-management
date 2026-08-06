import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCategoryBySlug } from '../../data/integrations';
import { PlugZap, ExternalLink, Loader2, CheckCircle, XCircle, AlertTriangle, Cloud, Fingerprint, Database, ListChecks, Code2, GitBranch, MessageSquare, Search, X } from 'lucide-react';
import api from '../../services/api';
import { saveActiveImportJob, loadActiveImportJob, clearActiveImportJob } from '../../utils/activeImportJob';
import { useOnlineStatus } from '../../utils/useOnlineStatus';

const VENDOR_ROUTES: Record<string, Record<string, string>> = {
  'cloud-providers': {
    'AWS': '/integrations/cloud-providers/aws',
    'Azure': '/integrations/cloud-providers/azure',
    'GCP': '/integrations/cloud-providers/gcp',
  },
  'identity-providers': {
    'Okta': '/integrations/identity-providers/okta',
  },
  'version-control': {
    'GitHub': '/integrations/version-control/github',
    'GitLab': '/integrations/version-control/gitlab',
    'Bitbucket': '/integrations/version-control/bitbucket',
  },
  'endpoint-security': {
    'CrowdStrike': '/integrations/endpoint-security/crowdstrike',
    'SentinelOne': '/integrations/endpoint-security/sentinelone',
  },
  'task-management': {
    'Jira': '/integrations/task-management/jira',
    'ServiceNow': '/integrations/task-management/servicenow',
    'Linear': '/integrations/task-management/linear',
  },
  'communication-platforms': {
    'Slack': '/integrations/communication-platforms/slack',
    'Microsoft Teams': '/integrations/communication-platforms/teams',
    'Zoom': '/integrations/communication-platforms/zoom',
  },
  'observability': {
    'Datadog': '/integrations/observability/datadog',
    'New Relic': '/integrations/observability/newrelic',
    'Splunk': '/integrations/observability/splunk',
  },
  'incident-management': {
    'PagerDuty': '/integrations/incident-management/pagerduty',
    'Opsgenie': '/integrations/incident-management/opsgenie',
  },
  'data-warehouse-providers': {
    'Snowflake': '/integrations/data-warehouse-providers/snowflake',
    'Databricks': '/integrations/data-warehouse-providers/databricks',
  },
  'datastore-providers': {
    'MongoDB': '/integrations/datastore-providers/mongodb',
  },
  'crm-platforms': {
    'Salesforce': '/integrations/crm-platforms/salesforce',
    'HubSpot': '/integrations/crm-platforms/hubspot',
  },
};

// Integrations that have actual import/sync functionality
const IMPORTABLE_INTEGRATIONS: Record<string, string[]> = {
  'cloud-providers': ['AWS', 'Azure', 'GCP'],
  'identity-providers': ['Okta'],
  'version-control': ['GitHub', 'GitLab', 'Bitbucket'],
  'communication-platforms': ['Slack'],
};

// Provider icon mapping
const PROVIDER_ICONS: Record<string, React.ReactNode> = {
  aws: <Cloud size={14} />,
  azure: <Database size={14} />,
  gcp: <Cloud size={14} />,
  okta: <Fingerprint size={14} />,
  github: <Code2 size={14} />,
  gitlab: <GitBranch size={14} />,
  bitbucket: <GitBranch size={14} />,
  slack: <MessageSquare size={14} />,
};

const PROVIDER_LABELS: Record<string, string> = {
  aws: 'AWS',
  azure: 'Azure',
  gcp: 'GCP',
  okta: 'Okta',
  github: 'GitHub',
  gitlab: 'GitLab',
  bitbucket: 'Bitbucket',
  slack: 'Slack',
};

// Number of ms between status-poll requests
const POLL_INTERVAL_MS = 1500;
// Number of consecutive failed status checks (network/server blips) to tolerate
// before declaring the connection lost. At 1.5s/check this is ~9 seconds.
const MAX_POLL_FAILURES = 6;

const IntegrationPlaceholder = () => {
  const { integration } = useParams();
  const navigate = useNavigate();
  const category = integration ? getCategoryBySlug(integration) : undefined;
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [bulkConfig, setBulkConfig] = useState<{
    aws_configured: boolean;
    azure_configured: boolean;
    okta_configured: boolean;
    github_configured: boolean;
    gcp_configured: boolean;
    gitlab_configured: boolean;
    bitbucket_configured: boolean;
    slack_configured: boolean;
    integrations_to_run: string[];
  } | null>(null);
  const [configLoading, setConfigLoading] = useState(true);

  // Integration selection modal state
  const [showPicker, setShowPicker] = useState(false);
  const [selectedIntegrations, setSelectedIntegrations] = useState<Record<string, boolean>>({});

  // Bulk import job state
  const [showModal, setShowModal] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [cancelFailed, setCancelFailed] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [connectionLost, setConnectionLost] = useState(false);
  const pollFailuresRef = useRef(0);
  const [jobStatus, setJobStatus] = useState<string>('idle');
  const [jobProgress, setJobProgress] = useState(0);
  const [jobPhase, setJobPhase] = useState('');
  const [jobMessage, setJobMessage] = useState('');
  const [jobCurrentIntegration, setJobCurrentIntegration] = useState('');
  const [jobCurrentMessage, setJobCurrentMessage] = useState('');
  const [jobResults, setJobResults] = useState<Record<string, any>>({});
  const [jobError, setJobError] = useState<string | null>(null);
  // The integrations that were requested for the current/last import. Used by
  // the Retry button (the picker's selection is cleared once it closes, so a
  // plain handleBulkImport call would have nothing to import).
  const lastImportIntegrationsRef = useRef<string[]>([]);

  // Check which integrations are configured
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

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const startPolling = useCallback((jId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/api/integrations/bulk/sync-status/${jId}`);
        const data = res.data;
        pollFailuresRef.current = 0;
        setReconnecting(false);
        setJobStatus(data.status);
        setJobProgress(data.progress);
        setJobPhase(data.phase);
        setJobMessage(data.message);
        setJobCurrentIntegration(data.current_integration);
        setJobCurrentMessage(data.current_message);
        setJobError(data.error);
        if (data.results && Object.keys(data.results).length > 0) {
          setJobResults(data.results);
        }
        if (data.status === 'completed' || data.status === 'error' || data.status === 'cancelled') {
          clearActiveImportJob();
          if (pollingRef.current) clearInterval(pollingRef.current);
          pollingRef.current = null;
          if (data.status === 'cancelled') {
            setShowModal(false);
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
    setShowModal(true);
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
      if (showModal && !connectionLost) setReconnecting(true);
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
  }, [isOnline, showModal, connectionLost, jobId, startPolling]);

  // Open the integration picker modal — start with nothing selected
  const openPicker = () => {
    setSelectedIntegrations({});
    setShowPicker(true);
  };

  // Toggle a single integration checkbox
  const toggleIntegration = (key: string) => {
    setSelectedIntegrations(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Start a bulk import for the given integration list and begin polling it.
  const startImport = useCallback(async (toImport: string[]) => {
    if (toImport.length === 0) return;
    lastImportIntegrationsRef.current = toImport;

    setShowPicker(false);
    setShowModal(true);
    setCancelling(false);
    setCancelFailed(false);
    setReconnecting(false);
    setConnectionLost(false);
    pollFailuresRef.current = 0;
    setJobStatus('starting');
    setJobProgress(0);
    setJobMessage('Starting bulk import...');
    setJobResults({});
    setJobError(null);

    try {
      const res = await api.post('/api/integrations/bulk/sync', { integrations: toImport });
      const jId = res.data.job_id;
      setJobId(jId);
      saveActiveImportJob(jId);
      setJobStatus('pending');
      startPolling(jId);
    } catch (err: any) {
      clearActiveImportJob();
      setJobStatus('error');
      setJobError(err.response?.data?.detail || 'Failed to start import');
    }
  }, [startPolling]);

  // Launch the import with the user's selected integrations
  const handleBulkImport = async () => {
    const toImport = Object.entries(selectedIntegrations)
      .filter(([, checked]) => checked)
      .map(([key]) => key);
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
      setShowModal(false);
      setShowPicker(false);
      return;
    }
    setCancelling(true);
    try {
      await api.post(`/api/integrations/bulk/cancel/${id}`);
      clearActiveImportJob();
      setJobId(null);
      setShowModal(false);
      setShowPicker(false);
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
      setShowModal(false);
    }
  };

  const closeModal = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = null;
    setShowModal(false);
    setShowPicker(false);
  };

  // Map from display name (e.g. "AWS") to internal key (e.g. "aws")
  const PROVIDER_NAME_TO_KEY: Record<string, string> = {
    AWS: 'aws',
    Azure: 'azure',
    GCP: 'gcp',
    Okta: 'okta',
    GitHub: 'github',
    GitLab: 'gitlab',
    Bitbucket: 'bitbucket',
    Slack: 'slack',
  };

  // Map from internal key to bulk config boolean field
  const PROVIDER_TO_CONFIG_FIELD: Record<string, 'aws_configured' | 'azure_configured' | 'okta_configured' | 'github_configured' | 'gcp_configured' | 'gitlab_configured' | 'bitbucket_configured' | 'slack_configured'> = {
    aws: 'aws_configured',
    azure: 'azure_configured',
    gcp: 'gcp_configured',
    okta: 'okta_configured',
    github: 'github_configured',
    gitlab: 'gitlab_configured',
    bitbucket: 'bitbucket_configured',
    slack: 'slack_configured',
  };

  /**
   * Return only the integrations that:
   *  - belong to the current category (e.g. cloud-providers → AWS, Azure)
   *  - AND are actually configured
   */
  const getImportableIntegrations = (): string[] => {
    if (!integration || !bulkConfig) return [];
    const allowedForCategory = IMPORTABLE_INTEGRATIONS[integration];
    if (!allowedForCategory) return [];

    return allowedForCategory
      .map(name => PROVIDER_NAME_TO_KEY[name])
      .filter(key => key && bulkConfig[PROVIDER_TO_CONFIG_FIELD[key]]);
  };

  const importable = getImportableIntegrations();
  const hasImportable = importable.length > 0;
  const categoryHasImports = integration ? IMPORTABLE_INTEGRATIONS[integration] : undefined;
  const [searchQuery, setSearchQuery] = useState('');

  if (!category) {
    return (
      <div className="card">
        <h1>Integrations</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Select a category from the sidebar.
        </p>
      </div>
    );
  }

  const filteredVendors = searchQuery
    ? category.vendors.filter(v =>
        v.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : category.vendors;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <PlugZap size={28} color="var(--primary)" />
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: 0 }}>{category.name}</h1>
        </div>
        {/* Select integrations to import button */}
        {categoryHasImports && !configLoading && hasImportable && (
          <button
            className="btn btn-primary"
            onClick={openPicker}
            disabled={jobStatus === 'running' || jobStatus === 'pending' || jobStatus === 'starting'}
            style={{ gap: '0.5rem', whiteSpace: 'nowrap' }}
          >
            <ListChecks size={16} />
            Import
          </button>
        )}
      </div>

      {/* Status banner when integrations exist but none configured */}
      {categoryHasImports && !configLoading && !hasImportable && (
        <div
          style={{
            padding: '0.75rem 1rem',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: 'var(--radius)',
            color: 'var(--warning)',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '1.5rem',
          }}
        >
          <AlertTriangle size={16} />
          Configure an integration below to enable bulk import.
        </div>
      )}

      {/* Integration selection modal — medium popup with checkboxes */}
      {showPicker && (
        <div className="import-modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget) setShowPicker(false);
        }}>
          <div className="import-modal" style={{ maxWidth: '420px' }}>
            <div className="import-modal-icon">
              <ListChecks size={28} />
            </div>
            <h2>Select Integrations to Import</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Choose which integrations to import. They will run one after another.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
              {importable.map(key => (
                <label
                  key={key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius)',
                    border: `1px solid ${selectedIntegrations[key] ? 'var(--primary)' : 'var(--border)'}`,
                    background: selectedIntegrations[key] ? 'rgba(14, 165, 233, 0.05)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={!!selectedIntegrations[key]}
                    onChange={() => toggleIntegration(key)}
                    style={{
                      width: '18px',
                      height: '18px',
                      accentColor: 'var(--primary)',
                      cursor: 'pointer',
                    }}
                  />
                  <div style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center' }}>
                    {PROVIDER_ICONS[key] || null}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem', flex: 1 }}>
                    {PROVIDER_LABELS[key] || key}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {key === 'aws' ? 'Cloud resources' :
                     key === 'azure' ? 'Cloud resources' :
                     key === 'okta' ? 'People assets' :
                     key === 'github' ? 'Repositories & code' :
                     key === 'gitlab' ? 'Repositories & code' :
                     key === 'bitbucket' ? 'Repositories & code' :
                     key === 'slack' ? 'Users, channels & logs' : ''}
                  </span>
                </label>
              ))}
            </div>

            <div className="import-modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowPicker(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleBulkImport}
              >
                Import Selected ({Object.values(selectedIntegrations).filter(Boolean).length})
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search bar */}
      {category.vendors.length > 6 && (
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
            placeholder="Search integrations..."
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

      {/* Vendor cards */}
      {searchQuery && filteredVendors.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <Search size={32} style={{ opacity: 0.3, marginBottom: '0.75rem', color: 'var(--text-muted)' }} />
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No integrations match "{searchQuery}"
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {filteredVendors.map((vendor) => {
          const route = VENDOR_ROUTES[category.slug]?.[vendor.name];
          return (
            <div
              key={vendor.name}
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '1.25rem 1.5rem',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: route ? 'pointer' : 'default',
              }}
              onClick={() => route && navigate(route)}
              onMouseEnter={(e) => {
                if (route) {
                  e.currentTarget.style.borderColor = 'var(--primary)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = 'var(--shadow)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: '8px',
                    background: 'rgba(14, 165, 233, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: 'var(--primary)',
                  }}
                >
                  {vendor.name.charAt(0)}
                </div>
                <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>{vendor.name}</span>
              </div>
              {route && <ExternalLink size={18} color="var(--primary)" style={{ opacity: 0.7 }} />}
            </div>
          );
        })}
      </div>
      )}

      {/* Progress Modal */}
      {showModal && (
        <div className="import-modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget && (jobStatus === 'completed' || jobStatus === 'error')) {
            closeModal();
          }
        }}>
          <div className="import-modal" style={{ maxWidth: '480px' }}>
            {/* Icon */}
            <div
              className={`import-modal-icon ${
                jobStatus === 'completed' ? 'import-success' :
                jobStatus === 'error' ? 'import-error' : ''
              }`}
            >
              {jobStatus === 'completed' ? <CheckCircle size={28} /> :
               jobStatus === 'error' ? <XCircle size={28} /> :
               <Loader2 size={28} className="animate-spin" />}
            </div>

            <h2>
              {jobStatus === 'completed' ? 'Import Complete' :
               jobStatus === 'error' ? 'Import Failed' :
               cancelling ? 'Cancelling Import...' :
               'Importing Resources...'}
            </h2>

            {/* Progress bar */}
            {!cancelling && jobStatus !== 'completed' && jobStatus !== 'error' && (
              <>
                <div className="import-progress-bar-track">
                  <div
                    className="import-progress-bar-fill"
                    style={{ width: `${Math.max(jobProgress, 5)}%` }}
                  />
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

            {/* Current phase */}
            {jobCurrentIntegration && (
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                  padding: '0.25rem 0.75rem',
                  background: 'rgba(14, 165, 233, 0.1)',
                  borderRadius: '999px',
                  fontSize: '0.8125rem',
                  color: 'var(--primary)',
                  fontWeight: 600,
                  marginBottom: '0.5rem',
                }}
              >
                {PROVIDER_ICONS[jobCurrentIntegration] || null}
                {PROVIDER_LABELS[jobCurrentIntegration] || jobCurrentIntegration}
              </div>
            )}

            <p className="import-progress-message">
              {jobStatus === 'completed' ? 'All configured integrations have been imported successfully.' :
               jobStatus === 'error' ? (jobError || 'An error occurred during import.') :
               cancelling ? 'Cancelling import... This may take a moment.' :
               jobCurrentMessage || jobMessage || 'Working...'}
            </p>

            {/* Results summary */}
            {jobStatus === 'completed' && Object.keys(jobResults).length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {Object.entries(jobResults).map(([provider, result]: [string, any]) => (
                  <div
                    key={provider}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem 0.75rem',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: 'var(--radius)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <div style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center' }}>
                      {PROVIDER_ICONS[provider] || null}
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.8125rem', flex: 1 }}>
                      {PROVIDER_LABELS[provider] || provider}
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

            {/* Error details */}
            {jobError && jobStatus === 'error' && (
              <p className="import-error-message">{jobError}</p>
            )}

            {/* Actions */}
            <div className="import-modal-actions">
              {!cancelling && (jobStatus !== 'completed' && jobStatus !== 'error') && (
                <button className="btn" onClick={handleCancelImport} style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                  Cancel Import
                </button>
              )}
              {(jobStatus === 'completed' || jobStatus === 'error') && (
                <button className="btn btn-primary" onClick={closeModal}>
                  {jobStatus === 'completed' ? 'Done' : 'Close'}
                </button>
              )}
              {jobStatus === 'completed' && failedProviders.length > 0 && (
                <button className="btn btn-secondary" onClick={() => startImport(failedProviders)}>
                  Retry Failed ({failedProviders.length})
                </button>
              )}
              {jobStatus === 'error' && !cancelFailed && !connectionLost && (
                <button className="btn btn-secondary" onClick={handleRetry}>
                  Retry Now
                </button>
              )}
              {jobStatus === 'error' && cancelFailed && (
                <button className="btn btn-secondary" onClick={handleCancelImport}>
                  Try Again
                </button>
              )}
              {jobStatus === 'error' && connectionLost && (
                <button className="btn btn-primary" onClick={handleReconnect}>
                  Reconnect
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationPlaceholder;
