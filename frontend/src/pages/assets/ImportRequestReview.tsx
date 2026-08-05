import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import api from '../../services/api';

interface ImportRequest {
  id: number;
  role_arn: string;
  account_name: string | null;
  region: string;
  status: string;
  requested_by_name: string | null;
  reviewed_by_name: string | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
}

const ImportRequestReview = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [req, setReq] = useState<ImportRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/api/assets/import-requests/${id}`)
      .then(r => setReq(r.data))
      .catch(() => setError('Failed to load import request'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleAction = async (status: 'approved' | 'rejected') => {
    setActionLoading(true);
    setError('');
    try {
      await api.patch(`/api/assets/import-requests/${id}`, {
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

  if (!req) {
    return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Import request not found</div>;
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out', maxWidth: '720px' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-ghost" onClick={() => navigate('/assets')} style={{ padding: '0.25rem' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Review</p>
          <h1 style={{ margin: 0 }}>AWS Import Request</h1>
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
            <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--text-main)' }}>
              {req.account_name || 'AWS Account'}
            </h2>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Requested by {req.requested_by_name || 'Unknown'} &middot; {new Date(req.created_at).toLocaleString()}
            </p>
          </div>
          <span className={`badge ${
            req.status === 'pending' ? 'badge-warning' :
            req.status === 'approved' ? 'badge-success' : 'badge-danger'
          }`} style={{ fontSize: '0.75rem' }}>
            {req.status}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ gridColumn: '1 / -1' }}>
            <label className="form-label">Role ARN</label>
            <code style={{ display: 'block', marginTop: '0.25rem', padding: '0.625rem', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius)', fontSize: '0.8125rem', wordBreak: 'break-all' }}>
              {req.role_arn}
            </code>
          </div>
          <div>
            <label className="form-label">Region</label>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9375rem', color: 'var(--text-main)' }}>{req.region}</p>
          </div>
          <div>
            <label className="form-label">Account Name</label>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9375rem', color: 'var(--text-main)' }}>{req.account_name || '—'}</p>
          </div>
        </div>

        <div style={{ padding: '0.75rem', backgroundColor: 'rgba(99, 102, 241, 0.05)', borderRadius: 'var(--radius)', border: '1px solid var(--border)', marginBottom: '1.5rem' }}>
          <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            <strong>Note:</strong> Approval will immediately attempt to connect to AWS and import discovered resources (EC2, RDS, S3, Lambda) into this organization's asset inventory.
          </p>
        </div>

        {req.review_notes && (
          <div style={{ marginBottom: '1.5rem', padding: '0.75rem', backgroundColor: 'rgba(99, 102, 241, 0.05)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
            <label className="form-label">Review Notes</label>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: 'var(--text-muted)' }}>{req.review_notes}</p>
          </div>
        )}

        {req.status === 'pending' && (
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
              <button className="btn btn-primary" onClick={() => handleAction('approved')} disabled={actionLoading}>
                {actionLoading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                Approve & Import
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ImportRequestReview;
