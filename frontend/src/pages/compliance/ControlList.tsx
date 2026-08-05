import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Search, Info } from 'lucide-react';
import api from '../../services/api';

interface ControlItem {
  id: number;
  code: string;
  name: string;
  description: string | null;
  status: string | null;
  evidence_count: number;
}

interface Framework {
  id: number;
  name: string;
  description: string;
  version: string;
}

const STATUS_OPTIONS = ['compliant', 'non_compliant', 'in_progress', 'not_applicable'] as const;

const ControlList = () => {
  const { frameworkId } = useParams();
  const navigate = useNavigate();
  const [controls, setControls] = useState<ControlItem[]>([]);
  const [framework, setFramework] = useState<Framework | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [frameworkRes, ctrlsRes] = await Promise.all([
          api.get(`/api/frameworks/${frameworkId}`),
          api.get(`/api/controls/?framework_id=${frameworkId}`)
        ]);
        setFramework(frameworkRes.data);
        setControls(Array.isArray(ctrlsRes.data) ? ctrlsRes.data : []);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setError('Access denied. You do not have permission to view controls.');
        } else {
          setError('Failed to load controls.');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [frameworkId]);

  const [savingId, setSavingId] = useState<number | null>(null);
  const [draftStatus, setDraftStatus] = useState<Record<number, string | null>>({});

  const updateStatus = async (ctrlId: number, newStatus: string | null) => {
    setSavingId(ctrlId);
    try {
      await api.patch(`/api/controls/${ctrlId}`, { status: newStatus });
      setControls(prev =>
        prev.map(c => c.id === ctrlId ? { ...c, status: newStatus } : c)
      );
      setDraftStatus(prev => ({ ...prev, [ctrlId]: undefined }));
    } catch {
      setError('Failed to update status');
    } finally {
      setSavingId(null);
    }
  };

  const statusLabel = (status: string | null) => {
    switch (status) {
      case 'compliant': return 'Compliant';
      case 'non_compliant': return 'Non-Compliant';
      case 'in_progress': return 'In Progress';
      case 'not_applicable': return 'N/A';
      default: return 'None';
    }
  };

  const statusColor = (status: string | null) => {
    switch (status) {
      case 'compliant':
        return 'var(--success)';
      case 'in_progress':
        return 'var(--primary)';
      case 'non_compliant':
        return 'var(--danger)';
      default:
        return 'var(--text-muted)';
    }
  };

  const filteredControls = controls.filter(c =>
    c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.description?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} color="var(--primary)" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/compliance')}
            style={{ padding: '0.5rem', borderRadius: '50%' }}
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              {framework?.name} Annex A Controls
            </p>
            <h1>{framework?.name} Controls</h1>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'flex-start', gap: '1rem', backgroundColor: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.1)' }}>
        <Info size={24} color="var(--primary)" style={{ marginTop: '0.25rem' }} />
        <div>
          <h4 style={{ margin: '0 0 0.5rem 0' }}>About {framework?.name} v{framework?.version}</h4>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.925rem' }}>{framework?.description}</p>
          <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {controls.length} Annex A controls — ISO/IEC 27001:2022
          </p>
        </div>
      </div>

      <div style={{ marginBottom: '2rem', position: 'relative' }}>
        <Search style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} size={20} />
        <input
          type="text"
          placeholder="Search by code or title..."
          className="form-control"
          style={{ paddingLeft: '3rem', width: '100%', maxWidth: '500px' }}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
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
              <th style={{ width: '110px' }}>Code</th>
              <th>Control Title</th>
              <th style={{ width: '200px', textAlign: 'center' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredControls.length === 0 ? (
              <tr>
                <td colSpan={3} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  No controls found.
                </td>
              </tr>
            ) : filteredControls.map((ctrl) => (
              <tr key={ctrl.id}>
                <td style={{ verticalAlign: 'top', paddingTop: '1.25rem' }}>
                  <span className="badge badge-indigo" style={{ fontSize: '0.8125rem', fontWeight: 700 }}>
                    {ctrl.code}
                  </span>
                </td>
                <td style={{ paddingTop: '1.25rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.375rem', fontSize: '1rem', color: 'var(--text-main)' }}>{ctrl.name}</div>
                  {ctrl.description && (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.5 }}>{ctrl.description}</div>
                  )}
                </td>
                <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                    <select
                      className="form-control"
                      style={{ width: 'auto', minWidth: '130px', fontSize: '0.8125rem', padding: '0.375rem 0.5rem' }}
                      value={draftStatus[ctrl.id] ?? ctrl.status ?? ''}
                      onChange={(e) => setDraftStatus(prev => ({ ...prev, [ctrl.id]: e.target.value || null }))}
                    >
                      <option value="">None</option>
                      {STATUS_OPTIONS.map(opt => (
                        <option key={opt} value={opt}>{statusLabel(opt)}</option>
                      ))}
                    </select>
                    <button
                      className="btn btn-primary"
                      style={{ padding: '0.375rem 0.75rem', fontSize: '0.8125rem', whiteSpace: 'nowrap' }}
                      onClick={() => updateStatus(ctrl.id, draftStatus[ctrl.id] ?? ctrl.status ?? null)}
                      disabled={savingId === ctrl.id}
                    >
                      {savingId === ctrl.id ? <Loader2 size={14} className="animate-spin" /> : 'Save'}
                    </button>
                  </div>
                  {ctrl.status && (
                    <div style={{ fontSize: '0.6875rem', color: statusColor(ctrl.status), marginTop: '0.25rem', textAlign: 'center' }}>
                      Current: {statusLabel(ctrl.status)}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: '1.5rem', padding: '1rem', display: 'flex', gap: '1.5rem', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
        <span style={{ color: 'var(--text-muted)' }}>None</span>
        <span style={{ color: 'var(--success)' }}>Compliant</span>
        <span style={{ color: 'var(--primary)' }}>In Progress</span>
        <span style={{ color: 'var(--danger)' }}>Non-Compliant</span>
      </div>
    </div>
  );
};

export default ControlList;