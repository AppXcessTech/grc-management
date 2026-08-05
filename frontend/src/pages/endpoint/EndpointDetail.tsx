import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Calendar, Monitor, HardDrive, User, Building2, Archive, Trash2, RotateCcw, Wrench, Smartphone, Shield } from 'lucide-react';
import api from '../../services/api';

interface EndpointDevice {
  id: number;
  name: string;
  asset_type: string;
  status: string;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  assigned_to: number | null;
  assigned_to_name: string | null;
  department: string | null;
  acquisition_date: string | null;
  mdm_device_id: string | null;
  mdm_payload: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

interface MdmDetails {
  device_name: string;
  manufacturer: string;
  model: string;
  os_version: string;
  platform_type: string;
  serial_number: string;
  udid: string;
  device_id: string;
  owned_by: string;
  user_id: string;
  is_supervised: boolean;
  is_removed: string;
  last_contact_time: string;
  battery_level: string;
  registered_time: string;
  added_time: string;
}

const EndpointDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [item, setItem] = useState<EndpointDevice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [mdmDetails, setMdmDetails] = useState<MdmDetails | null>(null);
  const [mdmLoading, setMdmLoading] = useState(false);

  const fetchItem = async () => {
    try {
      const response = await api.get(`/api/endpoint-devices/${id}`);
      setItem(response.data);
    } catch {
      setError('Endpoint device not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItem();
  }, [id]);

  const mdmPayload = item?.mdm_payload ? JSON.parse(item.mdm_payload) : null;

  const fetchMdmDetails = async () => {
    if (!item?.mdm_device_id) return;
    setMdmLoading(true);
    try {
      const res = await api.get(`/api/integrations/manageengine-mdm/devices/${item.mdm_device_id}`);
      setMdmDetails(res.data);
    } catch (err: any) {
      setMdmDetails(null);
      alert(err?.response?.data?.detail || 'Failed to fetch MDM details');
    } finally {
      setMdmLoading(false);
    }
  };

  const updateLifecycle = async () => {
    if (!item?.mdm_device_id) return;
    try {
      const res = await api.post(`/api/integrations/manageengine-mdm/devices/${item.mdm_device_id}/update-lifecycle`);
      fetchItem();
      alert(res.data.message);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update lifecycle');
    }
  };

  const handleArchive = async () => {
    if (!window.confirm('Archive this endpoint device?')) return;
    try {
      await api.post(`/api/endpoint-devices/${id}/archive`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to archive');
    }
  };

  const handleRestore = async () => {
    try {
      await api.post(`/api/endpoint-devices/${id}/restore`);
      fetchItem();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Permanently delete this endpoint device? This cannot be undone.')) return;
    try {
      await api.delete(`/api/endpoint-devices/${id}`);
      navigate('/assets/devices');
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
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{error || 'Endpoint device not found'}</p>
        <button className="btn btn-outline" onClick={() => navigate('/assets/devices')}>Back to Endpoint Devices</button>
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
          <button className="btn btn-ghost" onClick={() => navigate('/assets/devices')} style={{ padding: '0.25rem' }}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Endpoint Device</p>
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
            <Monitor size={18} /> Basic Information
          </h3>
          <InfoRow label="Asset Name" value={item.name} />
          <InfoRow label="Asset Type" value={item.asset_type} />
          <InfoRow label="Status" value={item.archived_at ? 'Archived' : item.status} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <HardDrive size={18} /> Device Information
          </h3>
          <InfoRow label="Manufacturer" value={item.manufacturer} />
          <InfoRow label="Model" value={item.model} />
          <InfoRow label="Serial Number" value={item.serial_number} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <User size={18} /> Ownership
          </h3>
          <InfoRow label="Assigned To" value={item.assigned_to_name || (mdmPayload?.owned_by) || null} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Building2 size={18} /> Organizational Information
          </h3>
          <InfoRow label="Department" value={item.department} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} /> Lifecycle Information
            {item.mdm_device_id && (
              <button className="btn btn-ghost" style={{ marginLeft: 'auto', fontSize: '0.75rem', padding: '0.25rem 0.5rem' }} onClick={updateLifecycle}>
                Fetch from MDM
              </button>
            )}
          </h3>
          <InfoRow label="Acquisition Date" value={item.acquisition_date ? new Date(item.acquisition_date).toLocaleDateString() : null} />
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} /> Audit Trail
          </h3>
          <InfoRow label="Created" value={item.created_at ? new Date(item.created_at).toLocaleString() : null} />
          <InfoRow label="Last Updated" value={item.updated_at ? new Date(item.updated_at).toLocaleString() : null} />
          <InfoRow label="Archived At" value={item.archived_at ? new Date(item.archived_at).toLocaleString() : 'Not archived'} />
        </div>

        {item.mdm_device_id && (
          <div className="card" style={{ padding: '1.25rem', gridColumn: '1 / -1' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Smartphone size={18} /> MDM Details
              <button className="btn btn-ghost" style={{ marginLeft: 'auto', fontSize: '0.75rem', padding: '0.25rem 0.5rem' }} onClick={fetchMdmDetails} disabled={mdmLoading}>
                {mdmLoading ? <Loader2 size={14} className="animate-spin" /> : null} Fetch from MDM
              </button>
            </h3>

            {mdmDetails ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
                <InfoRow label="Device Name" value={mdmDetails.device_name} />
                <InfoRow label="Manufacturer" value={mdmDetails.manufacturer} />
                <InfoRow label="Model" value={mdmDetails.model} />
                <InfoRow label="Platform" value={mdmDetails.platform_type} />
                <InfoRow label="OS Version" value={mdmDetails.os_version} />
                <InfoRow label="Serial Number" value={mdmDetails.serial_number} />
                <InfoRow label="UDID" value={mdmDetails.udid} />
                <InfoRow label="Device ID" value={mdmDetails.device_id} />
                <InfoRow label="Owned By" value={mdmDetails.owned_by} />
                <InfoRow label="User ID" value={mdmDetails.user_id} />
                <InfoRow label="Battery" value={mdmDetails.battery_level ? `${mdmDetails.battery_level}%` : null} />
                <InfoRow label="Supervised" value={mdmDetails.is_supervised ? 'Yes' : 'No'} />
                <InfoRow label="Removed" value={mdmDetails.is_removed} />
                <InfoRow label="Last Contact" value={mdmDetails.last_contact_time ? new Date(Number(mdmDetails.last_contact_time)).toLocaleString() : null} />
                <InfoRow label="Registered" value={mdmDetails.registered_time ? new Date(Number(mdmDetails.registered_time)).toLocaleString() : null} />
              </div>
            ) : mdmPayload ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
                <InfoRow label="Device Name" value={mdmPayload.device_name} />
                <InfoRow label="Model" value={mdmPayload.model} />
                <InfoRow label="Platform" value={mdmPayload.platform_type} />
                <InfoRow label="OS Version" value={mdmPayload.os_version} />
                <InfoRow label="Serial Number" value={mdmPayload.serial_number} />
                <InfoRow label="UDID" value={mdmPayload.udid} />
                <InfoRow label="Device ID" value={mdmPayload.device_id} />
                <InfoRow label="Owned By" value={mdmPayload.owned_by} />
                <InfoRow label="User ID" value={mdmPayload.user_id} />
                <InfoRow label="Customer ID" value={mdmPayload.customer_id} />
                <InfoRow label="Supervised" value={mdmPayload.is_supervised ? 'Yes' : 'No'} />
                <InfoRow label="Removed" value={mdmPayload.is_removed} />
                <InfoRow label="Last Contact" value={mdmPayload.last_contact_time ? new Date(Number(mdmPayload.last_contact_time)).toLocaleString() : null} />
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>No cached MDM data. Click "Fetch from MDM" to get live details.</p>
            )}
          </div>
        )}
      </div>

      {showEditModal && (
        <EndpointFormModal
          asset={item}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => { setShowEditModal(false); fetchItem(); }}
        />
      )}
    </div>
  );
};

export default EndpointDetail;
