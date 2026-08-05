import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';

const PolicyDetail = () => {
  const { policyId } = useParams<{ policyId: string }>();
  const navigate = useNavigate();
  const [policy, setPolicy] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', description: '', category: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [policyId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const policyRes = await api.get(`/api/policies/${policyId}`);
      setPolicy(policyRes.data);
      setEditForm({
        name: policyRes.data.name,
        description: policyRes.data.description || '',
        category: policyRes.data.category
      });
      
      const versionsRes = await api.get(`/api/policies/${policyId}/versions`);
      setVersions(versionsRes.data);
    } catch (error) {
      console.error('Failed to fetch policy details', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.patch(`/api/policies/${policyId}`, editForm);
      setIsEditing(false);
      fetchData();
    } catch (error) {
      console.error('Failed to update policy', error);
      alert('Failed to update policy');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this policy? This action cannot be undone.')) {
      return;
    }
    try {
      await api.delete(`/api/policies/${policyId}`);
      navigate('/policies');
    } catch (error) {
      console.error('Failed to delete policy', error);
      alert('Failed to delete policy');
    }
  };

  const handlePublish = async (versionId: number) => {
    try {
      await api.post(`/api/policies/versions/${versionId}/publish`);
      fetchData();
    } catch (error) {
      console.error('Failed to publish', error);
    }
  };

  const handleAcknowledge = async (versionId: number) => {
    try {
      await api.post(`/api/policies/versions/${versionId}/acknowledge`);
      alert('Acknowledged successfully');
    } catch (error) {
      console.error('Failed to acknowledge', error);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!policy) return <div>Policy not found</div>;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          {isEditing ? (
            <form onSubmit={handleUpdate}>
              <div style={{ marginBottom: '10px' }}>
                <input 
                  type="text" 
                  value={editForm.name} 
                  onChange={e => setEditForm({...editForm, name: e.target.value})}
                  required
                  style={{ fontSize: '1.5em', fontWeight: 'bold', width: '100%', padding: '5px' }}
                />
              </div>
              <div style={{ marginBottom: '10px' }}>
                <select 
                  value={editForm.category} 
                  onChange={e => setEditForm({...editForm, category: e.target.value})}
                  style={{ padding: '5px', width: '100%' }}
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
              <div style={{ marginBottom: '10px' }}>
                <textarea 
                  value={editForm.description} 
                  onChange={e => setEditForm({...editForm, description: e.target.value})}
                  style={{ width: '100%', minHeight: '100px', padding: '5px' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="btn-primary">Save Changes</button>
                <button type="button" className="btn-secondary" onClick={() => setIsEditing(false)}>Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <h1>{policy.name}</h1>
              <div style={{ marginBottom: '10px' }}>
                <span className="badge" style={{ backgroundColor: '#e0e0e0', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8em' }}>
                  {policy.category.replace(/_/g, ' ')}
                </span>
                <span className="badge" style={{ marginLeft: '10px', backgroundColor: policy.status === 'published' ? '#d4edda' : '#fff3cd', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8em' }}>
                  {policy.status}
                </span>
              </div>
              <p>{policy.description}</p>
            </>
          )}
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {!isEditing && (
            <button onClick={() => setIsEditing(true)} className="btn-secondary">Edit</button>
          )}
          <button onClick={handleDelete} className="btn-danger" style={{ backgroundColor: '#ff4d4f', color: 'white', border: 'none', padding: '5px 15px', borderRadius: '4px', cursor: 'pointer' }}>
            Delete
          </button>
        </div>
      </div>
      
      <hr style={{ margin: '20px 0' }} />

      <h3>Versions</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #ddd', textAlign: 'left' }}>
            <th style={{ padding: '10px' }}>No.</th>
            <th style={{ padding: '10px' }}>Notes</th>
            <th style={{ padding: '10px' }}>Status</th>
            <th style={{ padding: '10px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {versions.length === 0 ? (
            <tr><td colSpan={4} style={{ padding: '10px', textAlign: 'center' }}>No versions available</td></tr>
          ) : (
            versions.map(v => (
              <tr key={v.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '10px' }}>v{v.version_number}</td>
                <td style={{ padding: '10px' }}>{v.notes || 'No notes'}</td>
                <td style={{ padding: '10px' }}>{v.published_at ? 'Published' : 'Draft'}</td>
                <td style={{ padding: '10px' }}>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {!v.published_at && (
                      <button onClick={() => handlePublish(v.id)} className="btn-primary" style={{ fontSize: '0.8em' }}>Publish</button>
                    )}
                    {v.published_at && (
                      <button onClick={() => handleAcknowledge(v.id)} className="btn-secondary" style={{ fontSize: '0.8em' }}>Acknowledge</button>
                    )}
                    {v.file_path && (
                      <a href={`/api/policies/versions/${v.id}/download`} target="_blank" rel="noreferrer" style={{ fontSize: '0.8em', alignSelf: 'center' }}>Download</a>
                    )}
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default PolicyDetail;
