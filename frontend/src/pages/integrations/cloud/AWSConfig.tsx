import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';
import api from '../../../services/api';

const AWS_REGIONS = [
  { value: 'us-east-1', label: 'US East (N. Virginia)' },
  { value: 'us-east-2', label: 'US East (Ohio)' },
  { value: 'us-west-1', label: 'US West (N. California)' },
  { value: 'us-west-2', label: 'US West (Oregon)' },
  { value: 'eu-central-1', label: 'Europe (Frankfurt)' },
  { value: 'eu-west-1', label: 'Europe (Ireland)' },
  { value: 'eu-west-2', label: 'Europe (London)' },
  { value: 'eu-west-3', label: 'Europe (Paris)' },
  { value: 'eu-north-1', label: 'Europe (Stockholm)' },
  { value: 'ap-south-1', label: 'Asia Pacific (Mumbai)' },
  { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
  { value: 'ap-southeast-2', label: 'Asia Pacific (Sydney)' },
  { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
  { value: 'ap-northeast-2', label: 'Asia Pacific (Seoul)' },
  { value: 'sa-east-1', label: 'South America (Sao Paulo)' },
  { value: 'ca-central-1', label: 'Canada (Central)' },
];

const AWSConfig = () => {
  const navigate = useNavigate();

  const [roleArn, setRoleArn] = useState('');
  const [accountName, setAccountName] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const [statusMsg, setStatusMsg] = useState('');
  const [testResult, setTestResult] = useState<'idle' | 'success' | 'error'>('idle');
  const [testMsg, setTestMsg] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/integrations/aws/config');
        const cfg = res.data;
        if (cfg.configured) {
          setRoleArn(cfg.role_arn);
          setAccountName(cfg.account_name);
          setRegion(cfg.region);
        }
      } catch {
        // not configured yet
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleSave = async () => {
    if (!roleArn.trim()) return;
    setSaving(true);
    setStatus('idle');
    try {
      await api.post('/api/integrations/aws/setup', {
        role_arn: roleArn.trim(),
        account_name: accountName.trim(),
        region,
      });
      setStatus('saved');
      setStatusMsg('AWS configuration saved.');
      setTestResult('idle');
      setTestMsg('');
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
      const res = await api.post('/api/integrations/aws/test');
      if (res.data.success) {
        setTestResult('success');
        setTestMsg(`Connection successful — Account ID: ${res.data.account_id}`);
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
          <h1 style={{ margin: 0 }}>AWS Configuration</h1>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem', maxWidth: 600 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>AWS Role ARN</label>
            <input className="form-control" placeholder="arn:aws:iam::123456789012:role/AppXcessImport" value={roleArn} onChange={(e) => setRoleArn(e.target.value)} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>Account Name (optional)</label>
            <input className="form-control" placeholder="Production Account" value={accountName} onChange={(e) => setAccountName(e.target.value)} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>Region</label>
            <select className="form-control" value={region} onChange={(e) => setRegion(e.target.value)}>
              {AWS_REGIONS.map(r => <option key={r.value} value={r.value}>{r.label} ({r.value})</option>)}
            </select>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Used for STS connection. Resource discovery scans all regions.</p>
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
          <button className="btn btn-outline" onClick={handleTest} disabled={testing || !roleArn.trim()}>
            {testing ? <Loader2 size={16} className="animate-spin" /> : null} Test Connection
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || !roleArn.trim()}>
            {saving ? <Loader2 size={16} className="animate-spin" /> : null} Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default AWSConfig;
