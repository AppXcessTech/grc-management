import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, Upload, FileCheck } from 'lucide-react';
import api from '../../services/api';

const PolicyCreate = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('information_security');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('description', description);
      formData.append('category', category);
      if (file) {
        formData.append('file', file);
      }

      await api.post('/api/policies/', formData);
      navigate('/policies');
    } catch (error: any) {
      console.error('Failed to create policy', error.response?.data || error);
      alert('Failed to create policy: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <button 
          onClick={() => navigate('/policies')} 
          style={{ background: 'none', border: 'none', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', padding: 0, marginBottom: '1rem', fontWeight: 600 }}
        >
          <ArrowLeft size={18} />
          Back to Policies
        </button>
        <h1>Create Security Policy</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>Draft and upload a new security policy for your organization.</p>
      </div>

      <div className="card" style={{ maxWidth: '800px' }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Policy Name</label>
            <input 
              type="text" 
              className="form-control"
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              required 
              placeholder="e.g. Information Security Policy"
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Category</label>
            <select 
              className="form-control"
              value={category} 
              onChange={(e) => setCategory(e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="information_security">Information Security</option>
              <option value="access_control">Access Control</option>
              <option value="incident_response">Incident Response</option>
              <option value="data_retention">Data Retention</option>
              <option value="vendor_security">Vendor Security</option>
              <option value="change_management">Change Management</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Description</label>
            <textarea 
              className="form-control"
              value={description} 
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Briefly describe the purpose and scope of this policy..."
              style={{ width: '100%', minHeight: '120px' }}
            />
          </div>

          <div style={{ marginBottom: '2.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>Policy Document (Optional)</label>
            <div style={{ 
              border: '2px dashed var(--border)', 
              borderRadius: 'var(--radius)', 
              padding: '2rem', 
              textAlign: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.01)',
              transition: 'all 0.2s'
            }}>
              <input 
                type="file" 
                id="file-upload"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                accept=".pdf,.doc,.docx"
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'rgba(14, 165, 233, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                  {file ? <FileCheck size={24} /> : <Upload size={24} />}
                </div>
                <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                  {file ? file.name : 'Click to upload or drag and drop'}
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                  PDF, DOC, DOCX up to 10MB
                </div>
              </label>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', paddingTop: '2rem', borderTop: '1px solid var(--border)' }}>
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={loading}
              style={{ minWidth: '140px' }}
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : 'Create Policy'}
            </button>
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={() => navigate('/policies')}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PolicyCreate;
