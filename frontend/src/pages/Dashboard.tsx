import { useEffect, useState } from 'react';
import { ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
  const { user } = useAuth();

  const [stats] = useState([

    { label: 'Compliance Score', value: '84%', icon: ShieldCheck, color: '#10b981', key: 'compliance', visible: true },
    { label: 'Open Risks', value: '7', icon: AlertCircle, color: '#f59e0b', key: 'risks', visible: true },
  ]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // In a real scenario, we would fetch actual scores and risk counts here.
        // For now, we simulate a successful data load for the GRC UI.
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch dashboard stats', err);
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Loader2 className="animate-spin" /></div>;

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Overview</p>
        <h1>Welcome back, {user?.first_name || 'User'}</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
        {stats.filter(s => s.visible).map((stat) => (
          <div key={stat.label} className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: 0, padding: '2rem' }}>
            <div style={{ padding: '1rem', borderRadius: '14px', backgroundColor: `${stat.color}15`, color: stat.color }}>
              <stat.icon size={32} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.25rem' }}>{stat.label}</p>
              <h3 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-main)' }}>{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '2rem', borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Recent Activity</h3>
          </div>
          <div style={{ textAlign: 'center', padding: '6rem 2rem', color: 'var(--text-muted)' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'rgba(255, 255, 255, 0.02)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', border: '1px solid var(--border)' }}>
              <ShieldCheck size={32} style={{ opacity: 0.3 }} />
            </div>
            <p style={{ fontSize: '0.9375rem', maxWidth: '300px', margin: '0 auto' }}>All systems are nominal. Recent audit logs and system activities will appear here as they occur.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
