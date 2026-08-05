import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Users, UserCheck, UserX, Archive, Plus, ArrowRight } from 'lucide-react';
import api from '../../services/api';

interface Counts {
  total: number;
  active: number;
  inactive: number;
  archived: number;
  by_type: Record<string, number>;
}

const TYPE_COLORS: Record<string, string> = {
  Employee: '#3b82f6',
  Contractor: '#f97316',
  Consultant: '#8b5cf6',
  Intern: '#06b6d4',
  'Temporary Staff': '#eab308',
  'Third-Party User': '#ec4899',
  'Vendor User': '#14b8a6',
  'Service Account': '#6366f1',
  'Shared Account': '#84cc16',
  'Privileged Account': '#ef4444',
  Administrator: '#f43f5e',
  Developer: '#22c55e',
  'Security Personnel': '#a855f7',
};

const PeopleDashboard = () => {
  const navigate = useNavigate();
  const [counts, setCounts] = useState<Counts | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/people-assets/counts')
      .then(r => setCounts(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" size={48} color="var(--primary)" /></div>;
  }

  const statCards = [
    { label: 'Total People', value: counts?.total ?? 0, icon: Users, color: '#3b82f6' },
    { label: 'Active', value: counts?.active ?? 0, icon: UserCheck, color: '#22c55e' },
    { label: 'Inactive', value: counts?.inactive ?? 0, icon: UserX, color: '#eab308' },
    { label: 'Archived', value: counts?.archived ?? 0, icon: Archive, color: '#6b7280' },
  ];

  const typeEntries = Object.entries(counts?.by_type ?? {}).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(...typeEntries.map(([, c]) => c), 1);

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People</p>
          <h1>People Assets Dashboard</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-primary" onClick={() => navigate('/assets/people/list')}>
            View All <ArrowRight size={18} />
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {statCards.map(card => (
          <div key={card.label} className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: '0.375rem' }}>{card.label}</p>
                <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>{card.value}</p>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius)', backgroundColor: `${card.color}15` }}>
                <card.icon size={24} color={card.color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', margin: 0 }}>By Asset Type</h3>
            <button className="btn btn-ghost" style={{ fontSize: '0.8125rem' }} onClick={() => navigate('/assets/people/list')}>View All →</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
            {typeEntries.length === 0 && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '2rem' }}>No people assets yet. Click "Add Person" to get started.</p>
            )}
            {typeEntries.map(([type, count]) => (
              <div key={type}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: '0.25rem' }}>
                  <span style={{ fontWeight: 500 }}>{type}</span>
                  <span style={{ fontWeight: 600 }}>{count}</span>
                </div>
                <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border)', borderRadius: '999px', overflow: 'hidden' }}>
                  <div style={{ width: `${(count / maxCount) * 100}%`, height: '100%', backgroundColor: TYPE_COLORS[type] || '#6366f1', borderRadius: '999px', transition: 'width 0.3s' }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Quick Actions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <button className="btn btn-primary" style={{ justifyContent: 'flex-start', padding: '0.75rem 1rem' }} onClick={() => navigate('/assets/people/new')}>
              <Plus size={18} />
              <span style={{ marginLeft: '0.5rem' }}>Add New People Asset</span>
            </button>
            <button className="btn btn-outline" style={{ justifyContent: 'flex-start', padding: '0.75rem 1rem' }} onClick={() => navigate('/assets/people/list')}>
              <Users size={18} />
              <span style={{ marginLeft: '0.5rem' }}>Browse All People Assets</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PeopleDashboard;
