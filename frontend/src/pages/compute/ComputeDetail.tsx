import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Calendar, Server, Cpu, User, Archive, Trash2, RotateCcw, Wrench } from 'lucide-react';
import api from '../../services/api';
import ComputeFormModal from '../../components/ComputeFormModal';

interface ComputeAsset {
  id: number;
  name: string;
  asset_type: string;
  status: string;
  hostname: string | null;
  operating_system: string | null;
  owner_id: number | null;
  owner_name: string | null;
  provisioned_date: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

const ComputeDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [item, setItem] = useState<ComputeAsset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);

  const fetchItem = async () => {
    try {
      const response = await api.get(`/api/compute-assets/${id}`);
      setItem(response.data);
    } catch {
      setError('Compute asset not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItem();
  }, [id]);

  const handleArchive = async () => {
    if (!window.confirm('Archive this compute asset?')) return;
    try {
      await api.post(`/api/compute-assets/${id}/archive`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to archive');
    }
  };

  const handleRestore = async () => {
    try {
      await api.post(`/api/compute-assets/${id}/restore`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Permanently delete this compute asset? This cannot be undone.')) return;
    try {
      await api.delete(`/api/compute-assets/${id}`);
      navigate('/assets/servers');
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
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{error || 'Compute asset not found'}</p>
        <button className="btn btn-outline" onClick={() => navigate('/assets/servers')}>Back to Compute Assets</button>
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
          <button className="btn btn-ghost" onClick={() => navigate('/assets/servers')} style={{ padding: '0.25rem' }}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Compute Asset</p>
            <h1 style={{ margin: 0 }}>{item.name}</h1>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-outline" onClick={() => setShowEditModal(true)}><Wrench size={16} /> Edit</button>
          {item.archived_at ? (
            <button className="btn btn-outline" onClick={handleRestore}><RotateCcw size={16} /> Restore</button>
          ) : (
            <button className="btn btn-outline" onClick={handleArchive}><Archive size={16} /> Archive</button>
          )}
          <button className="btn btn-outline" style={{ color: '#ef4444', borderColor: '#ef4444' }} onClick={handleDelete}><Trash2 size={16} /> Delete</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={18} /> Basic Information
          </h3>
          <InfoRow label="Asset Name" value={item.name} />
          <InfoRow label="Asset Type" value={item.asset_type} />
          <InfoRow label="Status" value={item.archived_at ? 'Archived' : item.status} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={18} /> Identification
          </h3>
          <InfoRow label="Hostname" value={item.hostname} />
          <InfoRow label="Operating System" value={item.operating_system} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <User size={18} /> Ownership
          </h3>
          <InfoRow label="Owner" value={item.owner_name} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} /> Lifecycle Information
          </h3>
          <InfoRow label="Provisioned Date" value={item.provisioned_date ? new Date(item.provisioned_date).toLocaleDateString() : null} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} /> Audit Trail
          </h3>
          <InfoRow label="Created At" value={item.created_at ? new Date(item.created_at).toLocaleString() : null} />
          <InfoRow label="Updated At" value={item.updated_at ? new Date(item.updated_at).toLocaleString() : null} />
          <InfoRow label="Archived At" value={item.archived_at ? new Date(item.archived_at).toLocaleString() : null} />
        </div>
      </div>

      {showEditModal && (
        <ComputeFormModal
          asset={item}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => { setShowEditModal(false); fetchItem(); }}
        />
      )}
    </div>
  );
};

export default ComputeDetail;
