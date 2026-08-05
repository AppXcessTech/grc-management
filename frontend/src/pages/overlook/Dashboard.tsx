import React, { useEffect, useState } from 'react';
import { Building2, Users, Activity, ShieldCheck, AlertTriangle } from 'lucide-react';
import api from '../../services/api';

const OverlookDashboard = () => {
  const [stats, setStats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/api/overlook/organizations/');
        setStats(response.data);
      } catch (err) {
        console.error('Failed to fetch dashboard stats', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const totalUsers = stats.reduce((acc, org) => acc + org.user_count, 0);

  const cards = [
    { title: 'Total Organizations', value: stats.length, icon: Building2, color: '#3b82f6' },
    { title: 'Total Users', value: totalUsers, icon: Users, color: '#10b981' },
    { title: 'System Health', value: '99.9%', icon: Activity, color: '#f43f5e' },
    { title: 'Active Support Tokens', value: '0', icon: ShieldCheck, color: '#8b5cf6' },
  ];

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <div>
          <p style={{ color: '#f43f5e', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Global Overview</p>
          <h1>Overlook Dashboard</h1>
        </div>
      </div>

      <div className="dashboard-grid">
        {cards.map((card) => (
          <div key={card.title} className="card dashboard-card">
            <div className="card-icon" style={{ backgroundColor: `${card.color}10`, color: card.color }}>
              <card.icon size={24} />
            </div>
            <div className="card-info">
              <h3>{card.title}</h3>
              <p>{card.value}</p>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h2>Critical Alerts</h2>
        <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <AlertTriangle size={48} color="#f59e0b" style={{ marginBottom: '1rem' }} />
          <p>No critical system alerts at this time.</p>
        </div>
      </div>
    </div>
  );
};

export default OverlookDashboard;
