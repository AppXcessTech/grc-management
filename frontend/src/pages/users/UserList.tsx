import { useEffect, useState } from 'react';
import { UserPlus, Loader2, Trash2, Eye } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import InviteUserModal from '../../components/InviteUserModal';
import BulkImportModal from '../../components/BulkImportModal';
import UserProfileModal from '../../components/UserProfileModal';

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
  organization_id: number;
  status: string;
  created_at: string;
  roles?: Role[];
}

const UserList = () => {
  const { user: currentUser } = useAuth();
  const isAdmin = currentUser?.roles?.some(r => r === 'super_admin' || r === 'compliance_admin');
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showBulkImportModal, setShowBulkImportModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/users/');
      setUsers(response.data);
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.delete(`/api/users/${id}`);
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  if (loading && users.length === 0) return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" size={48} color="var(--primary)" /></div>;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Administration</p>
          <h1>Users</h1>
        </div>
        {isAdmin && (
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
            <button className="btn btn-secondary" onClick={() => setShowBulkImportModal(true)}>Bulk Import</button>
            <button 
              className="btn btn-primary" 
              onClick={() => setShowInviteModal(true)}
            >
              <UserPlus size={18} />
              Invite User
            </button>
          </div>
        )}
      </div>
      
      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Status</th>
              {isAdmin && <th>Roles</th>}
              <th>Created At</th>
              {isAdmin && <th style={{ textAlign: 'right' }}>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={isAdmin ? 5 : 3} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>{isAdmin ? 'No users found. Click "Invite User" to add team members.' : 'No user data available.'}</td>
              </tr>
            ) : users.map((user) => (
              <tr key={user.id} style={{ transition: 'background-color 0.2s' }}>
                <td>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{user.first_name} {user.last_name}</span>
                    <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{user.email}</span>
                  </div>
                </td>
                <td>
                  <span className={`badge ${user.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                    {user.status}
                  </span>
                </td>
                {isAdmin && (
                  <td>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {user.roles && user.roles.length > 0
                        ? user.roles.map(role => (
                            <span key={role.id} className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>
                              {role.display_name || role.name}
                            </span>
                          ))
                        : <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>—</span>
                      }
                    </div>
                  </td>
                )}
                <td style={{ color: 'var(--text-muted)' }}>{new Date(user.created_at).toLocaleDateString()}</td>
                {isAdmin && (
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                      <button 
                        className="btn" 
                        style={{ background: 'none', color: 'var(--primary)', padding: '0.5rem' }} 
                        onClick={() => setSelectedUserId(user.id)}
                        title="View Profile"
                      >
                        <Eye size={18} />
                      </button>
                      <button 
                        className="btn" 
                        style={{ background: 'none', color: '#ef4444', padding: '0.5rem' }} 
                        onClick={() => handleDeleteUser(user.id)}
                        title="Delete User"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showBulkImportModal && (
        <BulkImportModal
          onClose={() => setShowBulkImportModal(false)}
          onSuccess={fetchUsers}
        />
      )}

      {showInviteModal && (
        <InviteUserModal 
          onClose={() => setShowInviteModal(false)} 
          onSuccess={() => {
            setShowInviteModal(false);
            fetchUsers();
          }} 
        />
      )}

      {selectedUserId && (
        <UserProfileModal 
          userId={selectedUserId} 
          onClose={() => setSelectedUserId(null)} 
          onUpdate={fetchUsers}
          onDelete={() => {
            setSelectedUserId(null);
            fetchUsers();
          }}
        />
      )}
    </div>
  );
};

export default UserList;
