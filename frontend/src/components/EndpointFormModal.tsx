import { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import api from '../services/api';

const DEVICE_TYPES = [
  'Windows Laptop', 'macOS Laptop', 'Linux Workstation', 'Desktop Computer',
  'iPhone', 'Android Phone', 'Tablet', 'Rugged Device',
  'Kiosk', 'Point-of-Sale System', 'Meeting Room System', 'Executive Device',
];

interface FormData {
  name: string;
  asset_type: string;
  status: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  assigned_to: string;
  department: string;
  acquisition_date: string;
}

interface PeopleAsset {
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

const EndpointFormModal = ({ asset, onClose, onSuccess }: Props) => {
  const isEditing = !!asset;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [people, setPeople] = useState<PeopleAsset[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);

  useEffect(() => {
    api.get('/api/departments').then(r => setDepartments(r.data.map((d: any) => d.name))).catch(() => {});
    api.get('/api/users/').then(r => setPeople(r.data)).catch(() => {});
  }, []);

  const [form, setForm] = useState<FormData>({
    name: '',
    asset_type: 'Windows Laptop',
    status: 'Active',
    manufacturer: '',
    model: '',
    serial_number: '',
    assigned_to: '',
    department: '',
    acquisition_date: '',
  });

  useEffect(() => {
    if (asset) {
      setForm({
        name: asset.name || '',
        asset_type: asset.asset_type || 'Windows Laptop',
        status: asset.status || 'Active',
        manufacturer: asset.manufacturer || '',
        model: asset.model || '',
        serial_number: asset.serial_number || '',
        assigned_to: asset.assigned_to ? String(asset.assigned_to) : '',
        department: asset.department || '',
        acquisition_date: asset.acquisition_date ? asset.acquisition_date.slice(0, 10) : '',
      });
    }
  }, [asset]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
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
        manufacturer: form.manufacturer || null,
        model: form.model || null,
        serial_number: form.serial_number || null,
        department: form.department || null,
        acquisition_date: form.acquisition_date || null,
      };
      if (form.assigned_to) {
        payload.assigned_to = parseInt(form.assigned_to, 10);
      }
      if (isEditing) {
        await api.patch(`/api/endpoint-devices/${asset.id}`, payload);
      } else {
        await api.post('/api/endpoint-devices/', payload);
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
          <h3>{isEditing ? 'Edit Endpoint Device' : 'Create Endpoint Device'}</h3>
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
                <input className="form-control" name="name" value={form.name} onChange={handleChange} required placeholder="e.g. JDOE-LAPTOP-001" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Type *</label>
                <select className="form-control" name="asset_type" value={form.asset_type} onChange={handleChange} required>
                  {DEVICE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
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
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Department</label>
                <select className="form-control" name="department" value={form.department} onChange={handleChange}>
                  <option value="">Select department</option>
                  {departments.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Manufacturer</label>
                <input className="form-control" name="manufacturer" value={form.manufacturer} onChange={handleChange} placeholder="e.g. Dell" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Model</label>
                <input className="form-control" name="model" value={form.model} onChange={handleChange} placeholder="e.g. Latitude 5540" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Serial Number</label>
                <input className="form-control" name="serial_number" value={form.serial_number} onChange={handleChange} placeholder="e.g. SN-12345" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Assigned To</label>
                <select className="form-control" name="assigned_to" value={form.assigned_to} onChange={handleChange}>
                  <option value="">Not assigned</option>
                  {people.map(p => <option key={p.id} value={p.id}>{p.first_name || p.last_name ? `${p.first_name || ''} ${p.last_name || ''}`.trim() : p.email}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Acquisition Date</label>
                <input className="form-control" name="acquisition_date" type="date" value={form.acquisition_date} onChange={handleChange} />
              </div>
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

export default EndpointFormModal;
