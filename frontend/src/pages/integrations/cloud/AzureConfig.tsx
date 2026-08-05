import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import api from '../../../services/api';

const AZURE_REGIONS = [
  { value: 'eastus', label: 'East US' },
  { value: 'eastus2', label: 'East US 2' },
  { value: 'westus', label: 'West US' },
  { value: 'westus2', label: 'West US 2' },
  { value: 'westus3', label: 'West US 3' },
  { value: 'centralus', label: 'Central US' },
  { value: 'northcentralus', label: 'North Central US' },
  { value: 'southcentralus', label: 'South Central US' },
  { value: 'northeurope', label: 'North Europe' },
  { value: 'westeurope', label: 'West Europe' },
  { value: 'eastasia', label: 'East Asia' },
  { value: 'southeastasia', label: 'Southeast Asia' },
  { value: 'uksouth', label: 'UK South' },
  { value: 'ukwest', label: 'UK West' },
  { value: 'canadacentral', label: 'Canada Central' },
  { value: 'brazilsouth', label: 'Brazil South' },
  { value: 'australiaeast', label: 'Australia East' },
  { value: 'japaneast', label: 'Japan East' },
];

const AzureConfig = () => {
  const navigate = useNavigate();

  const [subscriptionId, setSubscriptionId] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [accountName, setAccountName] = useState('');
  const [region, setRegion] = useState('eastus');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const [statusMsg, setStatusMsg] = useState('');
  const [testResult, setTestResult] = useState<'idle' | 'success' | 'error'>('idle');
  const [testMsg, setTestMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [hasExistingConfig, setHasExistingConfig] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/integrations/azure/config');
        const cfg = res.data;
        if (cfg.configured) {
          setHasExistingConfig(true);
          setSubscriptionId(cfg.subscription_id);
          setTenantId(cfg.tenant_id);
          setClientId(cfg.client_id);
          setAccountName(cfg.account_name);
          setRegion(cfg.region || 'eastus');
        }
      } catch {
        // not configured yet
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleSave = async () => {
    if (!subscriptionId.trim() || !tenantId.trim() || !clientId.trim()) return;
    setSaving(true);
    setStatus('idle');
    try {
      await api.post('/api/integrations/azure/setup', {
        subscription_id: subscriptionId.trim(),
        tenant_id: tenantId.trim(),
        client_id: clientId.trim(),
        client_secret: clientSecret.trim(),
        account_name: accountName.trim(),
        region,
      });
      setStatus('saved');
      setStatusMsg('Azure configuration saved.');
      setTestResult('idle');
      setTestMsg('');
      setHasExistingConfig(true);
    } catch (err: any) {
      setStatus('error');
      setStatusMsg(err.response?.data?.detail || 'Failed to save configuration.');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult('idle');
    setTestMsg('');
    try {
      const res = await api.post('/api/integrations/azure/test');
      if (res.data.success) {
        setTestResult('success');
        setTestMsg(`Connection successful — Subscription: ${res.data.subscription_id}`);
      } else {
        setTestResult('error');
        setTestMsg(res.data.error || 'Connection failed');
      }
    } catch (err: any) {
      setTestResult('error');
      setTestMsg(err.response?.data?.detail || 'Connection failed');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <Loader2 size={24} className="animate-spin" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/integrations/cloud-providers')} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Cloud Providers</p>
          <h1 style={{ margin: 0 }}>Azure Configuration</h1>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem', maxWidth: 600 }}>
        {hasExistingConfig && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--info)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} /> Existing configuration loaded. Update fields below and save to change.
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Subscription ID <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              className="form-control"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={subscriptionId}
              onChange={(e) => setSubscriptionId(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Tenant ID <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              className="form-control"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Client ID (App Registration) <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              className="form-control"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Client Secret <span style={{ color: 'var(--danger)' }}>*</span>
              {!hasExistingConfig && <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> (required for new config)</span>}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                className="form-control"
                type={showSecret ? 'text' : 'password'}
                placeholder={hasExistingConfig ? 'Leave blank to keep existing' : 'Azure client secret'}
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                style={{ paddingRight: '2.5rem' }}
                autoComplete="off"
              />
              <button
                type="button"
                onClick={() => setShowSecret(!showSecret)}
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
                  justifyContent: 'center',
                }}
                tabIndex={-1}
              >
                {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>Account Name (optional)</label>
            <input className="form-control" placeholder="Production Subscription" value={accountName} onChange={(e) => setAccountName(e.target.value)} />
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Friendly name to identify this Azure subscription.</p>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>Region</label>
            <select className="form-control" value={region} onChange={(e) => setRegion(e.target.value)}>
              {AZURE_REGIONS.map(r => <option key={r.value} value={r.value}>{r.label} ({r.value})</option>)}
            </select>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Azure region for resource discovery.</p>
          </div>
        </div>

        {status === 'saved' && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', color: 'var(--success)', borderRadius: 'var(--radius)', marginTop: '1rem', border: '1px solid rgba(34, 197, 94, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} /> {statusMsg}
          </div>
        )}

        {status === 'error' && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginTop: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <XCircle size={16} /> {statusMsg}
          </div>
        )}

        {testResult === 'success' && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', color: 'var(--success)', borderRadius: 'var(--radius)', marginTop: '1rem', border: '1px solid rgba(34, 197, 94, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} /> {testMsg}
          </div>
        )}

        {testResult === 'error' && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginTop: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <XCircle size={16} /> {testMsg}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
          <button className="btn btn-outline" onClick={handleTest} disabled={testing || !subscriptionId.trim() || !tenantId.trim() || !clientId.trim()}>
            {testing ? <Loader2 size={16} className="animate-spin" /> : null} Test Connection
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || !subscriptionId.trim() || !tenantId.trim() || !clientId.trim()}>
            {saving ? <Loader2 size={16} className="animate-spin" /> : null} Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default AzureConfig;
