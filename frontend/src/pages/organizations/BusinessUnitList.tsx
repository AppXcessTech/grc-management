import { useEffect, useState } from 'react';
import { Plus, Loader2, Briefcase, Pencil, Trash2, X } from 'lucide-react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface BusinessUnit {
  id: number;
  name: string;
  description: string | null;
  organization_id: number;
  created_at: string;
}

interface OrgOption {
  id: number;
  name: string;
  slug: string;
}

const BusinessUnitList = () => {
  const { user } = useAuth();
  const [bunits, setBunits] = useState<BusinessUnit[]>([]);
  const [organizations, setOrganizations] = useState<OrgOption[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<number | null>(user?.organization_id || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [editingBu, setEditingBu] = useState<BusinessUnit | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  const selectedOrg = organizations.find((o) => o.id === selectedOrgId);

  useEffect(() => {
    api.get('/api/organizations/')
      .then((res) => {
        const orgs: OrgOption[] = res.data;
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) setSelectedOrgId(orgs[0].id);
      })
      .catch(() => setError('Failed to load organizations'));
  }, []);

  useEffect(() => {
    if (!selectedOrg?.slug) return;
    setLoading(true);
    api.get(`/api/organizations/${selectedOrg.slug}/bunits`)
      .then((res) => { setBunits(res.data); setError(''); })
      .catch(() => setError('Failed to load business units'))
      .finally(() => setLoading(false));
  }, [selectedOrg?.slug]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrg) return;
    try {
      await api.post(`/api/organizations/${selectedOrg.slug}/bunits`, {
        organization_id: selectedOrg.id, name: newName, description: newDesc || null,
      });
      setNewName(''); setNewDesc('');
      const res = await api.get(`/api/organizations/${selectedOrg.slug}/bunits`);
      setBunits(res.data);
    } catch { setError('Failed to create business unit'); }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingBu || !selectedOrg) return;
    try {
      await api.patch(`/api/organizations/${selectedOrg.slug}/bunits/${editingBu.id}`, {
        name: editName, description: editDesc || null,
      });
      setEditingBu(null);
      const res = await api.get(`/api/organizations/${selectedOrg.slug}/bunits`);
      setBunits(res.data);
    } catch { setError('Failed to update business unit'); }
  };

  const handleDelete = async (bu: BusinessUnit) => {
    if (!window.confirm(`Delete business unit "${bu.name}"?`)) return;
    if (!selectedOrg) return;
    try {
      await api.delete(`/api/organizations/${selectedOrg.slug}/bunits/${bu.id}`);
      const res = await api.get(`/api/organizations/${selectedOrg.slug}/bunits`);
      setBunits(res.data);
    } catch { setError('Failed to delete business unit'); }
  };

  const openEdit = (bu: BusinessUnit) => {
    setEditName(bu.name);
    setEditDesc(bu.description || '');
    setEditingBu(bu);
  };

  if (loading && bunits.length === 0 && !error) {
    return <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <Loader2 className="animate-spin" size={40} color="var(--primary)" />
    </div>;
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Organization</p>
          <h1>Business Units</h1>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'flex-end', gap: '1rem' }}>
        <div className="form-group" style={{ minWidth: '280px' }}>
          <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>Select Organization</label>
          <select className="form-control" value={selectedOrgId ?? ''} onChange={(e) => setSelectedOrgId(parseInt(e.target.value))}>
            {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
          </select>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Name</label>
            <input className="form-control" placeholder="Business unit name" value={newName} onChange={(e) => setNewName(e.target.value)} required />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Description</label>
            <input className="form-control" placeholder="Brief description" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary" style={{ padding: '0.5rem 1.5rem' }}><Plus size={18} /> Create</button>
        </form>
      </div>

      {error && <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>{error}</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Organization</th><th>Name</th><th>Description</th><th>Created</th><th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {bunits.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  <Briefcase size={48} style={{ marginBottom: '1rem', opacity: 0.2 }} />
                  <p>No business units found for this organization.</p>
                </td>
              </tr>
            ) : bunits.map((bu) => (
              <tr key={bu.id}>
                <td style={{ color: 'var(--text-muted)' }}>{selectedOrg?.name || '-'}</td>
                <td style={{ fontWeight: 600 }}>{bu.name}</td>
                <td style={{ color: 'var(--text-muted)' }}>{bu.description || '-'}</td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>{new Date(bu.created_at).toLocaleDateString()}</td>
                <td style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                    <button className="btn" style={{ background: 'none', color: 'var(--primary)', padding: '0.5rem' }} onClick={() => openEdit(bu)} title="Edit"><Pencil size={16} /></button>
                    <button className="btn" style={{ background: 'none', color: '#ef4444', padding: '0.5rem' }} onClick={() => handleDelete(bu)} title="Delete"><Trash2 size={16} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingBu && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }} onClick={() => setEditingBu(null)}>
          <div className="card" style={{ width: '440px', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Edit Business Unit</h2>
              <button className="btn btn-ghost" onClick={() => setEditingBu(null)} style={{ padding: '0.375rem' }}><X size={20} /></button>
            </div>
            <form onSubmit={handleEdit}>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Name</label>
                <input className="form-control" required value={editName} onChange={(e) => setEditName(e.target.value)} />
              </div>
              <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Description</label>
                <input className="form-control" placeholder="Brief description" value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.75rem' }}>Save Changes</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessUnitList;