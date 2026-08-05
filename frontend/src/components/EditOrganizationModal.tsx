import React, { useState, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';
import api from '../services/api';

interface Organization {
  id: number;
  external_id: string;
  name: string;
  slug: string;
  domain: string;
  size: string;
  industry: string;
}

interface EditOrganizationModalProps {
  org: Organization;
  onClose: () => void;
  onSuccess: () => void;
}

const EditOrganizationModal: React.FC<EditOrganizationModalProps> = ({ org, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: org.name,
    domain: org.domain || '',
    industry: org.industry || '',
    size: org.size
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.patch(`/api/organizations/${org.id}`, formData);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update organization');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
      backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '500px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Edit Organization</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontSize: '0.875rem' }}>{error}</div>}
          
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Organization Name</label>
            <input 
              type="text" required className="form-control" style={{ width: '100%' }}
              value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Domain</label>
            <input 
              type="text" className="form-control" style={{ width: '100%' }}
              value={formData.domain} onChange={(e) => setFormData({...formData, domain: e.target.value})}
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Size</label>
            <select 
              className="form-control" style={{ width: '100%' }}
              value={formData.size} onChange={(e) => setFormData({...formData, size: e.target.value})}
            >
              <option value="startup">Startup</option>
              <option value="SMB">SMB</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" size={18} /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditOrganizationModal;
