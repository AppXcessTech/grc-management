import React, { useState, useEffect } from 'react';
import { X, Loader2, Plus as PlusIcon } from 'lucide-react';
import api from '../services/api';

interface AssetCategory {
  id: number;
  name: string;
}

interface AssetTag {
  key: string;
  value: string | null;
}

interface Asset {
  id: number;
  name: string;
  description: string | null;
  source: string;
  status: string;
  department: string | null;
  criticality: string;
  risk_level: string;
  owner_id: number | null;
  category_id: number;
  tags: AssetTag[];
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

interface Department {
  id: number;
  name: string;
  code: string | null;
}

interface AssetFormModalProps {
  asset: Asset | null;
  onClose: () => void;
  onSuccess: () => void;
}

const AssetFormModal: React.FC<AssetFormModalProps> = ({ asset, onClose, onSuccess }) => {
  const isEdit = !!asset;
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingData, setFetchingData] = useState(true);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category_id: '',
    source: 'Manual',
    status: 'Active',
    department: '',
    criticality: 'Medium',
    risk_level: 'Medium',
    owner_id: '',
  });
  const [tags, setTags] = useState<AssetTag[]>([]);
  const [newTagKey, setNewTagKey] = useState('');
  const [newTagValue, setNewTagValue] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [catsRes, deptsRes, usersRes] = await Promise.all([
          api.get('/api/asset-categories/'),
          api.get('/api/departments'),
          api.get('/api/users/'),
        ]);
        setCategories(catsRes.data);
        setDepartments(deptsRes.data);
        setUsers(usersRes.data);
      } catch (err) {
        console.error('Failed to fetch modal data', err);
      } finally {
        setFetchingData(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (asset) {
      setFormData({
        name: asset.name || '',
        description: asset.description || '',
        category_id: String(asset.category_id || ''),
        source: asset.source || 'Manual',
        status: asset.status || 'Active',
        department: asset.department || '',
        criticality: asset.criticality || 'Medium',
        risk_level: asset.risk_level || 'Medium',
        owner_id: String(asset.owner_id || ''),
      });
      setTags(asset.tags?.map(t => ({ key: t.key, value: t.value })) || []);
    }
  }, [asset]);

  const addTag = () => {
    if (!newTagKey.trim()) return;
    setTags([...tags, { key: newTagKey.trim(), value: newTagValue.trim() || null }]);
    setNewTagKey('');
    setNewTagValue('');
  };

  const removeTag = (i: number) => {
    setTags(tags.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const payload: any = {
      ...formData,
      category_id: parseInt(formData.category_id),
      owner_id: formData.owner_id ? parseInt(formData.owner_id) : null,
      tags: tags.length > 0 ? tags : undefined,
    };

    try {
      if (isEdit) {
        await api.patch(`/api/assets/${asset!.id}`, payload);
      } else {
        await api.post('/api/assets/', payload);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save asset');
    } finally {
      setLoading(false);
    }
  };

  if (fetchingData) {
    return (
      <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
        <Loader2 className="animate-spin" size={40} color="white" />
      </div>
    );
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="card" style={{ width: '100%', maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2>{isEdit ? 'Edit Asset' : 'Add New Asset'}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X /></button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontSize: '0.875rem' }}>{error}</div>}

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Name <span style={{ color: 'var(--danger)' }}>*</span></label>
            <input type="text" required className="form-control" style={{ width: '100%' }}
              placeholder="e.g. Primary Database"
              value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Category <span style={{ color: 'var(--danger)' }}>*</span></label>
              <select required className="form-control" style={{ width: '100%' }}
                value={formData.category_id} onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}>
                <option value="">Select category</option>
                {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Source</label>
              <select className="form-control" style={{ width: '100%' }}
                value={formData.source} onChange={(e) => setFormData({ ...formData, source: e.target.value })}>
                <option value="Manual">Manual</option>
                <option value="AWS">AWS</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Status</label>
              <select className="form-control" style={{ width: '100%' }}
                value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })}>
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
                <option value="Archived">Archived</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Department</label>
              <select className="form-control" style={{ width: '100%' }}
                value={formData.department} onChange={(e) => setFormData({ ...formData, department: e.target.value })}>
                <option value="">None</option>
                {departments.map(d => <option key={d.id} value={d.name}>{d.name}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Criticality</label>
              <select className="form-control" style={{ width: '100%' }}
                value={formData.criticality} onChange={(e) => setFormData({ ...formData, criticality: e.target.value })}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Risk Level</label>
              <select className="form-control" style={{ width: '100%' }}
                value={formData.risk_level} onChange={(e) => setFormData({ ...formData, risk_level: e.target.value })}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Owner</label>
            <select className="form-control" style={{ width: '100%' }}
              value={formData.owner_id} onChange={(e) => setFormData({ ...formData, owner_id: e.target.value })}>
              <option value="">None</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name} ({u.email})</option>)}
            </select>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Description</label>
            <textarea className="form-control" style={{ width: '100%', minHeight: '80px' }}
              placeholder="Detailed description..."
              value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Tags</label>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
              {tags.map((tag, i) => (
                <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: 'var(--radius)', background: 'var(--bg-secondary)', fontSize: '0.8125rem' }}>
                  <strong>{tag.key}</strong>{tag.value ? `: ${tag.value}` : ''}
                  <button type="button" onClick={() => removeTag(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: 0, lineHeight: 1 }}>&times;</button>
                </span>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input className="form-control" style={{ flex: 1 }} placeholder="Key" value={newTagKey} onChange={(e) => setNewTagKey(e.target.value)} />
              <input className="form-control" style={{ flex: 1 }} placeholder="Value (optional)" value={newTagValue} onChange={(e) => setNewTagValue(e.target.value)} />
              <button type="button" className="btn btn-secondary" onClick={addTag} style={{ whiteSpace: 'nowrap' }}>
                <PlusIcon size={16} />
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" size={18} /> : isEdit ? 'Update Asset' : 'Create Asset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AssetFormModal;
