import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, Save, Server, Cpu, User, Calendar } from 'lucide-react';
import api from '../../services/api';

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

const ComputeCreate = () => {
  const navigate = useNavigate();
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
      const res = await api.post('/api/compute-assets/', payload);
      navigate(`/assets/servers/${res.data.id}`);
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
          <button className="btn btn-ghost" onClick={() => navigate('/assets/servers')} style={{ padding: '0.5rem' }}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Servers & Compute</p>
            <h1>Add New Compute Asset</h1>
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
                <Server size={18} color="var(--primary)" /> Basic Information
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Name <span style={{ color: 'var(--danger)' }}>*</span></label>
                  <input className="form-control" name="name" value={form.name} onChange={handleChange} required placeholder="e.g. PROD-APP-01" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Asset Type <span style={{ color: 'var(--danger)' }}>*</span></label>
                  <select className="form-control" name="asset_type" value={form.asset_type} onChange={handleChange} required>
                    {COMPUTE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
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
                <Cpu size={18} color="var(--primary)" /> Identification
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Hostname</label>
                  <input className="form-control" name="hostname" value={form.hostname} onChange={handleChange} placeholder="e.g. srv-app01.example.com" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Operating System</label>
                  <input className="form-control" name="operating_system" value={form.operating_system} onChange={handleChange} placeholder="e.g. Ubuntu 22.04 LTS" />
                </div>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />

            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <User size={18} color="var(--primary)" /> Ownership
              </h3>
              <div>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Owner</label>
                <select className="form-control" name="owner_id" value={form.owner_id} onChange={handleChange}>
                  <option value="">Not assigned</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.first_name || u.last_name ? `${u.first_name || ''} ${u.last_name || ''}`.trim() : u.email}</option>)}
                </select>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />

            <div>
              <h3 style={{ fontSize: '0.9375rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                <Calendar size={18} color="var(--primary)" /> Lifecycle Information
              </h3>
              <div style={{ maxWidth: '50%' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem' }}>Provisioned Date</label>
                <input className="form-control" name="provisioned_date" type="date" value={form.provisioned_date} onChange={handleChange} />
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
            <button type="button" className="btn btn-outline" onClick={() => navigate('/assets/servers')}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              <span style={{ marginLeft: '0.5rem' }}>Create Compute Asset</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComputeCreate;
