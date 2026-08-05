import React, { useState, useEffect } from 'react';
import { X, Loader2, User as UserIcon, Save } from 'lucide-react';
import api from '../services/api';

interface Role {
  id: number;
  name: string;
  display_name: string;
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
  created_at: string;
  roles: Role[];
}

interface UserProfileModalProps {
  userId: number;
  onClose: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

const UserProfileModal: React.FC<UserProfileModalProps> = ({ userId, onClose, onUpdate, onDelete }) => {
  const [user, setUser] = useState<User | null>(null);
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({ 
    first_name: '', 
    last_name: '', 
    status: '',
    role_ids: [] as number[]
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userRes, rolesRes] = await Promise.all([
          api.get(`/api/users/${userId}`),
          api.get('/api/roles/')
        ]);
        setUser(userRes.data);
        setAllRoles(rolesRes.data);
        setFormData({
          first_name: userRes.data.first_name,
          last_name: userRes.data.last_name,
          status: userRes.data.status,
          role_ids: userRes.data.roles.map((r: any) => r.id)
        });
      } catch (err) {
        console.error('Failed to fetch data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [userId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      // Update basic profile
      await api.patch(`/api/users/${userId}`, {
        first_name: formData.first_name,
        last_name: formData.last_name,
        status: formData.status
      });

      // Sync roles
      await api.post('/api/users/sync-roles', {
        user_id: userId,
        role_ids: formData.role_ids
      });

      setIsEditing(false);
      onUpdate();
      
      // Refresh local user data
      const response = await api.get(`/api/users/${userId}`);
      setUser(response.data);
      alert('User profile and roles updated successfully');
    } catch (err) {
      console.error('Update failed', err);
      alert('Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  const toggleRole = (roleId: number) => {
    setFormData(prev => ({
      ...prev,
      role_ids: prev.role_ids.includes(roleId)
        ? prev.role_ids.filter(id => id !== roleId)
        : [...prev.role_ids, roleId]
    }));
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await api.delete(`/api/users/${userId}`);
        onDelete();
      } catch (err) {
        console.error('Delete failed', err);
      }
    }
  };

  if (loading) return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000 }}>
      <Loader2 className="animate-spin" color="white" size={48} />
    </div>
  );

  return (
    <div style={{
      position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
      backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)', zIndex: 1000
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '600px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2rem', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ margin: 0 }}>User Profile</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X /></button>
        </div>

        <div style={{ padding: '2rem', overflowY: 'auto', flex: 1 }}>
          {user && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2rem' }}>
                <UserIcon size={40} color="var(--secondary)" />
              </div>
              
              {!isEditing ? (
                <>
                  <h3 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0 0 0.5rem', color: 'var(--text-main)' }}>{user.first_name} {user.last_name}</h3>
                  <p style={{ color: 'var(--text-muted)', margin: '0 0 1.5rem', fontSize: '1.125rem' }}>{user.email}</p>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '2.5rem' }}>
                    <span className={`badge ${user.status === 'active' ? 'badge-success' : 'badge-warning'}`}>{user.status}</span>
                    {user.roles.map(role => (
                      <span key={role.id} className="badge badge-indigo">{role.display_name}</span>
                    ))}
                    {user.roles.length === 0 && <span className="badge badge-secondary">No Roles Assigned</span>}
                  </div>
                </>
              ) : (
                <form onSubmit={handleUpdate} style={{ textAlign: 'left' }}>
                  <div style={{ display: 'flex', gap: '1.25rem', marginBottom: '1.25rem' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>First Name</label>
                      <input 
                        className="form-control" 
                        style={{ width: '100%' }} 
                        value={formData.first_name} 
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})} 
                        required
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Last Name</label>
                      <input 
                        className="form-control" 
                        style={{ width: '100%' }} 
                        value={formData.last_name} 
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})} 
                        required
                      />
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Status</label>
                    <select 
                      className="form-control" 
                      style={{ width: '100%' }} 
                      value={formData.status} 
                      onChange={(e) => setFormData({...formData, status: e.target.value})}
                    >
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                      <option value="deactivated">Deactivated</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: '2rem' }}>
                    <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>Assigned Roles</label>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      {allRoles.map(role => (
                        <label key={role.id} style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '12px', 
                          cursor: 'pointer', 
                          padding: '0.875rem 1rem', 
                          border: '1px solid var(--border)', 
                          borderRadius: '8px', 
                          backgroundColor: formData.role_ids.includes(role.id) ? 'rgba(14, 165, 233, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                          borderColor: formData.role_ids.includes(role.id) ? 'var(--primary)' : 'var(--border)',
                          transition: 'all 0.2s'
                        }}>
                          <input 
                            type="checkbox" 
                            checked={formData.role_ids.includes(role.id)}
                            onChange={() => toggleRole(role.id)}
                            style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                          />
                          <span style={{ fontSize: '0.9375rem', color: formData.role_ids.includes(role.id) ? 'var(--text-main)' : 'var(--text-muted)' }}>{role.display_name}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', marginTop: '2.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
                    <button type="submit" className="btn btn-primary" style={{ flex: 2 }} disabled={saving}>
                      {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                      Save Changes
                    </button>
                    <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setIsEditing(false)} disabled={saving}>
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>

        {!isEditing && (
          <div style={{ padding: '2rem', borderTop: '1px solid var(--border)', display: 'flex', gap: '1rem', backgroundColor: 'rgba(0,0,0,0.1)' }}>
            <button className="btn btn-primary" style={{ flex: 2 }} onClick={() => setIsEditing(true)}>Update Profile & Roles</button>
            <button className="btn" style={{ flex: 1, backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', border: '1px solid rgba(239, 68, 68, 0.2)' }} onClick={handleDelete}>Delete User</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfileModal;
