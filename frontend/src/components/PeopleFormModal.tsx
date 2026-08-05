import React, { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import api from '../services/api';

const ASSET_TYPES = [
  'Employee', 'Contractor', 'Consultant', 'Intern',
  'Temporary Staff', 'Third-Party User', 'Vendor User',
  'Service Account', 'Shared Account', 'Privileged Account',
  'Administrator', 'Developer', 'Security Personnel',
];

interface FormData {
  name: string;
  email: string;
  asset_type: string;
  department: string;
  job_title: string;
  asset_owner: string;
  status: string;
  start_date: string;
  end_date: string;
  description: string;
}

interface Props {
  asset?: any;
  onClose: () => void;
  onSuccess: () => void;
}

const PeopleFormModal = ({ asset, onClose, onSuccess }: Props) => {
  const isEditing = !!asset;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [departments, setDepartments] = useState<string[]>([]);

  useEffect(() => {
    api.get('/api/departments').then(r => setDepartments(r.data.map((d: any) => d.name))).catch(() => {});
  }, []);

  const [form, setForm] = useState<FormData>({
    name: '',
    email: '',
    asset_type: 'Employee',
    department: '',
    job_title: '',
    asset_owner: '',
    status: 'Active',
    start_date: '',
    end_date: '',
    description: '',
  });

  useEffect(() => {
    if (asset) {
      setForm({
        name: asset.name || '',
        email: asset.email || '',
        asset_type: asset.asset_type || 'Employee',
        department: asset.department || '',
        job_title: asset.job_title || '',
        asset_owner: asset.asset_owner || '',
        status: asset.status || 'Active',
        start_date: asset.start_date ? asset.start_date.slice(0, 10) : '',
        end_date: asset.end_date ? asset.end_date.slice(0, 10) : '',
        description: asset.description || '',
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
      const payload = {
        name: form.name,
        email: form.email || null,
        asset_type: form.asset_type,
        department: form.department || null,
        job_title: form.job_title || null,
        asset_owner: form.asset_owner || null,
        status: form.status,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        description: form.description || null,
      };
      if (isEditing) {
        await api.patch(`/api/people-assets/${asset.id}`, payload);
      } else {
        await api.post('/api/people-assets/', payload);
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
          <h3>{isEditing ? 'Edit People Asset' : 'Create People Asset'}</h3>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '0.25rem' }}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '70vh', overflowY: 'auto' }}>
            {error && (
              <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
                {error}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Name *</label>
                <input className="form-control" name="name" value={form.name} onChange={handleChange} required placeholder="e.g. John Doe" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Email</label>
                <input className="form-control" name="email" type="email" value={form.email} onChange={handleChange} placeholder="john@company.com" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Type *</label>
                <select className="form-control" name="asset_type" value={form.asset_type} onChange={handleChange} required>
                  {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Status</label>
                <select className="form-control" name="status" value={form.status} onChange={handleChange}>
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Department</label>
                  <select className="form-control" name="department" value={form.department} onChange={handleChange}>
                    <option value="">Select department</option>
                    {departments.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Job Title</label>
                <input className="form-control" name="job_title" value={form.job_title} onChange={handleChange} placeholder="e.g. Senior Developer" />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Owner</label>
              <input className="form-control" name="asset_owner" value={form.asset_owner} onChange={handleChange} placeholder="Person responsible for this asset" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Start Date</label>
                <input className="form-control" name="start_date" type="date" value={form.start_date} onChange={handleChange} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>End Date</label>
                <input className="form-control" name="end_date" type="date" value={form.end_date} onChange={handleChange} />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Description / Notes</label>
              <textarea className="form-control" name="description" value={form.description} onChange={handleChange} rows={3} placeholder="Additional notes..." style={{ resize: 'vertical' }} />
            </div>
          </div>
          <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : null}
              {isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PeopleFormModal;
