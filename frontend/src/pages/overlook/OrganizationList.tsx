import React, { useEffect, useState } from 'react';
import { Loader2, Search, Plus, X, Copy, Check, Edit3, Trash2 } from 'lucide-react';
import api from '../../services/api';

interface OrganizationStats {
  id: number;
  name: string;
  external_id: string;
  user_count: number;
  department_count: number;
  business_unit_count: number;
  subsidiary_count: number;
}

interface CreatedOrgResponse {
  id: number;
  name: string;
  slug: string;
  domain: string | null;
  industry: string | null;
  size: string;
  admin_email: string;
  generated_password: string;
}

const OverlookOrganizationList = () => {
  const [orgs, setOrgs] = useState<OrganizationStats[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingOrg, setEditingOrg] = useState<OrganizationStats | null>(null);
  const [createdOrg, setCreatedOrg] = useState<CreatedOrgResponse | null>(null);
  const [copied, setCopied] = useState<'email' | 'password' | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    domain: '',
    industry: '',
    size: 'startup',
    admin_email: '',
    admin_first_name: '',
    admin_last_name: '',
  });
  const [editData, setEditData] = useState({
    name: '',
    slug: '',
    domain: '',
    industry: '',
    size: 'startup',
  });
  const [createError, setCreateError] = useState('');
  const [editError, setEditError] = useState('');

  const fetchOrgs = async () => {
    try {
      const response = await api.get('/api/overlook/organizations/');
      setOrgs(response.data);
    } catch (err) {
      console.error('Failed to load organizations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);


  const handleEdit = (org: OrganizationStats) => {
    setEditingOrg(org);
    setEditData({ name: org.name, slug: '', domain: '', industry: '', size: 'startup' });
    setEditError('');
    setShowEditModal(true);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingOrg) return;
    setEditError('');

    const payload: Record<string, any> = {};
    if (editData.name.trim()) payload.name = editData.name.trim();
    if (editData.slug.trim()) payload.slug = editData.slug.trim();
    if (editData.domain.trim()) payload.domain = editData.domain.trim();
    if (editData.industry.trim()) payload.industry = editData.industry.trim();
    if (editData.size) payload.size = editData.size;

    try {
      await api.patch(`/api/overlook/organizations/${editingOrg.id}`, payload);
      setShowEditModal(false);
      setEditingOrg(null);
      fetchOrgs();
    } catch (err: any) {
      setEditError(err.response?.data?.detail || 'Failed to update organization');
    }
  };

  const handleDelete = async (orgId: number) => {
    try {
      await api.delete(`/api/overlook/organizations/${orgId}`);
      setDeleteConfirm(null);
      fetchOrgs();
    } catch (err) {
      alert('Failed to delete organization');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError('');
    try {
      const response = await api.post('/api/overlook/organizations/', formData);
      setCreatedOrg(response.data);
      setShowCreateModal(false);
      setFormData({ name: '', slug: '', domain: '', industry: '', size: 'startup', admin_email: '', admin_first_name: '', admin_last_name: '' });
      fetchOrgs();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create organization');
    }
  };

  const handleCopy = (value: string, field: 'email' | 'password') => {
    navigator.clipboard.writeText(value);
    setCopied(field);
    setTimeout(() => setCopied(null), 2000);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} color="#f43f5e" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: '#f43f5e', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Management</p>
          <h1>Tenants</h1>
        </div>
        <button
          className="btn btn-primary"
          style={{ backgroundColor: '#f43f5e', borderColor: '#f43f5e', marginBottom: '0.5rem' }}
          onClick={() => setShowCreateModal(true)}
        >
          <Plus size={18} />
          Create Organization
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Organization</th>
              <th>Users</th>
              <th>Depts</th>
              <th>BUs</th>
              <th>Subs</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orgs.map((org) => (
              <tr key={org.id}>
                <td style={{ fontWeight: 600 }}>{org.name}</td>
                <td>{org.user_count}</td>
                <td>{org.department_count}</td>
                <td>{org.business_unit_count}</td>
                <td>{org.subsidiary_count}</td>
                <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', marginRight: '0.375rem' }}
                    onClick={() => handleEdit(org)}
                    title="Edit organization"
                  >
                    <Edit3 size={14} />
                  </button>
                  <button
                    className="btn btn-danger"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                    onClick={() => setDeleteConfirm(org.id)}
                    title="Delete organization"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit modal */}
      {showEditModal && editingOrg && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '480px', padding: '2rem',
            position: 'relative', maxHeight: '90vh', overflowY: 'auto'
          }}>
            <button
              onClick={() => { setShowEditModal(false); setEditingOrg(null); }}
              style={{
                position: 'absolute', top: '1rem', right: '1rem',
                background: 'none', border: 'none', color: 'var(--text-muted)',
                cursor: 'pointer', padding: '0.25rem'
              }}
            >
              <X size={20} />
            </button>
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Edit Organization</h2>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Updating: <strong>{editingOrg.name}</strong>
            </p>
            {editError && (
              <div style={{
                padding: '0.75rem 1rem', backgroundColor: 'rgba(239,68,68,0.1)',
                color: '#ef4444', borderRadius: 'var(--radius)',
                marginBottom: '1rem', fontSize: '0.875rem',
                border: '1px solid rgba(239,68,68,0.2)'
              }}>
                {editError}
              </div>
            )}
            <form onSubmit={handleUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Name</label>
                <input
                  className="form-control"
                  value={editData.name}
                  onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                  placeholder={editingOrg.name}
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Slug</label>
                <input
                  className="form-control"
                  value={editData.slug}
                  onChange={(e) => setEditData({ ...editData, slug: e.target.value })}
                  placeholder={editingOrg.external_id}
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Domain</label>
                <input
                  className="form-control"
                  value={editData.domain}
                  onChange={(e) => setEditData({ ...editData, domain: e.target.value })}
                  placeholder="acme.com"
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Industry</label>
                <input
                  className="form-control"
                  value={editData.industry}
                  onChange={(e) => setEditData({ ...editData, industry: e.target.value })}
                  placeholder="Technology"
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Size</label>
                <select
                  className="form-control"
                  value={editData.size}
                  onChange={(e) => setEditData({ ...editData, size: e.target.value })}
                >
                  <option value="startup">Startup</option>
                  <option value="SMB">SMB</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="submit" className="btn btn-primary" style={{ backgroundColor: '#f43f5e', borderColor: '#f43f5e', flex: 1 }}>
                  Save Changes
                </button>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => { setShowEditModal(false); setEditingOrg(null); }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      {deleteConfirm !== null && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: '400px', padding: '2rem', position: 'relative', textAlign: 'center' }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '50%',
              backgroundColor: 'rgba(239,68,68,0.1)', display: 'flex',
              alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem'
            }}>
              <Trash2 size={24} color="#ef4444" />
            </div>
            <h2 style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>Delete Organization?</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              This action cannot be undone. All data for this tenant will be permanently removed.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                className="btn btn-danger"
                style={{ flex: 1 }}
                onClick={() => handleDelete(deleteConfirm)}
              >
                Delete
              </button>
              <button
                className="btn btn-secondary"
                style={{ flex: 1 }}
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '520px', padding: '2rem',
            position: 'relative', maxHeight: '90vh', overflowY: 'auto'
          }}>
            <button
              onClick={() => setShowCreateModal(false)}
              style={{
                position: 'absolute', top: '1rem', right: '1rem',
                background: 'none', border: 'none', color: 'var(--text-muted)',
                cursor: 'pointer', padding: '0.25rem'
              }}
            >
              <X size={20} />
            </button>
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Create Organization</h2>
            {createError && (
              <div style={{
                padding: '0.75rem 1rem', backgroundColor: 'rgba(239,68,68,0.1)',
                color: '#ef4444', borderRadius: 'var(--radius)',
                marginBottom: '1rem', fontSize: '0.875rem',
                border: '1px solid rgba(239,68,68,0.2)'
              }}>
                {createError}
              </div>
            )}
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Organization Name</label>
                <input
                  className="form-control"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="Acme Corp"
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Slug</label>
                <input
                  className="form-control"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  required
                  placeholder="acme-corp"
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Domain</label>
                <input
                  className="form-control"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                  placeholder="acme.com"
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Industry</label>
                <input
                  className="form-control"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  placeholder="Technology"
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Size</label>
                <select
                  className="form-control"
                  value={formData.size}
                  onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                >
                  <option value="startup">Startup</option>
                  <option value="SMB">SMB</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
              <hr style={{ borderColor: 'var(--border)', margin: '0.5rem 0' }} />
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 500 }}>Super Admin Credentials</p>
              <div className="form-group">
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Admin Email</label>
                <input
                  type="email"
                  className="form-control"
                  value={formData.admin_email}
                  onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                  required
                  placeholder="admin@acme.com"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>First Name</label>
                  <input
                    className="form-control"
                    value={formData.admin_first_name}
                    onChange={(e) => setFormData({ ...formData, admin_first_name: e.target.value })}
                    placeholder="Jane"
                  />
                </div>
                <div className="form-group">
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Last Name</label>
                  <input
                    className="form-control"
                    value={formData.admin_last_name}
                    onChange={(e) => setFormData({ ...formData, admin_last_name: e.target.value })}
                    placeholder="Doe"
                  />
                </div>
              </div>
              <button type="submit" className="btn btn-primary" style={{ backgroundColor: '#f43f5e', borderColor: '#f43f5e', marginTop: '0.5rem' }}>
                Create Organization
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Credentials success modal */}
      {createdOrg && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '480px', padding: '2rem',
            position: 'relative'
          }}>
            <button
              onClick={() => setCreatedOrg(null)}
              style={{
                position: 'absolute', top: '1rem', right: '1rem',
                background: 'none', border: 'none', color: 'var(--text-muted)',
                cursor: 'pointer', padding: '0.25rem'
              }}
            >
              <X size={20} />
            </button>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{
                width: '48px', height: '48px', borderRadius: '50%',
                backgroundColor: 'rgba(16,185,129,0.1)', display: 'flex',
                alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem'
              }}>
                <Check size={24} color="#10b981" />
              </div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Organization Created</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                {createdOrg.name} has been provisioned with a super admin.
              </p>
            </div>
            <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Admin Email</span>
                  <p style={{ fontSize: '0.9375rem', fontWeight: 600, marginTop: '0.25rem', fontFamily: 'monospace' }}>{createdOrg.admin_email}</p>
                </div>
                <button
                  onClick={() => handleCopy(createdOrg.admin_email, 'email')}
                  style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.375rem', cursor: 'pointer', color: copied === 'email' ? '#10b981' : 'var(--text-muted)' }}
                  title="Copy email"
                >
                  {copied === 'email' ? <Check size={16} /> : <Copy size={16} />}
                </button>
              </div>
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Generated Password</span>
                  <p style={{ fontSize: '0.9375rem', fontWeight: 600, marginTop: '0.25rem', fontFamily: 'monospace' }}>{createdOrg.generated_password}</p>
                </div>
                <button
                  onClick={() => handleCopy(createdOrg.generated_password, 'password')}
                  style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.375rem', cursor: 'pointer', color: copied === 'password' ? '#10b981' : 'var(--text-muted)' }}
                  title="Copy password"
                >
                  {copied === 'password' ? <Check size={16} /> : <Copy size={16} />}
                </button>
              </div>
            </div>
            <div style={{ padding: '0.75rem 1rem', backgroundColor: 'rgba(245,158,11,0.1)', borderRadius: 'var(--radius)', fontSize: '0.8125rem', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)', marginBottom: '1.5rem' }}>
              These credentials will only be shown once. Share them securely with the customer's designated super admin.
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', backgroundColor: '#f43f5e', borderColor: '#f43f5e' }}
              onClick={() => setCreatedOrg(null)}
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default OverlookOrganizationList;