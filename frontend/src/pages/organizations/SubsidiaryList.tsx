import { useEffect, useState } from 'react';
import { Plus, Loader2, GitBranch, Pencil, Trash2, X } from 'lucide-react';
import api from '../../services/api';

interface Organization {
  id: number;
  name: string;
}

interface Subsidiary {
  id: number;
  parent_organization_id: number;
  child_organization_id: number;
  relationship_type: string;
  created_at: string;
}

const SubsidiaryList = () => {
  const [subsidiaries, setSubsidiaries] = useState<Subsidiary[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newParentOrgId, setNewParentOrgId] = useState('');
  const [newChildOrgId, setNewChildOrgId] = useState('');
  const [newRelationshipType, setNewRelationshipType] = useState('');
  const [editingSub, setEditingSub] = useState<Subsidiary | null>(null);
  const [editParentOrgId, setEditParentOrgId] = useState('');
  const [editChildOrgId, setEditChildOrgId] = useState('');
  const [editRelationshipType, setEditRelationshipType] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [subsRes, orgsRes] = await Promise.all([
        api.get('/api/subsidiaries/'),
        api.get('/api/organizations/'),
      ]);
      setSubsidiaries(subsRes.data);
      setOrganizations(orgsRes.data);
      setError('');
    } catch {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newParentOrgId || !newChildOrgId || !newRelationshipType) return;
    try {
      await api.post('/api/subsidiaries/', {
        parent_organization_id: parseInt(newParentOrgId),
        child_organization_id: parseInt(newChildOrgId),
        relationship_type: newRelationshipType,
      });
      setNewParentOrgId(''); setNewChildOrgId(''); setNewRelationshipType('');
      fetchData();
    } catch { setError('Failed to create subsidiary'); }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSub) return;
    try {
      await api.patch(`/api/subsidiaries/${editingSub.id}`, {
        parent_organization_id: parseInt(editParentOrgId),
        child_organization_id: parseInt(editChildOrgId),
        relationship_type: editRelationshipType,
      });
      setEditingSub(null);
      fetchData();
    } catch { setError('Failed to update subsidiary'); }
  };

  const handleDelete = async (sub: Subsidiary) => {
    if (!window.confirm(`Delete this subsidiary relationship?`)) return;
    try {
      await api.delete(`/api/subsidiaries/${sub.id}`);
      fetchData();
    } catch { setError('Failed to delete subsidiary'); }
  };

  const openEdit = (sub: Subsidiary) => {
    setEditParentOrgId(sub.parent_organization_id.toString());
    setEditChildOrgId(sub.child_organization_id.toString());
    setEditRelationshipType(sub.relationship_type);
    setEditingSub(sub);
  };

  const orgName = (id: number) => {
    const org = organizations.find((o) => o.id === id);
    return org ? org.name : `Org #${id}`;
  };

  if (loading && subsidiaries.length === 0) {
    return <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <Loader2 className="animate-spin" size={40} color="var(--primary)" />
    </div>;
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Organization</p>
          <h1>Subsidiaries</h1>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Parent Organization</label>
            <select className="form-control" value={newParentOrgId} onChange={(e) => setNewParentOrgId(e.target.value)} required>
              <option value="">Select parent...</option>
              {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Child Organization</label>
            <select className="form-control" value={newChildOrgId} onChange={(e) => setNewChildOrgId(e.target.value)} required>
              <option value="">Select child...</option>
              {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Relationship Type</label>
            <input className="form-control" placeholder="e.g. subsidiary, parent" value={newRelationshipType} onChange={(e) => setNewRelationshipType(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ padding: '0.5rem 1.5rem' }}><Plus size={18} /> Create</button>
        </form>
      </div>

      {error && <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>{error}</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Parent Organization</th><th>Child Organization</th><th>Relationship Type</th><th>Created</th><th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {subsidiaries.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  <GitBranch size={48} style={{ marginBottom: '1rem', opacity: 0.2 }} />
                  <p>No subsidiaries found.</p>
                </td>
              </tr>
            ) : subsidiaries.map((sub) => (
              <tr key={sub.id}>
                <td style={{ fontWeight: 600 }}>{orgName(sub.parent_organization_id)}</td>
                <td style={{ fontWeight: 600 }}>{orgName(sub.child_organization_id)}</td>
                <td><span className="badge badge-indigo" style={{ textTransform: 'capitalize' }}>{sub.relationship_type}</span></td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>{new Date(sub.created_at).toLocaleDateString()}</td>
                <td style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                    <button className="btn" style={{ background: 'none', color: 'var(--primary)', padding: '0.5rem' }} onClick={() => openEdit(sub)} title="Edit"><Pencil size={16} /></button>
                    <button className="btn" style={{ background: 'none', color: '#ef4444', padding: '0.5rem' }} onClick={() => handleDelete(sub)} title="Delete"><Trash2 size={16} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingSub && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }} onClick={() => setEditingSub(null)}>
          <div className="card" style={{ width: '520px', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Edit Subsidiary</h2>
              <button className="btn btn-ghost" onClick={() => setEditingSub(null)} style={{ padding: '0.375rem' }}><X size={20} /></button>
            </div>
            <form onSubmit={handleEdit}>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Parent Organization</label>
                  <select className="form-control" value={editParentOrgId} onChange={(e) => setEditParentOrgId(e.target.value)} required>
                    <option value="">Select parent...</option>
                    {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Child Organization</label>
                  <select className="form-control" value={editChildOrgId} onChange={(e) => setEditChildOrgId(e.target.value)} required>
                    <option value="">Select child...</option>
                    {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Relationship Type</label>
                <input className="form-control" placeholder="e.g. subsidiary, parent" value={editRelationshipType} onChange={(e) => setEditRelationshipType(e.target.value)} required />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.75rem' }}>Save Changes</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubsidiaryList;