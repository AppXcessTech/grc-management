import { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import api from '../services/api';

const COMPUTE_TYPES = [
  'Application Server', 'Database Server', 'File Server', 'Backup Server', 'Domain Controller',
  'VMware VM', 'Hyper-V VM', 'Cloud VM',
  'EC2 Instance', 'Azure Virtual Machine', 'Google Compute Engine', 'Container Host',
];

interface FormData {
  name: string;
  asset_type: string;
  status: string;
  hostname: string;
  operating_system: string;
  owner_id: string;
  provisioned_date: string;
}

interface User {
  id: number;
  first_name: string | null;
  last_name: string | null;
  email: string;
}

interface Props {
  asset?: any;
  onClose: () => void;
  onSuccess: () => void;
}

const ComputeFormModal = ({ asset, onClose, onSuccess }: Props) => {
  const isEditing = !!asset;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    api.get('/api/users/').then(r => setUsers(r.data)).catch(() => {});
  }, []);

  const [form, setForm] = useState<FormData>({
    name: '',
    asset_type: 'Application Server',
    status: 'Active',
    hostname: '',
    operating_system: '',
    owner_id: '',
    provisioned_date: '',
  });

  useEffect(() => {
    if (asset) {
      setForm({
        name: asset.name || '',
        asset_type: asset.asset_type || 'Application Server',
        status: asset.status || 'Active',
        hostname: asset.hostname || '',
        operating_system: asset.operating_system || '',
        owner_id: asset.owner_id ? String(asset.owner_id) : '',
        provisioned_date: asset.provisioned_date ? asset.provisioned_date.slice(0, 10) : '',
      });
    }
  }, [asset]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload: any = {
        name: form.name,
        asset_type: form.asset_type,
        status: form.status,
        hostname: form.hostname || null,
        operating_system: form.operating_system || null,
        provisioned_date: form.provisioned_date || null,
      };
      if (form.owner_id) {
        payload.owner_id = parseInt(form.owner_id, 10);
      }
      if (isEditing) {
        await api.patch(`/api/compute-assets/${asset.id}`, payload);
      } else {
        await api.post('/api/compute-assets/', payload);
      }
      onSuccess();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((d: any) => d.msg).join('; ') : detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: '600px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{isEditing ? 'Edit Compute Asset' : 'Create Compute Asset'}</h3>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '0.25rem' }}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '70vh', overflowY: 'auto' }}>
            {error && (
              <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
                {error}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Name *</label>
                <input className="form-control" name="name" value={form.name} onChange={handleChange} required placeholder="e.g. PROD-APP-01" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Type *</label>
                <select className="form-control" name="asset_type" value={form.asset_type} onChange={handleChange} required>
                  {COMPUTE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Status</label>
                <select className="form-control" name="status" value={form.status} onChange={handleChange}>
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Hostname</label>
                <input className="form-control" name="hostname" value={form.hostname} onChange={handleChange} placeholder="e.g. srv-app01.example.com" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Operating System</label>
                <input className="form-control" name="operating_system" value={form.operating_system} onChange={handleChange} placeholder="e.g. Ubuntu 22.04 LTS" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Owner</label>
                <select className="form-control" name="owner_id" value={form.owner_id} onChange={handleChange}>
                  <option value="">Not assigned</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.first_name || u.last_name ? `${u.first_name || ''} ${u.last_name || ''}`.trim() : u.email}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Provisioned Date</label>
              <input className="form-control" name="provisioned_date" type="date" value={form.provisioned_date} onChange={handleChange} />
            </div>
          </div>

          <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : null}
              <span style={{ marginLeft: saving ? '0.5rem' : 0 }}>{isEditing ? 'Update' : 'Create'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComputeFormModal;
