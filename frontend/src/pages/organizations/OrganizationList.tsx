import { useEffect, useState } from 'react';
import { Loader2, Building, GitBranch } from 'lucide-react';
import api from '../../services/api';

interface Organization {
  id: number;
  name: string;
  slug: string;
  domain: string | null;
  industry: string | null;
  size: string;
  created_at: string;
}

interface Subsidiary {
  id: number;
  parent_organization_id: number;
  child_organization_id: number;
  relationship_type: string;
}

const OrganizationList = () => {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [subsidiaries, setSubsidiaries] = useState<Subsidiary[]>([]);
  const [myOrgId, setMyOrgId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const [orgsRes, subsRes] = await Promise.all([
        api.get('/api/organizations/'),
        api.get('/api/subsidiaries/'),
      ]);
      setOrgs(orgsRes.data);
      setSubsidiaries(subsRes.data);
      const me = await api.get('/api/auth/me');
      setMyOrgId(me.data.organization_id);
    } catch {
      setError('Failed to load organizations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);

  const isChildOrg = (orgId: number) =>
    subsidiaries.some((s) => s.child_organization_id === orgId && s.parent_organization_id === myOrgId);

  if (loading) {
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
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>Organization</p>
          <h1>Organizations</h1>
        </div>

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
              <th>Name</th>
              <th>Slug</th>
              <th>Domain</th>
              <th>Industry</th>
              <th>Size</th>
            </tr>
          </thead>
          <tbody>
            {orgs.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  <Building size={48} style={{ marginBottom: '1rem', opacity: 0.2 }} />
                  <p>No organizations found.</p>
                </td>
              </tr>
            ) : orgs.map((org) => (
              <tr key={org.id}>
                <td style={{ fontWeight: 600 }}>
                  {org.name}
                  {org.id === myOrgId && <span className="badge" style={{ marginLeft: '0.5rem', backgroundColor: 'rgba(14,165,233,0.1)', color: 'var(--primary)' }}>Primary</span>}
                  {isChildOrg(org.id) && <span className="badge badge-indigo" style={{ marginLeft: '0.5rem' }}><GitBranch size={12} style={{ marginRight: '0.25rem' }} />Subsidiary</span>}
                </td>
                <td><code>{org.slug}</code></td>
                <td style={{ color: 'var(--text-muted)' }}>{org.domain || '—'}</td>
                <td style={{ color: 'var(--text-muted)' }}>{org.industry || '—'}</td>
                <td><span className="badge badge-indigo" style={{ textTransform: 'capitalize' }}>{org.size}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>


    </div>
  );
};

export default OrganizationList;