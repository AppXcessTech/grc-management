import React, { useEffect, useState, useMemo } from 'react';
import { X, Loader2, Save, ChevronDown, ChevronRight } from 'lucide-react';
import api from '../services/api';

interface Permission {
  id: number;
  resource: string;
  action: string;
  category: string | null;
  description: string;
}

interface PermissionModalProps {
  roleId: number;
  roleName: string;
  onClose: () => void;
}

const CATEGORY_ORDER = [
  'User & Organization Management',
  'Asset Inventory',
  'Compliance Frameworks',
  'Policy Management',
  'Evidence Collection',
  'Cloud & Security Monitoring',
  'Audit Management',
  'Risk Management',
  'Vendor Management',
  'Security Questionnaires',
];

const PermissionModal: React.FC<PermissionModalProps> = ({ roleId, roleName, onClose }) => {
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [rolePermissions, setRolePermissions] = useState<number[]>([]);
  const [originalPermissions, setOriginalPermissions] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [allRes, roleRes] = await Promise.all([
          api.get('/api/roles/permissions'),
          api.get(`/api/roles/${roleId}/permissions`)
        ]);
        setAllPermissions(allRes.data);
        const rolePermIds = roleRes.data.map((p: any) => p.id);
        setRolePermissions(rolePermIds);
        setOriginalPermissions([...rolePermIds]);
      } catch (err) {
        console.error('Failed to fetch permissions', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [roleId]);

  const grouped = useMemo(() => {
    const groups: Record<string, Permission[]> = {};
    const uncategorized: Permission[] = [];
    for (const perm of allPermissions) {
      if (perm.category) {
        if (!groups[perm.category]) groups[perm.category] = [];
        groups[perm.category].push(perm);
      } else {
        uncategorized.push(perm);
      }
    }
    const ordered: { category: string; permissions: Permission[] }[] = [];
    for (const cat of CATEGORY_ORDER) {
      if (groups[cat]) {
        ordered.push({ category: cat, permissions: groups[cat] });
        delete groups[cat];
      }
    }
    for (const [cat, perms] of Object.entries(groups)) {
      ordered.push({ category: cat, permissions: perms });
    }
    if (uncategorized.length > 0) {
      ordered.unshift({ category: 'General', permissions: uncategorized });
    }
    return ordered;
  }, [allPermissions]);

  const togglePermission = (permissionId: number) => {
    setRolePermissions(prev => 
      prev.includes(permissionId) 
        ? prev.filter(id => id !== permissionId) 
        : [...prev, permissionId]
    );
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post('/api/roles/sync-permissions', {
        role_id: roleId,
        permission_ids: rolePermissions
      });
      setOriginalPermissions([...rolePermissions]);
      alert('Permissions saved successfully');
      onClose();
    } catch (err) {
      console.error('Failed to save permissions', err);
      alert('Failed to save permissions');
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = JSON.stringify([...rolePermissions].sort()) !== JSON.stringify([...originalPermissions].sort());

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
      backgroundColor: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '900px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h2 style={{ margin: 0 }}>Permissions: {roleName}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X /></button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '5rem' }}><Loader2 className="animate-spin" size={40} color="var(--primary)" /></div>
        ) : (
          <>
            <div style={{ overflowY: 'auto', flex: 1, marginBottom: '2rem' }}>
              {grouped.map(({ category, permissions }) => {
                const enabledCount = permissions.filter(p => rolePermissions.includes(p.id)).length;
                const isExpanded = expandedCategories.has(category);
                return (
                  <div key={category} style={{ marginBottom: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
                    <div
                      onClick={() => toggleCategory(category)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                        padding: '0.75rem 1rem', cursor: 'pointer',
                        backgroundColor: 'var(--bg-secondary)', fontWeight: 600,
                        fontSize: '0.9375rem', color: 'var(--text-main)',
                        borderBottom: isExpanded ? '1px solid var(--border)' : 'none',
                        userSelect: 'none',
                      }}
                    >
                      {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                      <span style={{ flex: 1 }}>{category}</span>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                        {enabledCount}/{permissions.length}
                      </span>
                    </div>
                    {isExpanded && (
                      <table className="data-table" style={{ margin: 0, border: 'none' }}>
                        <thead>
                          <tr>
                            <th>Resource</th>
                            <th>Action</th>
                            <th>Description</th>
                            <th style={{ textAlign: 'center', width: '80px' }}>Enabled</th>
                          </tr>
                        </thead>
                        <tbody>
                          {permissions.map((perm) => (
                            <tr key={perm.id}>
                              <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{perm.resource}</td>
                              <td><span className="badge badge-indigo">{perm.action}</span></td>
                              <td style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{perm.description}</td>
                              <td style={{ textAlign: 'center' }}>
                                <input 
                                  type="checkbox" 
                                  checked={rolePermissions.includes(perm.id)}
                                  onChange={() => togglePermission(perm.id)}
                                  style={{ 
                                    width: '20px', height: '20px', cursor: 'pointer',
                                    accentColor: 'var(--primary)'
                                  }}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
              <button className="btn btn-secondary" onClick={onClose} disabled={saving}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={!hasChanges || saving}>
                {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                Save Changes
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PermissionModal;
