import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, Plus, Trash2 } from 'lucide-react';
import api from '../../services/api';

interface AssetCategory {
  id: number;
  name: string;
}

interface Department {
  id: number;
  name: string;
}

interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  marginBottom: '0.375rem',
  fontSize: '0.875rem',
  fontWeight: 500,
  color: 'var(--text-muted)',
};

const SuggestAsset = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [department, setDepartment] = useState('');
  const [ownerId, setOwnerId] = useState<number | ''>('');
  const [criticality, setCriticality] = useState('Medium');
  const [riskLevel, setRiskLevel] = useState('Medium');
  const [tags, setTags] = useState<Array<{ key: string; value: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const nonAdminUsers = users.filter(u => u.email !== 'admin@hybrid.com');

  useEffect(() => {
    api.get('/api/asset-categories/').then(r => setCategories(r.data)).catch(() => {});
    api.get('/api/departments').then(r => setDepartments(r.data)).catch(() => {});
    api.get('/api/users/').then(r => setUsers(r.data)).catch(() => {});
  }, []);

  const addTag = () => setTags([...tags, { key: '', value: '' }]);
  const removeTag = (i: number) => setTags(tags.filter((_, idx) => idx !== i));
  const updateTag = (i: number, field: 'key' | 'value', val: string) => {
    const next = [...tags];
    next[i] = { ...next[i], [field]: val };
    setTags(next);
  };

  const handleSubmit = async () => {
    if (!name.trim() || !categoryId) return;
    setLoading(true);
    setError('');
    try {
      await api.post('/api/assets/suggestions', {
        name,
        description: description || undefined,
        category_id: categoryId,
        department: department || undefined,
        owner_id: ownerId || undefined,
        criticality,
        risk_level: riskLevel,
        tags: tags.filter(t => t.key).map(t => ({ key: t.key, value: t.value || undefined })),
      });
      setSubmitted(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit suggestion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out', maxWidth: '720px' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/assets')} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Inventory</p>
          <h1 style={{ margin: 0 }}>Add Asset</h1>
        </div>
      </div>

      <div className="card">
        {submitted ? (
          <div>
            <div style={{ padding: '1rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', borderRadius: 'var(--radius)', border: '1px solid rgba(34, 197, 94, 0.2)', marginBottom: '1rem' }}>
              <p style={{ fontWeight: 600, color: 'var(--success)', marginBottom: '0.25rem' }}>Suggestion Submitted</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                An admin will review your suggestion. You'll be notified when it's approved.
              </p>
            </div>
            <button className="btn btn-primary" onClick={() => navigate('/assets')}>Back to Assets</button>
          </div>
        ) : (
          <>
            {error && (
              <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.25rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
                {error}
              </div>
            )}

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={labelStyle}>Asset Name *</label>
              <input className="form-control" placeholder="e.g. Web Server 01" value={name} onChange={(e) => setName(e.target.value)} disabled={loading} />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={labelStyle}>Description</label>
              <textarea className="form-control" rows={3} placeholder="Optional description" value={description} onChange={(e) => setDescription(e.target.value)} disabled={loading} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
              <div>
                <label style={labelStyle}>Category *</label>
                <select className="form-control" value={categoryId} onChange={(e) => setCategoryId(Number(e.target.value))} disabled={loading}>
                  <option value="">Select category</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>Department</label>
                <select className="form-control" value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading}>
                  <option value="">None</option>
                  {departments.map(d => <option key={d.id} value={d.name}>{d.name}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
              <div>
                <label style={labelStyle}>Criticality</label>
                <select className="form-control" value={criticality} onChange={(e) => setCriticality(e.target.value)} disabled={loading}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div>
                <label style={labelStyle}>Risk Level</label>
                <select className="form-control" value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} disabled={loading}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={labelStyle}>Owner</label>
              <select className="form-control" value={ownerId} onChange={(e) => setOwnerId(e.target.value ? Number(e.target.value) : '' )} disabled={loading}>
                <option value="">None</option>
                {nonAdminUsers.map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name} ({u.email})</option>)}
              </select>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <label style={{ ...labelStyle, marginBottom: 0 }}>Tags</label>
                <button className="btn btn-ghost" style={{ fontSize: '0.8125rem', padding: '0.25rem 0.75rem', gap: '0.375rem' }} onClick={addTag} type="button">
                  <Plus size={14} /> Add Tag
                </button>
              </div>
              {tags.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: 0 }}>No tags added yet.</p>
              ) : (
                tags.map((tag, i) => (
                  <div key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', alignItems: 'center' }}>
                    <input className="form-control" style={{ flex: 1 }} placeholder="Key" value={tag.key} onChange={(e) => updateTag(i, 'key', e.target.value)} disabled={loading} />
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>=</span>
                    <input className="form-control" style={{ flex: 1 }} placeholder="Value" value={tag.value} onChange={(e) => updateTag(i, 'value', e.target.value)} disabled={loading} />
                    <button className="btn btn-ghost" style={{ padding: '0.375rem', color: '#ef4444', flexShrink: 0 }} onClick={() => removeTag(i)} type="button" title="Remove tag">
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button className="btn btn-secondary" onClick={() => navigate('/assets')}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={!name.trim() || !categoryId || loading}>
                {loading ? <Loader2 size={16} className="animate-spin" /> : null}
                Submit Suggestion
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SuggestAsset;
