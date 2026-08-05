import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Calendar, Mail, Briefcase, Building2, UserCog, UserCheck, Archive, Trash2, RotateCcw, ShieldCheck } from 'lucide-react';
import api from '../../services/api';
import PeopleFormModal from '../../components/PeopleFormModal';
import { useAuth } from '../../context/AuthContext';

interface PeopleAsset {
  id: number;
  name: string;
  email: string | null;
  asset_type: string;
  department: string | null;
  job_title: string | null;
  manager: string | null;
  asset_owner: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  last_access_review: string | null;
  last_reviewed_by: number | null;
}

const PeopleDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.roles?.some(r => r === 'super_admin' || r === 'compliance_admin');
  const isSuperAdmin = user?.roles?.some(r => r === 'super_admin');

  const [item, setItem] = useState<PeopleAsset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);

  const fetchItem = async () => {
    try {
      const response = await api.get(`/api/people-assets/${id}`);
      setItem(response.data);
    } catch {
      setError('People asset not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItem();
  }, [id]);

  const handleArchive = async () => {
    if (!window.confirm('Archive this people asset?')) return;
    try {
      await api.post(`/api/people-assets/${id}/archive`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to archive');
    }
  };

  const handleRestore = async () => {
    try {
      await api.post(`/api/people-assets/${id}/restore`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore');
    }
  };

  const handleReview = async () => {
    if (!window.confirm('Record an access review for this person?')) return;
    try {
      await api.post(`/api/people-assets/${id}/review`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record review');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Permanently delete this people asset? This cannot be undone.')) return;
    try {
      await api.delete(`/api/people-assets/${id}`);
      navigate('/assets/people');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete');
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" size={48} color="var(--primary)" /></div>;
  }

  if (error || !item) {
    return (
      <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>Not Found</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{error || 'People asset not found'}</p>
        <button className="btn btn-outline" onClick={() => navigate('/assets/people')}>Back to People Assets</button>
      </div>
    );
  }

  const InfoRow = ({ label, value }: { label: string; value: string | null | undefined }) => (
    <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0.625rem 0' }}>
      <span style={{ width: '180px', flexShrink: 0, color: 'var(--text-muted)', fontSize: '0.8125rem' }}>{label}</span>
      <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{value || '-'}</span>
    </div>
  );

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/people')} style={{ padding: '0.25rem' }}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People Asset</p>
            <h1 style={{ margin: 0 }}>{item.name}</h1>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-outline" onClick={() => setShowEditModal(true)}><UserCheck size={16} /> Edit</button>
          {item.archived_at ? (
            <button className="btn btn-outline" onClick={handleRestore}><RotateCcw size={16} /> Restore</button>
          ) : (
            <button className="btn btn-outline" onClick={handleArchive}><Archive size={16} /> Archive</button>
          )}
          {isSuperAdmin && (
            <button className="btn btn-outline" style={{ color: '#059669', borderColor: '#059669' }} onClick={handleReview}><ShieldCheck size={16} /> Record Review</button>
          )}
          {isAdmin && (
            <button className="btn btn-outline" style={{ color: '#ef4444', borderColor: '#ef4444' }} onClick={handleDelete}><Trash2 size={16} /> Delete</button>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <UserCog size={18} /> Basic Information
          </h3>
          <InfoRow label="Name" value={item.name} />
          <InfoRow label="Asset Type" value={item.asset_type} />
          <InfoRow label="Status" value={item.archived_at ? 'Archived' : item.status} />
          <InfoRow label="Description" value={item.description} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Mail size={18} /> Contact Information
          </h3>
          <InfoRow label="Email" value={item.email} />
          <InfoRow label="Start Date" value={item.start_date ? new Date(item.start_date).toLocaleDateString() : null} />
          <InfoRow label="End Date" value={item.end_date ? new Date(item.end_date).toLocaleDateString() : null} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Building2 size={18} /> Organizational Information
          </h3>
          <InfoRow label="Department" value={item.department} />
          <InfoRow label="Job Title" value={item.job_title} />
          <InfoRow label="Asset Owner" value={item.asset_owner} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} /> Audit Trail
          </h3>
          <InfoRow label="Created" value={item.created_at ? new Date(item.created_at).toLocaleString() : null} />
          <InfoRow label="Last Updated" value={item.updated_at ? new Date(item.updated_at).toLocaleString() : null} />
          <InfoRow label="Last Access Review" value={item.last_access_review ? new Date(item.last_access_review).toLocaleString() : 'Never reviewed'} />
          <InfoRow label="Archived At" value={item.archived_at ? new Date(item.archived_at).toLocaleString() : 'Not archived'} />
        </div>
      </div>

      {item.description && (
        <div className="card" style={{ padding: '1.25rem', marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Notes</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{item.description}</p>
        </div>
      )}

      {showEditModal && (
        <PeopleFormModal
          asset={item}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => { setShowEditModal(false); fetchItem(); }}
        />
      )}
    </div>
  );
};

export default PeopleDetail;
