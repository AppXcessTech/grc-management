import { useEffect, useState } from 'react';
import { ShieldCheck, Loader2, Settings, Plus, X, Pencil, Trash2 } from 'lucide-react';
import api from '../../services/api';
import PermissionModal from '../../components/PermissionModal';

interface Role {
  id: number;
  name: string;
  display_name: string;
  is_system: boolean;
}

const RoleList = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<{id: number, name: string} | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [newRole, setNewRole] = useState({ name: '', display_name: '' });
  const [editForm, setEditForm] = useState({ name: '', display_name: '' });
  const [createError, setCreateError] = useState('');
  const [editError, setEditError] = useState('');
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchRoles = async () => {
    try {
      const response = await api.get('/api/roles/');
      setRoles(response.data);
    } catch (err) {
      console.error('Failed to fetch roles', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRoles(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      await api.post('/api/roles/', newRole);
      setShowCreateModal(false);
      setNewRole({ name: '', display_name: '' });
      fetchRoles();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create role');
    } finally {
      setCreating(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRole) return;
    setEditError('');
    setSaving(true);
    try {
      await api.patch(`/api/roles/${editingRole.id}`, editForm);
      setEditingRole(null);
      fetchRoles();
    } catch (err: any) {
      setEditError(err.response?.data?.detail || 'Failed to update role');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (role: Role) => {
    if (!window.confirm(`Delete role "${role.display_name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/roles/${role.id}`);
      fetchRoles();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete role');
    }
  };

  const openEdit = (role: Role) => {
    setEditForm({ name: role.name, display_name: role.display_name });
    setEditingRole(role);
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" /></div>;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Security</p>
          <h1>Roles & Permissions</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={18} />
          Create Custom Role
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Role Name</th>
              <th>Type</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.id} style={{ transition: 'background-color 0.2s' }}>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <ShieldCheck size={18} style={{ color: 'var(--secondary)' }} />
                    {role.display_name}
                  </div>
                </td>
                <td>
                  <span className={`badge ${role.is_system ? 'badge-secondary' : 'badge-indigo'}`}>
                    {role.is_system ? 'System' : 'Custom'}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.5rem 1rem', fontSize: '0.8125rem' }}
                      onClick={() => setSelectedRole({ id: role.id, name: role.display_name })}
                    >
                      <Settings size={14} />
                      Permissions
                    </button>
                    <button className="btn" style={{ background: 'none', color: 'var(--primary)', padding: '0.5rem' }} onClick={() => openEdit(role)} title="Edit Role">
                      <Pencil size={16} />
                    </button>
                    <button className="btn" style={{ background: 'none', color: '#ef4444', padding: '0.5rem' }} onClick={() => handleDelete(role)} title="Delete Role">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedRole && (
        <PermissionModal
          roleId={selectedRole.id}
          roleName={selectedRole.name}
          onClose={() => setSelectedRole(null)}
        />
      )}

      {showCreateModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
        }} onClick={() => setShowCreateModal(false)}>
          <div className="card" style={{ width: '440px', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Create Custom Role</h2>
              <button className="btn btn-ghost" onClick={() => setShowCreateModal(false)} style={{ padding: '0.375rem' }}><X size={20} /></button>
            </div>
            {createError && <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>{createError}</div>}
            <form onSubmit={handleCreate}>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Role Name <span style={{ color: 'var(--danger)' }}>*</span></label>
                <input className="form-control" required placeholder="e.g. compliance_manager" value={newRole.name} onChange={(e) => setNewRole({ ...newRole, name: e.target.value })} />
              </div>
              <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Display Name <span style={{ color: 'var(--danger)' }}>*</span></label>
                <input className="form-control" required placeholder="e.g. Compliance Manager" value={newRole.display_name} onChange={(e) => setNewRole({ ...newRole, display_name: e.target.value })} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.75rem' }} disabled={creating}>
                {creating ? <Loader2 size={18} className="animate-spin" /> : 'Create Role'}
              </button>
            </form>
          </div>
        </div>
      )}

      {editingRole && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
        }} onClick={() => setEditingRole(null)}>
          <div className="card" style={{ width: '440px', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Edit Role</h2>
              <button className="btn btn-ghost" onClick={() => setEditingRole(null)} style={{ padding: '0.375rem' }}><X size={20} /></button>
            </div>
            {editError && <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>{editError}</div>}
            <form onSubmit={handleEdit}>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Role Name</label>
                <input className="form-control" required placeholder="e.g. compliance_manager" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
              </div>
              <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.875rem', fontWeight: 500 }}>Display Name</label>
                <input className="form-control" required placeholder="e.g. Compliance Manager" value={editForm.display_name} onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.75rem' }} disabled={saving}>
                {saving ? <Loader2 size={18} className="animate-spin" /> : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleList;