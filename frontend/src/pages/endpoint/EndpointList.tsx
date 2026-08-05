import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Loader2, Search, Eye, Archive, Trash2, RotateCcw } from 'lucide-react';
import api from '../../services/api';
import EndpointFormModal from '../../components/EndpointFormModal';

const DEVICE_TYPES = [
  'Windows Laptop', 'macOS Laptop', 'Linux Workstation', 'Desktop Computer',
  'iPhone', 'Android Phone', 'Tablet', 'Rugged Device',
  'Kiosk', 'Point-of-Sale System', 'Meeting Room System', 'Executive Device',
];

interface EndpointDevice {
  id: number;
  name: string;
  asset_type: string;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  assigned_to: number | null;
  assigned_to_name: string | null;
  department: string | null;
  status: string;
  acquisition_date: string | null;
  mdm_device_id: string | null;
  mdm_payload: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

const EndpointList = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<EndpointDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<EndpointDevice | null>(null);

  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [includeArchived, setIncludeArchived] = useState(false);

  const [departments, setDepartments] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const pageSize = 20;

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: any = { page, page_size: pageSize, sort_by: 'name', sort_order: 'asc' };
      if (search) params.search = search;
      if (filterType) params.asset_type = filterType;
      if (filterDepartment) params.department = filterDepartment;
      if (filterStatus) params.status = filterStatus;
      if (includeArchived) params.include_archived = true;

      const response = await api.get('/api/endpoint-devices/', { params });
      setItems(response.data);
      setHasMore(response.data.length >= pageSize);
    } catch {
      setError('Failed to load endpoint devices');
    } finally {
      setLoading(false);
    }
  }, [search, filterType, filterDepartment, filterStatus, includeArchived, page]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  useEffect(() => {
    api.get('/api/endpoint-devices/departments').then(r => setDepartments(r.data)).catch(() => {});
  }, []);

  const handleArchive = async (id: number) => {
    if (!window.confirm('Archive this endpoint device?')) return;
    try {
      await api.post(`/api/endpoint-devices/${id}/archive`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to archive');
    }
  };

  const handleRestore = async (id: number) => {
    try {
      await api.post(`/api/endpoint-devices/${id}/restore`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Permanently delete this endpoint device? This cannot be undone.')) return;
    try {
      await api.delete(`/api/endpoint-devices/${id}`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const openEdit = (asset: EndpointDevice) => {
    setEditingAsset(asset);
    setShowFormModal(true);
  };

  const clearFilters = () => {
    setSearch('');
    setFilterType('');
    setFilterDepartment('');
    setFilterStatus('');
    setPage(1);
  };

  const hasFilters = search || filterType || filterDepartment || filterStatus;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Endpoint Devices</p>
          <h1>All Endpoint Devices</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-primary" onClick={() => navigate('/assets/devices/new')}>
            <Plus size={18} /> Add Device
          </button>
          <button className="btn btn-outline" onClick={() => navigate('/assets/devices/integrations')}>
            <i className="ti ti-plug-connected"></i> Integrations
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: '1 1 200px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.625rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input className="form-control" style={{ paddingLeft: '2rem' }} placeholder="Search devices..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select className="form-control" style={{ width: 'auto', minWidth: '140px' }} value={filterType} onChange={e => { setFilterType(e.target.value); setPage(1); }}>
            <option value="">All Types</option>
            {DEVICE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '140px' }} value={filterDepartment} onChange={e => { setFilterDepartment(e.target.value); setPage(1); }}>
            <option value="">All Departments</option>
            {departments.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '120px' }} value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
            <option value="Archived">Archived</option>
          </select>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
            <input type="checkbox" checked={includeArchived} onChange={e => { setIncludeArchived(e.target.checked); setPage(1); }} />
            Include Archived
          </label>
          {hasFilters && (
            <button className="btn btn-ghost" style={{ fontSize: '0.8125rem' }} onClick={clearFilters}>Clear</button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" size={48} color="var(--primary)" /></div>
      ) : items.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>No endpoint devices found.</p>
          {!hasFilters && (
            <button className="btn btn-primary" onClick={() => navigate('/assets/devices/new')}>
              <Plus size={18} /> Add Your First Device
            </button>
          )}
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset Name</th>
                  <th>Asset Type</th>
                  <th>Manufacturer</th>
                  <th>Assigned To</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th style={{ width: '120px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/assets/devices/${item.id}`)}>
                    <td style={{ fontWeight: 500 }}>{item.name}</td>
                    <td>{item.asset_type}</td>
                    <td>{item.manufacturer || '-'}</td>
                    <td>{item.assigned_to_name || (item.mdm_payload ? JSON.parse(item.mdm_payload).owned_by : null) || '-'}</td>
                    <td>{item.department || '-'}</td>
                    <td>
                      <span className={`badge ${item.archived_at ? 'badge-secondary' : item.status === 'Active' ? 'badge-success' : 'badge-warning'}`}>
                        {item.archived_at ? 'Archived' : item.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem' }} onClick={e => e.stopPropagation()}>
                        <button className="btn btn-ghost" style={{ padding: '0.25rem' }} title="View" onClick={() => navigate(`/assets/devices/${item.id}`)}>
                          <Eye size={16} />
                        </button>
                        <button className="btn btn-ghost" style={{ padding: '0.25rem' }} title="Edit" onClick={() => openEdit(item)}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                        </button>
                        {item.archived_at ? (
                          <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#22c55e' }} title="Restore" onClick={() => handleRestore(item.id)}>
                            <RotateCcw size={16} />
                          </button>
                        ) : (
                          <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#eab308' }} title="Archive" onClick={() => handleArchive(item.id)}>
                            <Archive size={16} />
                          </button>
                        )}
                        <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#ef4444' }} title="Delete" onClick={() => handleDelete(item.id)}>
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {hasMore && !loading && (
        <div style={{ textAlign: 'center', padding: '1rem' }}>
          <button className="btn btn-outline" onClick={() => setPage(p => p + 1)}>Load More</button>
        </div>
      )}

      {showFormModal && (
        <EndpointFormModal
          asset={editingAsset}
          onClose={() => { setShowFormModal(false); setEditingAsset(null); }}
          onSuccess={() => { setShowFormModal(false); setEditingAsset(null); fetchItems(); }}
        />
      )}
    </div>
  );
};

export default EndpointList;
