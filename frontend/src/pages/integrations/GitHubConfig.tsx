import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle, ArrowLeft, Info, AlertTriangle, Shield } from 'lucide-react';
import api from '../../services/api';

const GitHubConfig = () => {
  const navigate = useNavigate();

  const [token, setToken] = useState('');
  const [classicToken, setClassicToken] = useState('');
  const [accountName, setAccountName] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const [statusMsg, setStatusMsg] = useState('');
  const [testResult, setTestResult] = useState<'idle' | 'success' | 'error'>('idle');
  const [testMsg, setTestMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [hasExisting, setHasExisting] = useState(false);
  const [hasClassicToken, setHasClassicToken] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/integrations/github/config');
        const cfg = res.data;
        if (cfg.configured) {
          setHasExisting(true);
          setHasClassicToken(cfg.has_classic_token);
          setAccountName(cfg.account_name || '');
          // Never pre-fill password fields
        }
      } catch {
        // not configured yet
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleSave = async () => {
    if (!token.trim() && !hasExisting) return;
    setSaving(true);
    setStatus('idle');
    try {
      const payload: Record<string, any> = {
        github_token: token.trim(),
        account_name: accountName.trim(),
      };
      // Only send classic_token if user entered something
      if (classicToken.trim()) {
        payload.classic_token = classicToken.trim();
      } else if (!hasClassicToken) {
        // No existing classic token and user didn't enter one — send empty to stay unconfigured
        payload.classic_token = '';
      }
      // If hasClassicToken and user left blank: omit classic_token so backend preserves it

      await api.post('/api/integrations/github/setup', payload);
      setStatus('saved');
      setStatusMsg('GitHub configuration saved.');
      setTestResult('idle');
      setTestMsg('');
      setHasExisting(true);
      setHasClassicToken(!!classicToken.trim() || hasClassicToken);
      // Clear password fields after save (write-once security)
      setToken('');
      setClassicToken('');
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
      const res = await api.post('/api/integrations/github/test');
      if (res.data.success) {
        setTestResult('success');
        setTestMsg(res.data.message || 'Connection successful!');
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

  const isFineGrainedProvided = () => token.trim().length > 0;
  const isFormValid = () => isFineGrainedProvided() || hasExisting;

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <Loader2 size={24} className="animate-spin" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/integrations/version-control')} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Version Control Systems</p>
          <h1 style={{ margin: 0 }}>GitHub Configuration</h1>
        </div>
      </div>

      {/* Token explanation banner */}
      <div
        style={{
          padding: '0.875rem 1rem',
          background: 'rgba(14, 165, 233, 0.06)',
          border: '1px solid rgba(14, 165, 233, 0.15)',
          borderRadius: 'var(--radius)',
          marginBottom: '1.25rem',
          maxWidth: 600,
          display: 'flex',
          gap: '0.75rem',
          alignItems: 'flex-start',
        }}
      >
        <Info size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: '1px' }} />
        <div style={{ fontSize: '0.8125rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--primary)' }}>Token setup</strong>
          <ul style={{ margin: '0.375rem 0 0', paddingLeft: '1.25rem' }}>
            <li>
              <strong>Fine-grained token</strong> (required, read-only) — works with most tables:
              repositories, teams, members, branch protection, secrets, workflows, and more.
            </li>
            <li>
              <strong>Classic token</strong> (optional) — needed for <em>audit log</em> and{' '}
              <em>user identity</em> sync, which require classic PAT scope.
            </li>
          </ul>
          {!hasClassicToken && hasExisting && (
            <p style={{ margin: '0.5rem 0 0', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <AlertTriangle size={14} />
              Add a classic token to enable audit log and user-identity sync.
            </p>
          )}
        </div>
      </div>

      {/* Main card */}
      <div className="card" style={{ padding: '1.25rem', maxWidth: 600 }}>
        {hasExisting && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--info)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} /> Existing configuration loaded. Update fields below and save to change.
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Fine-grained token field */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Fine-grained Personal Access Token <span style={{ color: 'var(--danger)' }}>*</span>
              {hasExisting && (
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 400 }}> (leave blank to keep existing)</span>
              )}
            </label>
            <input
              className="form-control"
              type="password"
              placeholder={
                hasExisting
                  ? 'Leave blank to keep existing secret'
                  : 'github_pat_xxxxxxxxxxxxxxxxxxx'
              }
              value={token}
              onChange={(e) => setToken(e.target.value)}
              autoComplete="new-password"
            />
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Shield size={12} />
              Read-only access to repositories, teams, members, and settings.
            </p>
          </div>

          {/* Classic token field */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Classic Personal Access Token <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.75rem' }}>(optional)</span>
              {hasClassicToken && (
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 400 }}> (leave blank to keep existing)</span>
              )}
            </label>
            <input
              className="form-control"
              type="password"
              placeholder={
                hasClassicToken
                  ? 'Leave blank to keep existing secret'
                  : 'ghp_xxxxxxxxxxxxxxxxxxx'
              }
              value={classicToken}
              onChange={(e) => setClassicToken(e.target.value)}
              autoComplete="new-password"
            />
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <AlertTriangle size={12} />
              Required for audit log and user identity tables. <a href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-classic-token" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)' }}>Learn more</a>
            </p>
          </div>

          {/* Account name (optional) */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Account Name <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.75rem' }}>(optional)</span>
            </label>
            <input
              className="form-control"
              placeholder="My Organization"
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
            />
          </div>
        </div>

        {/* Status messages */}
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

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
          <button className="btn btn-outline" onClick={handleTest} disabled={testing || !isFormValid()}>
            {testing ? <Loader2 size={16} className="animate-spin" /> : null} Test Connection
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || !isFormValid()}>
            {saving ? <Loader2 size={16} className="animate-spin" /> : null} Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default GitHubConfig;
