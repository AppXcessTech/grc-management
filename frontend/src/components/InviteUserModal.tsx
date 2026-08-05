import React, { useState, useEffect } from 'react';
import { X, Loader2, Copy, Check } from 'lucide-react';
import api from '../services/api';

interface InviteUserModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

interface Role {
  id: number;
  name: string;
  display_name: string;
}

interface CreatedUser {
  email: string;
  first_name: string;
  last_name: string;
  generated_password: string;
}

const InviteUserModal: React.FC<InviteUserModalProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    organization_id: ''
  });
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingData, setFetchingData] = useState(true);
  const [error, setError] = useState('');
  const [createdUser, setCreatedUser] = useState<CreatedUser | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [orgsRes, rolesRes] = await Promise.all([
          api.get('/api/organizations/'),
          api.get('/api/roles/'),
        ]);
        setOrganizations(orgsRes.data);
        setRoles(rolesRes.data);
        if (orgsRes.data.length > 0) {
          setFormData(prev => ({ ...prev, organization_id: orgsRes.data[0].id.toString() }));
        }
      } catch (err) {
        console.error('Failed to fetch data', err);
      } finally {
        setFetchingData(false);
      }
    };
    fetchData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/api/users/invite', {
        ...formData,
        organization_id: parseInt(formData.organization_id),
      });
      if (selectedRoleId) {
        await api.post('/api/users/assign-role', {
          user_id: res.data.id,
          role_id: parseInt(selectedRoleId),
        });
      }
      setCreatedUser({
        email: res.data.email,
        first_name: res.data.first_name,
        last_name: res.data.last_name,
        generated_password: res.data.generated_password,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to invite user');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
      backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '500px' }}>
        {!createdUser ? (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2>Invite User</h2>
              <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X /></button>
            </div>

            <form onSubmit={handleSubmit}>
              {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontSize: '0.875rem' }}>{error}</div>}

              <div style={{ display: 'flex', gap: '1.25rem', marginBottom: '1.25rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>First Name</label>
                  <input type="text" required className="form-control" style={{ width: '100%' }} placeholder="John" value={formData.first_name} onChange={(e) => setFormData({...formData, first_name: e.target.value})} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Last Name</label>
                  <input type="text" required className="form-control" style={{ width: '100%' }} placeholder="Doe" value={formData.last_name} onChange={(e) => setFormData({...formData, last_name: e.target.value})} />
                </div>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Email Address</label>
                <input type="email" required className="form-control" style={{ width: '100%' }} placeholder="john.doe@example.com" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Organization</label>
                {fetchingData ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}><Loader2 className="animate-spin" size={18} /><span style={{ fontSize: '0.875rem' }}>Loading...</span></div>
                ) : (
                  <select className="form-control" style={{ width: '100%' }} value={formData.organization_id} onChange={(e) => setFormData({...formData, organization_id: e.target.value})}>
                    {organizations.map(org => <option key={org.id} value={org.id}>{org.name}</option>)}
                  </select>
                )}
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Assign Role</label>
                {fetchingData ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}><Loader2 className="animate-spin" size={18} /><span style={{ fontSize: '0.875rem' }}>Loading...</span></div>
                ) : (
                  <select className="form-control" style={{ width: '100%' }} value={selectedRoleId} onChange={(e) => setSelectedRoleId(e.target.value)}>
                    <option value="">— No role —</option>
                    {roles.map(role => <option key={role.id} value={role.id}>{role.display_name}</option>)}
                  </select>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
                <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading || fetchingData}>
                  {loading ? <Loader2 className="animate-spin" size={18} /> : 'Send Invitation'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ color: '#22c55e' }}>User Created</h2>
              <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X /></button>
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Share these credentials with the user. They can log in immediately.
            </p>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>Email</label>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <code style={{ flex: 1, padding: '0.625rem 0.75rem', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '0.9375rem' }}>{createdUser.email}</code>
                <button className="btn btn-secondary" style={{ padding: '0.5rem' }} onClick={() => handleCopy(createdUser.email)} title="Copy email">
                  {copied ? <Check size={16} color="#22c55e" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>Generated Password</label>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <code style={{ flex: 1, padding: '0.625rem 0.75rem', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '0.9375rem', fontFamily: 'monospace' }}>{createdUser.generated_password}</code>
                <button className="btn btn-secondary" style={{ padding: '0.5rem' }} onClick={() => handleCopy(createdUser.generated_password)} title="Copy password">
                  {copied ? <Check size={16} color="#22c55e" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
              <button type="button" onClick={onClose} className="btn btn-primary">Done</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default InviteUserModal;