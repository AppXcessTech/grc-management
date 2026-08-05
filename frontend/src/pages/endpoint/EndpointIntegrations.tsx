import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const EndpointIntegrations = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ total?: number; created?: number; updated?: number; errors?: string[] } | null>(null);
  const [error, setError] = useState('');
  const handleSetup = () => {
    navigate('/assets/devices/integrations/setup');
  };

  const handleSync = async () => {
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const res = await api.post('/api/integrations/manageengine-mdm/sync');
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Sync failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Endpoint Devices</p>
          <h1>Integrations</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/devices')}>
            <i className="ti ti-arrow-left"></i> Back
          </button>
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
        Connect ManageEngine MDM Plus to sync endpoint device inventory via OAuth.
      </p>

      <div className="card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div style={{ width: 48, height: 48, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f59e0b15', color: '#f59e0b', fontSize: 24 }}>
          <i className="ti ti-device-mobile"></i>
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: 0 }}>ManageEngine MDM Plus</h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
            Click <strong>Configure</strong> to enter OAuth credentials, then <strong>Sync Now</strong> to fetch devices.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-outline" onClick={handleSetup}>
            <i className="ti ti-key"></i> Configure
          </button>
          <button className="btn btn-primary" onClick={handleSync} disabled={loading}>
            <i className="ti ti-refresh"></i> {loading ? 'Working...' : 'Sync Now'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: 8, background: '#dc262615', border: '1px solid #dc262630', color: '#dc2626', fontSize: '0.8125rem', marginTop: '1rem' }}>
          <i className="ti ti-alert-triangle" style={{ marginRight: 6 }}></i> {error}
        </div>
      )}



      {result && result.total !== undefined && (
        <div style={{ marginTop: '1rem' }}>
          <div className="card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 0.75rem' }}>Sync Results</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '0.75rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: 8, background: 'var(--background)', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>{result.total}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total from MDM</div>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: 8, background: '#05966915', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#059669' }}>{result.created}</div>
                <div style={{ fontSize: '0.75rem', color: '#059669' }}>Created</div>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: 8, background: '#2563eb15', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#2563eb' }}>{result.updated}</div>
                <div style={{ fontSize: '0.75rem', color: '#2563eb' }}>Updated</div>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: 8, background: '#dc262615', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#dc2626' }}>{(result.errors || []).length}</div>
                <div style={{ fontSize: '0.75rem', color: '#dc2626' }}>Errors</div>
              </div>
            </div>
            {result.errors && result.errors.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                {result.errors.map((e, i) => (
                  <div key={i} style={{ padding: '0.375rem 0.625rem', borderRadius: 4, background: '#dc262615', fontSize: '0.75rem', color: '#dc2626' }}>
                    {e}
                  </div>
                ))}
              </div>
            )}
            {result.created && result.created > 0 && (
              <p style={{ color: '#059669', fontSize: '0.8125rem', marginTop: '0.5rem' }}>
                <i className="ti ti-circle-check"></i> Successfully created {result.created} devices from ManageEngine MDM.
              </p>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default EndpointIntegrations;
