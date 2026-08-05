import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Server, Monitor, Cloud, Cpu, Plus, ArrowRight } from 'lucide-react';
import api from '../../services/api';

interface Counts {
  total: number;
  active: number;
  physical_servers: number;
  virtual_machines: number;
  cloud_compute: number;
}

const ComputeDashboard = () => {
  const navigate = useNavigate();
  const [counts, setCounts] = useState<Counts | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/compute-assets/counts')
      .then(r => setCounts(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" size={48} color="var(--primary)" /></div>;
  }

  const statCards = [
    { label: 'Total Assets', value: counts?.total ?? 0, icon: Server, color: '#3b82f6' },
    { label: 'Active', value: counts?.active ?? 0, icon: Monitor, color: '#22c55e' },
    { label: 'Physical Servers', value: counts?.physical_servers ?? 0, icon: Cpu, color: '#8b5cf6' },
    { label: 'Virtual Machines', value: counts?.virtual_machines ?? 0, icon: Monitor, color: '#f97316' },
    { label: 'Cloud Compute', value: counts?.cloud_compute ?? 0, icon: Cloud, color: '#06b6d4' },
  ];

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Servers & Compute</p>
          <h1>Servers & Compute Dashboard</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-primary" onClick={() => navigate('/assets/servers/list')}>
            View All <ArrowRight size={18} />
          </button>
        </div>
      </div>

      <div className="page-actions" style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-primary" onClick={() => navigate('/assets/servers/new')}>
          <Plus size={18} /> Add Compute Asset
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
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
    </div>
  );
};

export default ComputeDashboard;
