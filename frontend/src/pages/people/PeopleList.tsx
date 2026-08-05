import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Loader2, Search, Eye, Archive, Trash2, UserCheck, RotateCcw } from 'lucide-react';
import api from '../../services/api';
import PeopleFormModal from '../../components/PeopleFormModal';
import { useAuth } from '../../context/AuthContext';

const ASSET_TYPES = [
  'Employee', 'Contractor', 'Consultant', 'Intern',
  'Temporary Staff', 'Third-Party User', 'Vendor User',
  'Service Account', 'Shared Account', 'Privileged Account',
  'Administrator', 'Developer', 'Security Personnel',
];

interface PeopleAsset {
  id: number;
  name: string;
  email: string | null;
  asset_type: string;
  department: string | null;
  job_title: string | null;
  manager: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

const PeopleList = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.roles?.some(r => r === 'super_admin' || r === 'compliance_admin');

  const [items, setItems] = useState<PeopleAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<PeopleAsset | null>(null);

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
      const params: any = { page, page_size: pageSize, sort_by: 'name', sort_dir: 'asc' };
      if (search) params.search = search;
      if (filterType) params.asset_type = filterType;
      if (filterDepartment) params.department = filterDepartment;
      if (filterStatus) params.status = filterStatus;
      if (includeArchived) params.include_archived = true;

      const response = await api.get('/api/people-assets/', { params });
      setItems(response.data);
      setHasMore(response.data.length >= pageSize);
    } catch {
      setError('Failed to load people assets');
    } finally {
      setLoading(false);
    }
  }, [search, filterType, filterDepartment, filterStatus, includeArchived, page]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  useEffect(() => {
    api.get('/api/people-assets/departments').then(r => setDepartments(r.data)).catch(() => {});
  }, []);

  const handleArchive = async (id: number) => {
    if (!window.confirm('Archive this people asset?')) return;
    try {
      await api.post(`/api/people-assets/${id}/archive`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to archive');
    }
  };

  const handleRestore = async (id: number) => {
    try {
      await api.post(`/api/people-assets/${id}/restore`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Permanently delete this people asset? This cannot be undone.')) return;
    try {
      await api.delete(`/api/people-assets/${id}`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const openEdit = (asset: PeopleAsset) => {
    setEditingAsset(asset);
    setShowFormModal(true);
  };

  const clearFilters = () => {
    setSearch('');
    setFilterType('');
    setFilterDepartment('');
    setFilterStatus('');
    setIncludeArchived(false);
    setPage(1);
  };

  const hasFilters = search || filterType || filterDepartment || filterStatus || includeArchived;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People</p>
          <h1>People Assets</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-primary" onClick={() => navigate('/assets/people/new')}>
            <Plus size={18} />
            Add Person
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: '1 1 200px' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input className="form-control" style={{ paddingLeft: '2.25rem' }}
              placeholder="Search people..."
              value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select className="form-control" style={{ width: 'auto', minWidth: '160px' }} value={filterType} onChange={(e) => { setFilterType(e.target.value); setPage(1); }}>
            <option value="">All Types</option>
            {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '140px' }} value={filterDepartment} onChange={(e) => { setFilterDepartment(e.target.value); setPage(1); }}>
            <option value="">All Departments</option>
            {departments.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '120px' }} value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}>
            <option value="">All Status</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
          </select>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={includeArchived} onChange={(e) => { setIncludeArchived(e.target.checked); setPage(1); }} />
            Include archived
          </label>
          {hasFilters && (
            <button className="btn btn-ghost" onClick={clearFilters} style={{ fontSize: '0.8125rem' }}>Clear</button>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Asset Type</th>
              <th>Department</th>
              <th>Job Title</th>
              <th>Status</th>
              <th style={{ width: '140px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && items.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '4rem' }}><Loader2 className="animate-spin" size={32} color="var(--primary)" /></td></tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  No people assets found. Click "Add Person" to get started.
                </td>
              </tr>
            ) : items.map((item) => (
              <tr key={item.id} style={{ transition: 'background-color 0.2s', opacity: item.archived_at ? 0.6 : 1 }}>
                <td>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)', cursor: 'pointer' }} onClick={() => navigate(`/assets/people/${item.id}`)}>
                      {item.name}
                    </span>
                    {item.email && <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{item.email}</span>}
                  </div>
                </td>
                <td><span className="badge badge-secondary">{item.asset_type}</span></td>
                <td>{item.department || '-'}</td>
                <td>{item.job_title || '-'}</td>
                <td>
                  <span className={`badge ${item.status === 'Active' ? 'badge-success' : 'badge-secondary'}`}>
                    {item.archived_at ? 'Archived' : item.status}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.375rem', justifyContent: 'flex-end' }}>
                    <button className="btn btn-ghost" style={{ padding: '0.25rem' }} onClick={() => navigate(`/assets/people/${item.id}`)} title="View">
                      <Eye size={14} />
                    </button>
                    <button className="btn btn-ghost" style={{ padding: '0.25rem' }} onClick={() => openEdit(item)} title="Edit">
                      <UserCheck size={14} />
                    </button>
                    {item.archived_at ? (
                      <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#eab308' }} onClick={() => handleRestore(item.id)} title="Restore">
                        <RotateCcw size={14} />
                      </button>
                    ) : (
                      <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#eab308' }} onClick={() => handleArchive(item.id)} title="Archive">
                        <Archive size={14} />
                      </button>
                    )}
                    {isAdmin && (
                      <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#ef4444' }} onClick={() => handleDelete(item.id)} title="Delete">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
        <button className="btn btn-outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
        <span style={{ display: 'flex', alignItems: 'center', fontSize: '0.875rem', color: 'var(--text-muted)', padding: '0 0.5rem' }}>Page {page}</span>
        <button className="btn btn-outline" disabled={!hasMore} onClick={() => setPage(page + 1)}>Next</button>
      </div>

      {showFormModal && (
        <PeopleFormModal
          asset={editingAsset}
          onClose={() => { setShowFormModal(false); setEditingAsset(null); }}
          onSuccess={() => { setShowFormModal(false); setEditingAsset(null); fetchItems(); }}
        />
      )}
    </div>
  );
};

export default PeopleList;
