import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const EndpointIntegrationsSetup = () => {
  const navigate = useNavigate();
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const res = await api.post('/api/integrations/manageengine-mdm/setup', {
        client_id: clientId,
        client_secret: clientSecret,
        code,
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
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Endpoint Devices</p>
          <h1>MDM Setup</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/devices/integrations')}>
            <i className="ti ti-arrow-left"></i> Back
          </button>
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
        Enter your ManageEngine MDM OAuth credentials to connect. Get a fresh authorization code from the Zoho consent screen, then paste it here along with your Client ID and Secret.
      </p>

      <div className="card" style={{ padding: '1.5rem', maxWidth: 600 }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.375rem', color: 'var(--text-secondary)' }}>Client ID</label>
            <input
              type="text"
              className="form-input"
              value={clientId}
              onChange={e => setClientId(e.target.value)}
              placeholder="1000.xxxxxxxxxxxx"
              required
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.375rem', color: 'var(--text-secondary)' }}>Client Secret</label>
            <input
              type="password"
              className="form-input"
              value={clientSecret}
              onChange={e => setClientSecret(e.target.value)}
              placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              required
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.375rem', color: 'var(--text-secondary)' }}>Authorization Code</label>
            <input
              type="text"
              className="form-input"
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder="1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              required
              style={{ width: '100%' }}
            />
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Get this from the Zoho OAuth consent page URL after authorizing the app.
            </p>
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            <i className="ti ti-key"></i> {loading ? 'Exchanging...' : 'Exchange Code'}
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
            <button className="btn btn-primary" style={{ marginTop: '0.75rem' }} onClick={() => navigate('/assets/devices/integrations')}>
              <i className="ti ti-refresh"></i> Go to Sync
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EndpointIntegrationsSetup;
