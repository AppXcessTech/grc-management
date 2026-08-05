import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, FileText, Loader2, Eye, Shield } from 'lucide-react';
import api from '../../services/api';

interface Policy {
  id: number;
  name: string;
  description: string;
  category: string;
  status: string;
}

const PolicyList = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPolicies = async () => {
    try {
      const response = await api.get('/api/policies/');
      setPolicies(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load policies.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  if (loading && policies.length === 0) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} color="var(--primary)" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Compliance</p>
          <h1>Security Policies</h1>
        </div>
        <Link 
          to="/policies/create" 
          className="btn btn-primary" 
          style={{ marginBottom: '0.5rem' }}
        >
          <Plus size={18} />
          Create Policy
        </Link>
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
              <th>Policy Name</th>
              <th>Category</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {policies.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  No policies found. Click "Create Policy" to get started.
                </td>
              </tr>
            ) : policies.map((policy) => (
              <tr key={policy.id} style={{ transition: 'background-color 0.2s' }}>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--primary)' }}><Shield size={18} /></div>
                    {policy.name}
                  </div>
                </td>
                <td>
                  <span className="badge badge-indigo" style={{ textTransform: 'capitalize' }}>
                    {policy.category.replace(/_/g, ' ')}
                  </span>
                </td>
                <td>
                  <span className="badge badge-success">Active</span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <Link 
                    to={`/policies/${policy.id}`} 
                    className="btn" 
                    style={{ background: 'none', color: 'var(--primary)', padding: '0.5rem' }}
                    title="View Details"
                  >
                    <Eye size={18} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PolicyList;
