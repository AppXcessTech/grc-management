import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle, ArrowLeft, Lock } from 'lucide-react';
import api from '../services/api';

export interface FieldDef {
  name: string;
  label: string;
  type: 'text' | 'password' | 'select';
  required?: boolean;
  placeholder?: string;
  defaultValue?: string;
  options?: { value: string; label: string }[];
  hint?: string;
}

interface Props {
  title: string;
  categoryLabel: string;
  backPath: string;
  apiPath: string;            // e.g. /api/integrations/generic/gcp
  fields: FieldDef[];
  loadFields?: (cfg: Record<string, any>) => Record<string, string>;
}

const IntegrationConfigForm = ({
  title,
  categoryLabel,
  backPath,
  apiPath,
  fields,
  loadFields,
}: Props) => {
  const navigate = useNavigate();

  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const [statusMsg, setStatusMsg] = useState('');
  const [testResult, setTestResult] = useState<'idle' | 'success' | 'error'>('idle');
  const [testMsg, setTestMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [hasExistingConfig, setHasExistingConfig] = useState(false);

  // Collect password field names for the backend masking API
  const passwordFieldNames = useMemo(
    () => fields.filter(f => f.type === 'password').map(f => f.name),
    [fields],
  );

  // Initialize default values
  useEffect(() => {
    const defaults: Record<string, string> = {};
    fields.forEach((f) => {
      defaults[f.name] = f.defaultValue || '';
    });
    setFormValues(defaults);

    (async () => {
      try {
        // Pass secret_fields so the backend masks password values with the sentinel
        const params: Record<string, string> = {};
        if (passwordFieldNames.length > 0) {
          params.secret_fields = passwordFieldNames.join(',');
        }
        const res = await api.get(apiPath + '/config', { params });
        const data = res.data;
        if (data.configured && data.config) {
          setHasExistingConfig(true);
          const loaded = loadFields ? loadFields(data.config) : data.config;

          // Write-only security:
          // Password fields are NEVER pre-filled from the server.
          // The backend returns a sentinel ("••••••••") instead of the real value.
          // We drop those sentinel values so the field stays empty, showing only
          // the helper text "Leave blank to keep the existing secret."
          const sanitized: Record<string, string> = {};
          for (const [key, value] of Object.entries(loaded)) {
            if (passwordFieldNames.includes(key)) {
              // Don't pre-fill password fields — stay empty
              sanitized[key] = '';
            } else {
              sanitized[key] = value as string;
            }
          }
          setFormValues((prev) => ({ ...prev, ...sanitized }));
        }
      } catch {
        // not configured yet
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const setValue = (name: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus('idle');
    try {
      await api.post(apiPath + '/setup', { config: formValues });
      setStatus('saved');
      setStatusMsg(`${title} configuration saved.`);
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
      const res = await api.post(apiPath + '/test');
      if (res.data.success) {
        setTestResult('success');
        setTestMsg(res.data.message || 'Connection successful!');
      } else {
        setTestResult('error');
        setTestMsg(res.data.message || res.data.error || 'Connection failed');
      }
    } catch (err: any) {
      setTestResult('error');
      setTestMsg(err.response?.data?.detail || 'Connection failed');
    } finally {
      setTesting(false);
    }
  };

  const isFormValid = () => {
    return fields
      .filter((f) => f.required)
      .every((f) => {
        const val = formValues[f.name]?.trim();
        // Password fields are allowed to be empty when there's existing config
        if (f.type === 'password' && hasExistingConfig && !val) return true;
        return !!val;
      });
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
        <button className="btn btn-ghost" onClick={() => navigate(backPath)} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>{categoryLabel}</p>
          <h1 style={{ margin: 0 }}>{title} Configuration</h1>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem', maxWidth: 600 }}>
        {hasExistingConfig && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--info)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} /> Existing configuration loaded. Update fields below and save to change.
          </div>
        )}

        {/* Write-only secret notice */}
        {hasExistingConfig && passwordFieldNames.length > 0 && (
          <div style={{ padding: '0.625rem 0.75rem', backgroundColor: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.15)', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.75rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Lock size={14} />
            Secrets are write-only — values are never displayed after saving.
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {fields.map((field) => (
            <div key={field.name}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-main)' }}>
                {field.label}
                {field.required && !(field.type === 'password' && hasExistingConfig) && (
                  <span style={{ color: 'var(--danger)' }}> *</span>
                )}
                {field.required && field.type === 'password' && hasExistingConfig && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 400 }}> (leave blank to keep existing)</span>
                )}
              </label>

              {field.type === 'select' ? (
                <select
                  className="form-control"
                  value={formValues[field.name] || ''}
                  onChange={(e) => setValue(field.name, e.target.value)}
                >
                  {field.options?.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              ) : field.type === 'password' ? (
                <div>
                  <input
                    className="form-control"
                    type="password"
                    placeholder={hasExistingConfig ? 'Leave blank to keep existing secret' : (field.placeholder || '')}
                    value={formValues[field.name] || ''}
                    onChange={(e) => setValue(field.name, e.target.value)}
                    autoComplete="new-password"
                    style={{ paddingRight: '0.75rem' }}
                  />
                  {hasExistingConfig && !formValues[field.name] && (
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem', fontStyle: 'italic' }}>
                      Leave blank to keep the existing secret.
                    </p>
                  )}
                </div>
              ) : (
                <input
                  className="form-control"
                  placeholder={field.placeholder || ''}
                  value={formValues[field.name] || ''}
                  onChange={(e) => setValue(field.name, e.target.value)}
                />
              )}

              {field.hint && (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{field.hint}</p>
              )}
            </div>
          ))}
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

export default IntegrationConfigForm;
