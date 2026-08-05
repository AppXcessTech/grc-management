import React, { useState, useRef } from 'react';
import { X, Upload, Download, Loader2, CheckCircle, XCircle, Copy, Check } from 'lucide-react';
import api from '../services/api';

interface ImportResult {
  success_count: number;
  error_count: number;
  created: Array<{
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    generated_password: string;
  }>;
  errors: Array<{ row: number; email: string; errors: string[] }>;
}

interface BulkImportModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const BulkImportModal: React.FC<BulkImportModalProps> = ({ onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ImportResult | null>(null);
  const [copiedPasswords, setCopiedPasswords] = useState<Set<number>>(new Set());
  const [copiedAll, setCopiedAll] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      const ext = f.name.split('.').pop()?.toLowerCase();
      if (!['csv', 'xlsx', 'xls'].includes(ext || '')) {
        setError('Please upload a CSV or Excel (.xlsx) file');
        return;
      }
      setFile(f);
      setError('');
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) {
      const ext = f.name.split('.').pop()?.toLowerCase();
      if (!['csv', 'xlsx', 'xls'].includes(ext || '')) {
        setError('Please upload a CSV or Excel (.xlsx) file');
        return;
      }
      setFile(f);
      setError('');
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/api/users/bulk-import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
      if (res.data.success_count > 0) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPassword = (id: number, password: string) => {
    navigator.clipboard.writeText(`${password}`);
    setCopiedPasswords(prev => new Set(prev).add(id));
    setTimeout(() => setCopiedPasswords(prev => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    }), 2000);
  };

  const handleCopyAll = () => {
    if (!result) return;
    const text = result.created.map(u => `${u.email}\t${u.generated_password}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const downloadTemplate = () => {
    const csv = 'Name,Email,Role,Department\nJohn Doe,john@example.com,employee,Engineering\nJane Smith,jane@example.com,compliance_admin,Security';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'user_import_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
      backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto', padding: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2rem', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ margin: 0 }}>Bulk Import Users</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X /></button>
        </div>

        <div style={{ padding: '2rem' }}>
          {!result ? (
            <>
              <div style={{ marginBottom: '1.5rem' }}>
                <button className="btn btn-secondary" onClick={downloadTemplate} style={{ fontSize: '0.8125rem' }}>
                  <Download size={16} />
                  Download CSV Template
                </button>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
                  Upload a CSV or Excel file with columns: <strong>Name</strong>, <strong>Email</strong>, <strong>Role</strong>, <strong>Department</strong> (optional).
                  Roles are mapped from your organization's configured roles.
                </p>
              </div>

              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${file ? 'var(--primary)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius)',
                  padding: '3rem 2rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: file ? 'rgba(14,165,233,0.03)' : 'rgba(255,255,255,0.02)',
                  transition: 'all 0.2s',
                  marginBottom: '1.5rem',
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                {file ? (
                  <div>
                    <CheckCircle size={32} color="var(--primary)" style={{ marginBottom: '0.75rem' }} />
                    <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{file.name}</p>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                    <button
                      className="btn btn-ghost"
                      style={{ marginTop: '0.75rem', fontSize: '0.8125rem', color: 'var(--danger)' }}
                      onClick={(e) => { e.stopPropagation(); setFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div>
                    <Upload size={32} color="var(--text-muted)" style={{ marginBottom: '0.75rem' }} />
                    <p style={{ color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Drag & drop a file here, or <span style={{ color: 'var(--primary)', fontWeight: 600 }}>browse</span>
                    </p>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>CSV or Excel (.xlsx)</p>
                  </div>
                )}
              </div>

              {error && (
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.875rem', border: '1px solid rgba(239,68,68,0.2)' }}>
                  {error}
                </div>
              )}

              <button
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={!file || loading}
                onClick={handleUpload}
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
                {loading ? 'Importing...' : `Import ${file ? file.name : 'Users'}`}
              </button>
            </>
          ) : (
            <>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                {result.error_count === 0 ? (
                  <CheckCircle size={40} color="#22c55e" style={{ marginBottom: '0.75rem' }} />
                ) : result.success_count > 0 ? (
                  <div>
                    <CheckCircle size={40} color="#22c55e" style={{ marginBottom: '0.5rem' }} />
                    <XCircle size={24} color="#ef4444" style={{ marginLeft: '-0.5rem' }} />
                  </div>
                ) : (
                  <XCircle size={40} color="#ef4444" style={{ marginBottom: '0.75rem' }} />
                )}
                <h3 style={{ margin: '0 0 0.25rem' }}>
                  {result.success_count > 0
                    ? `Successfully imported ${result.success_count} user${result.success_count !== 1 ? 's' : ''}`
                    : 'Import completed'}
                </h3>
                {result.error_count > 0 && (
                  <p style={{ color: '#ef4444', fontSize: '0.875rem', margin: 0 }}>
                    {result.error_count} error{result.error_count !== 1 ? 's' : ''}
                  </p>
                )}
              </div>

              {result.created.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <p style={{ fontSize: '0.875rem', fontWeight: 600, margin: 0 }}>Generated Credentials</p>
                    <button className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }} onClick={handleCopyAll}>
                      {copiedAll ? <Check size={14} /> : <Copy size={14} />}
                      {copiedAll ? ' Copied' : ' Copy All'}
                    </button>
                  </div>
                  <div style={{ maxHeight: '240px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
                    <table style={{ width: '100%', fontSize: '0.8125rem' }}>
                      <thead>
                        <tr style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}>
                          <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Email</th>
                          <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Password</th>
                          <th style={{ padding: '0.5rem 0.75rem', width: '40px' }}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.created.map(u => (
                          <tr key={u.id} style={{ borderTop: '1px solid var(--border)' }}>
                            <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace' }}>{u.email}</td>
                            <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace' }}>{u.generated_password}</td>
                            <td style={{ padding: '0.5rem 0.75rem' }}>
                              <button
                                className="btn btn-ghost"
                                style={{ padding: '0.25rem' }}
                                onClick={() => handleCopyPassword(u.id, u.generated_password)}
                                title="Copy password"
                              >
                                {copiedPasswords.has(u.id) ? <Check size={14} color="#22c55e" /> : <Copy size={14} />}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {result.errors.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <p style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: '#ef4444' }}>Errors</p>
                  <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius)' }}>
                    {result.errors.map((err, idx) => (
                      <div key={idx} style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid rgba(239,68,68,0.1)', fontSize: '0.8125rem' }}>
                        <span style={{ fontWeight: 600 }}>Row {err.row}</span> — {err.email}: {err.errors.join(', ')}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button className="btn btn-primary" style={{ width: '100%' }} onClick={onClose}>
                Done
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkImportModal;