import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, Save, Monitor, HardDrive, User, Building2, Calendar } from 'lucide-react';
import api from '../../services/api';

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

const EndpointCreate = () => {
  const navigate = useNavigate();
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
      const res = await api.post('/api/endpoint-devices/', payload);
      navigate(`/assets/devices/${res.data.id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((d: any) => d.msg).join('; ') : detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/devices')} style={{ padding: '0.5rem' }}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Endpoint Devices</p>
            <h1>Add New Device</h1>
          </div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: '1200px' }}>
        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <Monitor size={18} color="var(--primary)" /> Basic Information
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Name <span style={{ color: 'var(--danger)' }}>*</span></label>
                  <input className="form-control" name="name" value={form.name} onChange={handleChange} required placeholder="e.g. JDOE-LAPTOP-001" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Type <span style={{ color: 'var(--danger)' }}>*</span></label>
                  <select className="form-control" name="asset_type" value={form.asset_type} onChange={handleChange} required>
                    {DEVICE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
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
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />

            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <HardDrive size={18} color="var(--primary)" /> Device Information
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
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
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />

            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <User size={18} color="var(--primary)" /> Ownership
              </h3>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Assigned To</label>
                <select className="form-control" name="assigned_to" value={form.assigned_to} onChange={handleChange}>
                  <option value="">Not assigned</option>
                  {people.map(p => <option key={p.id} value={p.id}>{p.first_name || p.last_name ? `${p.first_name || ''} ${p.last_name || ''}`.trim() : p.email}</option>)}
                </select>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />

            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <Building2 size={18} color="var(--primary)" /> Organizational Information
              </h3>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Department</label>
                <select className="form-control" name="department" value={form.department} onChange={handleChange}>
                  <option value="">Select department</option>
                  {departments.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />

            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <Calendar size={18} color="var(--primary)" /> Lifecycle Information
              </h3>
              <div style={{ maxWidth: '50%' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Acquisition Date</label>
                <input className="form-control" name="acquisition_date" type="date" value={form.acquisition_date} onChange={handleChange} />
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
            <button type="button" className="btn btn-outline" onClick={() => navigate('/assets/devices')}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              <span style={{ marginLeft: '0.5rem' }}>Create Device</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EndpointCreate;
