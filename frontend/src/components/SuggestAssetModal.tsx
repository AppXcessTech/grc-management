import React, { useEffect, useState } from 'react';
import { X, Loader2, Plus, Trash2 } from 'lucide-react';
import api from '../services/api';

interface AssetCategory {
  id: number;
  name: string;
}

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

const SuggestAssetModal: React.FC<Props> = ({ onClose, onSuccess }) => {
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [department, setDepartment] = useState('');
  const [criticality, setCriticality] = useState('Medium');
  const [riskLevel, setRiskLevel] = useState('Medium');
  const [tags, setTags] = useState<Array<{ key: string; value: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/api/asset-categories/').then(r => setCategories(r.data)).catch(() => {});
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
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.125rem' }}>Add Asset</h2>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '0.25rem' }}>
            <X size={18} />
          </button>
        </div>

        {submitted ? (
          <div>
            <div style={{ padding: '1rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', borderRadius: 'var(--radius)', border: '1px solid rgba(34, 197, 94, 0.2)', marginBottom: '1rem' }}>
              <p style={{ fontWeight: 600, color: 'var(--success)', marginBottom: '0.25rem' }}>Suggestion Submitted</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                An admin will review your suggestion. You'll be notified when it's approved.
              </p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={onSuccess}>Done</button>
            </div>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <label className="form-label">Asset Name *</label>
              <input className="form-control" placeholder="e.g. Web Server 01" value={name} onChange={(e) => setName(e.target.value)} disabled={loading} />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label className="form-label">Description</label>
              <textarea className="form-control" rows={3} placeholder="Optional description" value={description} onChange={(e) => setDescription(e.target.value)} disabled={loading} />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label className="form-label">Category *</label>
              <select className="form-control" value={categoryId} onChange={(e) => setCategoryId(Number(e.target.value))} disabled={loading}>
                <option value="">Select category</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label className="form-label">Department</label>
              <input className="form-control" placeholder="e.g. Engineering" value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading} />
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
              <div style={{ flex: 1 }}>
                <label className="form-label">Criticality</label>
                <select className="form-control" value={criticality} onChange={(e) => setCriticality(e.target.value)} disabled={loading}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label className="form-label">Risk Level</label>
                <select className="form-control" value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} disabled={loading}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <label className="form-label" style={{ marginBottom: 0 }}>Tags</label>
                <button className="btn btn-ghost" style={{ fontSize: '0.75rem', padding: '0.125rem 0.5rem' }} onClick={addTag} type="button">
                  <Plus size={12} /> Add Tag
                </button>
              </div>
              {tags.map((tag, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.375rem' }}>
                  <input className="form-control" style={{ flex: 1 }} placeholder="Key" value={tag.key} onChange={(e) => updateTag(i, 'key', e.target.value)} disabled={loading} />
                  <input className="form-control" style={{ flex: 1 }} placeholder="Value" value={tag.value} onChange={(e) => updateTag(i, 'value', e.target.value)} disabled={loading} />
                  <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#ef4444' }} onClick={() => removeTag(i)} type="button">
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>

            {error && (
              <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
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

export default SuggestAssetModal;
