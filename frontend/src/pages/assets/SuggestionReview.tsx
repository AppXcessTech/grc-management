import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import api from '../../services/api';

interface Suggestion {
  id: number;
  suggested_data: {
    name: string;
    description?: string;
    category_id: number;
    department?: string;
    criticality: string;
    risk_level: string;
    tags?: Array<{ key: string; value?: string }>;
  };
  status: string;
  suggested_by_name: string | null;
  reviewed_by_name: string | null;
  review_notes: string | null;
  category_name: string | null;
  created_at: string;
  updated_at: string;
}

const getBadgeClass = (level: string) => {
  switch (level.toLowerCase()) {
    case 'critical': return 'badge-danger';
    case 'high': return 'badge-warning';
    case 'medium': return 'badge-indigo';
    case 'low': return 'badge-success';
    default: return 'badge-secondary';
  }
};

const SuggestionReview = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/api/assets/suggestions/${id}`)
      .then(r => setSuggestion(r.data))
      .catch(() => setError('Failed to load suggestion'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleAction = async (status: 'approved' | 'rejected') => {
    setActionLoading(true);
    setError('');
    try {
      await api.patch(`/api/assets/suggestions/${id}`, {
        status,
        review_notes: reviewNotes || undefined,
      });
      navigate('/assets');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} color="var(--primary)" />
      </div>
    );
  }

  if (!suggestion) {
    return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Suggestion not found</div>;
  }

  const data = suggestion.suggested_data;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out', maxWidth: '720px' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/assets')} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Review</p>
          <h1 style={{ margin: 0 }}>Asset Suggestion</h1>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1rem', marginTop: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      <div className="card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--text-main)' }}>{data.name}</h2>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Suggested by {suggestion.suggested_by_name || 'Unknown'} &middot; {new Date(suggestion.created_at).toLocaleString()}
            </p>
          </div>
          <span className={`badge ${
            suggestion.status === 'pending' ? 'badge-warning' :
            suggestion.status === 'approved' ? 'badge-success' : 'badge-danger'
          }`} style={{ fontSize: '0.75rem' }}>
            {suggestion.status}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
          <div>
            <label className="form-label">Category</label>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9375rem', color: 'var(--text-main)' }}>{suggestion.category_name || data.category_id}</p>
          </div>
          {data.department && (
            <div>
              <label className="form-label">Department</label>
              <p style={{ margin: '0.25rem 0 0', fontSize: '0.9375rem', color: 'var(--text-main)' }}>{data.department}</p>
            </div>
          )}
          <div>
            <label className="form-label">Criticality</label>
            <p style={{ margin: '0.25rem 0 0' }}>
              <span className={`badge ${getBadgeClass(data.criticality)}`}>{data.criticality}</span>
            </p>
          </div>
          <div>
            <label className="form-label">Risk Level</label>
            <p style={{ margin: '0.25rem 0 0' }}>
              <span className={`badge ${getBadgeClass(data.risk_level)}`}>{data.risk_level}</span>
            </p>
          </div>
        </div>

        {data.description && (
          <div style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">Description</label>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{data.description}</p>
          </div>
        )}

        {data.tags && data.tags.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">Tags</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginTop: '0.25rem' }}>
              {data.tags.map((t, i) => (
                <span key={i} className="badge badge-secondary">{t.key}{t.value ? `: ${t.value}` : ''}</span>
              ))}
            </div>
          </div>
        )}

        {suggestion.review_notes && (
          <div style={{ marginBottom: '1.5rem', padding: '0.75rem', backgroundColor: 'rgba(99, 102, 241, 0.05)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
            <label className="form-label">Review Notes</label>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: 'var(--text-muted)' }}>{suggestion.review_notes}</p>
          </div>
        )}

        {suggestion.status === 'pending' && (
          <>
            <div style={{ marginBottom: '1.25rem' }}>
              <label className="form-label">Review Notes (optional)</label>
              <textarea className="form-control" rows={3} placeholder="Add notes about your decision..." value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} disabled={actionLoading} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button className="btn btn-outline" style={{ color: '#ef4444', borderColor: '#ef4444' }} onClick={() => handleAction('rejected')} disabled={actionLoading}>
                {actionLoading ? <Loader2 size={16} className="animate-spin" /> : <XCircle size={16} />}
                Reject
              </button>
              <button className="btn btn-primary" style={{ backgroundColor: 'var(--success)', borderColor: 'var(--success)' }} onClick={() => handleAction('approved')} disabled={actionLoading}>
                {actionLoading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                Approve & Create Asset
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SuggestionReview;
