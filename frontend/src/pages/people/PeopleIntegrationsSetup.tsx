import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const PeopleIntegrationsSetup = () => {
  const navigate = useNavigate();
  const [oktaDomain, setOktaDomain] = useState('');
  const [oktaToken, setOktaToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const res = await api.post('/api/integrations/okta/setup', {
        okta_domain: oktaDomain,
        okta_token: oktaToken,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People Assets</p>
          <h1>Okta Setup</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/people/integrations')}>
            <i className="ti ti-arrow-left"></i> Back
          </button>
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
        Enter your Okta domain and API token. Generate an API token in the Okta admin console under Security → API → Tokens.
      </p>

      <div className="card" style={{ padding: '1.5rem', maxWidth: 600 }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.375rem', color: 'var(--text-secondary)' }}>Okta Domain</label>
            <input
              type="text"
              className="form-input"
              value={oktaDomain}
              onChange={e => setOktaDomain(e.target.value)}
              placeholder="your-domain.okta.com"
              required
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.375rem', color: 'var(--text-secondary)' }}>API Token</label>
            <input
              type="password"
              className="form-input"
              value={oktaToken}
              onChange={e => setOktaToken(e.target.value)}
              placeholder="00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              required
              style={{ width: '100%' }}
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            <i className="ti ti-key"></i> {loading ? 'Saving...' : 'Save Configuration'}
          </button>
        </form>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: 8, background: '#dc262615', border: '1px solid #dc262630', color: '#dc2626', fontSize: '0.8125rem', marginTop: '1rem', maxWidth: 600 }}>
          <i className="ti ti-alert-triangle" style={{ marginRight: 6 }}></i> {error}
        </div>
      )}

      {result?.success && (
        <div style={{ marginTop: '1rem', maxWidth: 600 }}>
          <div className="card" style={{ padding: '1.25rem', border: '1px solid #05966930' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 0.5rem', color: '#059669' }}>
              <i className="ti ti-circle-check"></i> Setup Complete
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {result.message}
            </p>
            <button className="btn btn-primary" style={{ marginTop: '0.75rem' }} onClick={() => navigate('/assets/people/integrations')}>
              <i className="ti ti-refresh"></i> Go to Sync
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PeopleIntegrationsSetup;
