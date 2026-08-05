import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle, ArrowLeft, Upload, FileJson } from 'lucide-react';
import api from '../../../services/api';

const GCP_REGIONS = [
  { value: 'us-central1', label: 'us-central1 (Iowa)' },
  { value: 'us-east1', label: 'us-east1 (South Carolina)' },
  { value: 'us-east4', label: 'us-east4 (Northern Virginia)' },
  { value: 'us-west1', label: 'us-west1 (Oregon)' },
  { value: 'us-west2', label: 'us-west2 (Los Angeles)' },
  { value: 'us-west3', label: 'us-west3 (Salt Lake City)' },
  { value: 'us-west4', label: 'us-west4 (Las Vegas)' },
  { value: 'europe-west1', label: 'europe-west1 (Belgium)' },
  { value: 'europe-west2', label: 'europe-west2 (London)' },
  { value: 'europe-west4', label: 'europe-west4 (Netherlands)' },
  { value: 'asia-east1', label: 'asia-east1 (Taiwan)' },
  { value: 'asia-southeast1', label: 'asia-southeast1 (Singapore)' },
  { value: 'australia-southeast1', label: 'australia-southeast1 (Sydney)' },
];

const GCPConfig = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const [projectId, setProjectId] = useState('');
  const [region, setRegion] = useState('us-central1');
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
        const res = await api.get('/api/integrations/gcp/config');
        const cfg = res.data;
        if (cfg.configured) {
          setHasExistingConfig(true);
          setProjectId(cfg.project_id || '');
          setRegion(cfg.region || 'us-central1');
        }
      } catch {
        // not configured yet
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      validateAndParseFile(f);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) {
      validateAndParseFile(f);
    }
  };

  const validateAndParseFile = (f: File) => {
    setFileError('');

    if (!f.name.endsWith('.json')) {
      setFileError('Please upload a valid GCP service account JSON key file (.json).');
      return;
    }

    if (f.size > 1024 * 1024) {
      setFileError('File is too large. GCP service account JSON files are typically under 100KB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const text = ev.target?.result as string;
        const creds = JSON.parse(text);

        if (!creds.project_id || !creds.private_key || !creds.client_email) {
          setFileError(
            'Invalid GCP service account key file. The JSON must contain "project_id", "client_email", and "private_key" fields.'
          );
          return;
        }

        if (creds.type !== 'service_account') {
          setFileError(
            'This does not appear to be a GCP service account key. The "type" field should be "service_account".'
          );
          return;
        }

        setFile(f);
        setFileError('');
      } catch {
        setFileError('Invalid JSON file. Please upload a valid GCP service account key file.');
      }
    };
    reader.readAsText(f);
  };

  const handleSave = async () => {
    if (!projectId.trim()) return;
    if (!file && !hasExistingConfig) {
      setFileError('Please upload a GCP service account JSON file.');
      return;
    }

    setSaving(true);
    setStatus('idle');
    try {
      const formData = new FormData();

      if (file) {
        formData.append('file', file);
      }

      formData.append('project_id', projectId.trim());
      formData.append('region', region);

      await api.post('/api/integrations/gcp/setup', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setStatus('saved');
      setStatusMsg('GCP configuration saved.');
      setTestResult('idle');
      setTestMsg('');
      setHasExistingConfig(true);
      setFile(null);
      setFileError('');
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
      const res = await api.post('/api/integrations/gcp/test');
      if (res.data.success) {
        setTestResult('success');
        setTestMsg(`Connection successful — Project: ${res.data.project_id}`);
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

  const removeFile = () => {
    setFile(null);
    setFileError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <Loader2 size={24} className="animate-spin" />
      </div>
    );
  }

  const isFormValid = () => {
    if (!projectId.trim()) return false;
    if (!file && !hasExistingConfig) return false;
    return true;
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/integrations/cloud-providers')} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Cloud Providers</p>
          <h1 style={{ margin: 0 }}>GCP Configuration</h1>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem', maxWidth: 640 }}>
        {hasExistingConfig && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--info)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} /> Existing configuration loaded. Upload a new key file or update fields below and save to change.
          </div>
        )}

        {/* Instructions banner */}
        <div style={{
          padding: '0.875rem 1rem',
          background: 'rgba(14, 165, 233, 0.06)',
          border: '1px solid rgba(14, 165, 233, 0.15)',
          borderRadius: 'var(--radius)',
          marginBottom: '1.25rem',
          display: 'flex',
          gap: '0.75rem',
          alignItems: 'flex-start',
        }}>
          <FileJson size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: '1px' }} />
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
            <strong style={{ color: 'var(--primary)' }}>Upload your GCP service account key</strong>
            <ol style={{ margin: '0.375rem 0 0', paddingLeft: '1.25rem' }}>
              <li>Go to <strong>GCP Console → IAM & Admin → Service Accounts</strong></li>
              <li>Select or create a service account with the required permissions</li>
              <li>Click <strong>Keys → Add Key → Create New Key → JSON</strong></li>
              <li>Download the JSON file and upload it below</li>
            </ol>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* File Upload */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Service Account Key File (JSON) <span style={{ color: 'var(--danger)' }}>*</span>
              {hasExistingConfig && (
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 400 }}> (upload to replace existing)</span>
              )}
            </label>

            {!file ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${hasExistingConfig ? 'var(--primary)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius)',
                  padding: '2rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: 'rgba(255,255,255,0.02)',
                  transition: 'all 0.2s',
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                <Upload size={28} color="var(--text-muted)" style={{ marginBottom: '0.5rem' }} />
                <p style={{ color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                  Drag & drop your service account JSON file here, or <span style={{ color: 'var(--primary)', fontWeight: 600 }}>browse</span>
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>.json file from GCP IAM & Admin</p>
              </div>
            ) : (
              <div style={{
                border: '2px solid rgba(34, 197, 94, 0.3)',
                borderRadius: 'var(--radius)',
                padding: '1rem',
                backgroundColor: 'rgba(34, 197, 94, 0.03)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: 'var(--radius)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <FileJson size={20} color="var(--success)" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontWeight: 600, marginBottom: '0.125rem', fontSize: '0.875rem' }}>{file.name}</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {(file.size / 1024).toFixed(1)} KB &middot; Key file validated
                    </p>
                  </div>
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: 'var(--danger)', flexShrink: 0 }}
                    onClick={(e) => { e.stopPropagation(); removeFile(); }}
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}

            {fileError && (
              <div style={{
                padding: '0.5rem 0.75rem',
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                color: 'var(--danger)',
                borderRadius: 'var(--radius)',
                marginTop: '0.5rem',
                border: '1px solid rgba(239, 68, 68, 0.15)',
                fontSize: '0.8125rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}>
                <XCircle size={14} /> {fileError}
              </div>
            )}
          </div>

          {/* Project ID */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
              Project ID <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              className="form-control"
              placeholder="my-gcp-project-123"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            />
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              GCP Project ID to discover resources from.
            </p>
          </div>

          {/* Region */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>Default Region</label>
            <select className="form-control" value={region} onChange={(e) => setRegion(e.target.value)}>
              {GCP_REGIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Default GCP region for resource discovery. Resources in all regions are discovered.
            </p>
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
          <button className="btn btn-outline" onClick={handleTest} disabled={testing || !hasExistingConfig || !projectId.trim()}>
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

export default GCPConfig;
