import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, FileCheck, Loader2, Search, ClipboardCheck } from 'lucide-react';
import api from '../../services/api';

interface Framework {
  id: number;
  name: string;
  description: string;
  version: string;
}

const ComplianceList = () => {
  const navigate = useNavigate();
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchFrameworks = async () => {
    try {
      const response = await api.get('/api/frameworks/');
      setFrameworks(response.data);
      setError('');
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('Access denied. You do not have permission to view compliance frameworks.');
      } else {
        setError('Failed to load compliance frameworks. Please check your backend connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFrameworks();
  }, []);

  const filteredFrameworks = frameworks.filter(f => 
    f.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    f.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading && frameworks.length === 0) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} color="var(--primary)" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header">
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Compliance</p>
          <h1>Framework Library</h1>
        </div>
      </div>

      <div style={{ marginBottom: '2rem', position: 'relative' }}>
        <Search style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} size={20} />
        <input 
          type="text" 
          placeholder="Search frameworks (e.g. ISO 27001, SOC 2...)" 
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '2rem' }}>
        {filteredFrameworks.length === 0 ? (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '5rem', color: 'var(--text-muted)', backgroundColor: 'var(--surface)', borderRadius: 'var(--radius)', border: '1px dashed var(--border)' }}>
            No frameworks found matching your search.
          </div>
        ) : filteredFrameworks.map((framework) => (
          <div key={framework.id} className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '2rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '1.25rem' }}>
              <div style={{ padding: '1rem', borderRadius: '14px', backgroundColor: 'rgba(14, 165, 233, 0.1)', color: 'var(--primary)' }}>
                <ShieldCheck size={32} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>{framework.name}</h3>
                <span className="badge badge-indigo" style={{ marginTop: '0.5rem' }}>v{framework.version}</span>
              </div>
            </div>
            
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', lineHeight: 1.6, flex: 1, marginBottom: '2rem' }}>
              {framework.description}
            </p>

            <div style={{ display: 'flex', borderTop: '1px solid var(--border)', paddingTop: '1.5rem', marginTop: 'auto', gap: '1rem' }}>
              <button 
                className="btn btn-primary" 
                style={{ flex: 1 }}
                onClick={() => navigate(`/compliance/${framework.id}/checklist`)}
              >
                <ClipboardCheck size={18} />
                View Checklist
              </button>
              <button className="btn btn-secondary" style={{ padding: '0.75rem' }} title="Requirements Overview" onClick={() => navigate(`/compliance/${framework.id}/requirements`)}>
                <FileCheck size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ComplianceList;
