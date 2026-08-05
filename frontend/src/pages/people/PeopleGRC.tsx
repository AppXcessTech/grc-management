import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

/* ===== MOCK DATA ===== */

const DEPARTMENTS = ['Engineering', 'Security', 'Finance', 'HR', 'Sales', 'Marketing', 'Legal', 'Operations', 'Product', 'IT'];
const PERSON_TYPES = ['Employee', 'Contractor', 'Consultant', 'Intern', 'Temp Staff', 'Vendor User', 'Third-Party User', 'Service Account', 'Shared Account', 'Privileged Account', 'Administrator', 'Developer', 'Security Personnel'];
const ACCOUNT_TYPES = ['Standard', 'Privileged', 'Service', 'Shared', 'Admin'];
const STATUSES = ['Active', 'Suspended', 'Offboarding'];
const RISK_LEVELS = ['Low', 'Medium', 'High'];
const SYSTEMS = ['AWS Console', 'GitHub Enterprise', 'Jira Cloud', 'Confluence', 'Slack', 'Workday', 'Okta', 'Datadog', 'PagerDuty', 'Sentry', 'Cloudflare', 'Vercel', 'Docker Hub', 'npm Registry', 'GCP Console', 'Azure Portal'];
const FRAMEWORKS = ['ISO 27001', 'SOC 2', 'GDPR', 'HIPAA'];
const MFA_METHODS = ['FIDO2', 'TOTP', 'Push', 'SMS', 'Email OTP', 'None'];
const MFA_STATUS_OPTIONS = ['Strong', 'Active', 'Weak', 'Exception', 'Non-compliant'];
const MFA_EVIDENCE_TYPES = ['Policy screenshot', 'Per-user status report', 'Sign-in log', 'Admin console export', 'Manual upload'];

const mockPeople = [
  { id: 1, firstName: 'Alice', lastName: 'Chen', email: 'alice.chen@trustgrid.io', personalEmail: 'alice@gmail.com', phone: '+1-415-555-0101', displayName: 'Alice Chen', employeeId: 'EMP-001', personType: 'Administrator', accountType: 'Privileged', department: 'Security', jobTitle: 'CISO', manager: 'Board of Directors', location: 'San Francisco, CA', workArrangement: 'Hybrid', costCenter: 'CC-SEC-001', status: 'Active', riskLevel: 'Medium', mfa: { enrolled: true, enforced: true, method: 'FIDO2', enforcedVia: ['Okta Policy', 'Entra ID Conditional Access'], enrollmentDate: '2023-03-14', lastVerifiedDate: '2024-11-20', verificationSource: 'Okta API', exceptionGranted: false, exceptionReason: '', exceptionApprovedBy: '', exceptionExpiryDate: '', evidence: [{ id: 'ev-001', type: 'Per-user status report', url: '', uploadedDate: '2024-11-20', notes: 'Exported from Okta admin console' }], notes: '' }, lastAccessReview: '2026-05-15', nextReviewDue: '2026-08-15', accessReviewStatus: 'Completed', startDate: '2020-03-01', endDate: null, onboardingComplete: true, offboardingDate: null, authMethod: 'SSO + MFA', pamVault: true, vpnAccess: true, riskScore: 35, dataClassification: 'Restricted', backgroundCheck: 'Completed (2026-01)', ndaSigned: true, lastLogin: '2026-06-23 14:32:18 UTC', lastLoginIp: '203.0.113.42', lastLoginGeo: 'San Francisco, US', anomalousActivity: false, createdAt: '2020-03-01 09:00:00 UTC', createdSource: 'Okta', lastModified: '2026-06-20 11:15:00 UTC', lastModifiedBy: 'System', dataSource: 'Okta', assignedDevices: [{ type: 'laptop', name: 'MacBook Pro M3 - ALICE-001' }, { type: 'phone', name: 'iPhone 16 Pro - ALICE-001' }], softwareLicences: ['Microsoft 365 E5', 'Datadog Enterprise', 'GitHub Enterprise'], linkedPolicies: ['Acceptable Use Policy', 'Security Policy', 'Access Control Policy'], vendorOrg: null, openIncidents: 0, auditLog: [{ event: 'Access review completed', date: '2026-05-15 10:00 UTC' }, { event: 'MFA device enrolled', date: '2025-11-20 14:30 UTC' }, { event: 'Role changed to CISO', date: '2024-06-01 09:00 UTC' }, { event: 'Onboarding completed', date: '2020-03-01 12:00 UTC' }], complianceTraining: { securityAwareness: 'Complete', gdpr: 'Complete', aup: 'Complete', codeOfConduct: 'Complete', phishing: 'Complete' } },
  { id: 2, firstName: 'Bob', lastName: 'Martinez', email: 'bob.martinez@trustgrid.io', personalEmail: null, phone: '+1-512-555-0202', displayName: 'Bob Martinez', employeeId: 'EMP-002', personType: 'Developer', accountType: 'Standard', department: 'Engineering', jobTitle: 'Senior Backend Engineer', manager: 'David Kim', location: 'Austin, TX', workArrangement: 'Remote', costCenter: 'CC-ENG-001', status: 'Active', riskLevel: 'Low', mfa: { enrolled: true, enforced: true, method: 'TOTP', enforcedVia: ['Okta Policy'], enrollmentDate: '2021-07-20', lastVerifiedDate: '2026-06-15', verificationSource: 'Okta API', exceptionGranted: false, exceptionReason: '', exceptionApprovedBy: '', exceptionExpiryDate: '', evidence: [], notes: '' }, lastAccessReview: '2026-04-20', nextReviewDue: '2026-07-20', accessReviewStatus: 'Completed', startDate: '2021-07-15', endDate: null, onboardingComplete: true, offboardingDate: null, authMethod: 'SSO + MFA', pamVault: false, vpnAccess: true, riskScore: 18, dataClassification: 'Internal', backgroundCheck: 'Completed (2021-07)', ndaSigned: true, lastLogin: '2026-06-23 09:15:42 UTC', lastLoginIp: '104.28.0.1', lastLoginGeo: 'Austin, US', anomalousActivity: false, createdAt: '2021-07-15 08:00:00 UTC', createdSource: 'Workday', lastModified: '2026-06-22 16:45:00 UTC', lastModifiedBy: 'Bob Martinez', dataSource: 'Workday', assignedDevices: [{ type: 'laptop', name: 'ThinkPad X1 - BOB-001' }], softwareLicences: ['JetBrains All Products', 'GitHub Team', 'Datadog APM'], linkedPolicies: ['Acceptable Use Policy', 'Code of Conduct'], vendorOrg: null, openIncidents: 1, auditLog: [{ event: 'Password rotated', date: '2026-06-15 08:00 UTC' }, { event: 'SSO session expired', date: '2026-06-14 18:00 UTC' }, { event: 'Access review completed', date: '2026-04-20 11:00 UTC' }], complianceTraining: { securityAwareness: 'Complete', gdpr: 'Complete', aup: 'Complete', codeOfConduct: 'Complete', phishing: 'Due' } },
  { id: 3, firstName: 'Carol', lastName: 'Williams', email: 'carol.williams@trustgrid.io', personalEmail: null, phone: null, displayName: 'Carol Williams', employeeId: 'CON-001', personType: 'Contractor', accountType: 'Standard', department: 'Marketing', jobTitle: 'Content Strategist', manager: 'Sarah Lee', location: 'Remote', workArrangement: 'Remote', costCenter: 'CC-MKT-001', status: 'Active', riskLevel: 'Low', mfa: { enrolled: true, enforced: true, method: 'TOTP', enforcedVia: ['Okta Policy'], enrollmentDate: '2025-01-15', lastVerifiedDate: '2026-05-01', verificationSource: 'Okta API', exceptionGranted: false, exceptionReason: '', exceptionApprovedBy: '', exceptionExpiryDate: '', evidence: [{ id: 'ev-002', type: 'Policy screenshot', url: '', uploadedDate: '2025-01-15', notes: 'Contractor MFA policy acknowledgment' }], notes: '' }, lastAccessReview: '2026-05-01', nextReviewDue: '2026-08-01', accessReviewStatus: 'Completed', startDate: '2025-01-10', endDate: '2026-12-31', onboardingComplete: true, offboardingDate: null, authMethod: 'SSO', pamVault: false, vpnAccess: false, riskScore: 12, dataClassification: 'Public', backgroundCheck: 'Completed (2025-01)', ndaSigned: true, lastLogin: '2026-06-22 11:30:00 UTC', lastLoginIp: '198.51.100.1', lastLoginGeo: 'Portland, US', anomalousActivity: false, createdAt: '2025-01-10 09:00:00 UTC', createdSource: 'Manual', lastModified: '2026-06-01 14:00:00 UTC', lastModifiedBy: 'Admin', dataSource: 'Manual', assignedDevices: [{ type: 'laptop', name: 'MacBook Air - CAROL-001' }], softwareLicences: ['Adobe Creative Cloud', 'Canva Pro', 'HubSpot'], linkedPolicies: ['Acceptable Use Policy', 'Confidentiality Agreement'], vendorOrg: 'Creative Solutions Inc.', openIncidents: 0, auditLog: [{ event: 'Contract extended to Dec 2026', date: '2026-01-10 10:00 UTC' }, { event: 'Onboarding completed', date: '2025-01-10 14:00 UTC' }], complianceTraining: { securityAwareness: 'Complete', gdpr: 'Due', aup: 'Complete', codeOfConduct: 'Complete', phishing: 'Complete' } }
];

const auditEvents = [
  { action: 'Access review completed', icon: 'ti ti-shield-check' },
  { action: 'MFA enrolled', icon: 'ti ti-fingerprint' },
  { action: 'Role changed', icon: 'ti ti-user-check' },
  { action: 'Password rotated', icon: 'ti ti-key' },
  { action: 'Account suspended', icon: 'ti ti-user-off' },
  { action: 'Account created', icon: 'ti ti-user-plus' },
  { action: 'Onboarding completed', icon: 'ti ti-checklist' },
  { action: 'Offboarding initiated', icon: 'ti ti-logout' },
  { action: 'Privileged access granted', icon: 'ti ti-shield-lock' },
  { action: 'Anomalous activity flagged', icon: 'ti ti-alert-triangle' },
];

/* ===== BADGE HELPERS ===== */
const personTypeBadge = (pt: string) => {
  const map: Record<string, { text: string; color: string }> = {
    Administrator: { text: pt, color: '#7c3aed' }, 'Privileged Account': { text: pt, color: '#7c3aed' },
    'Security Personnel': { text: pt, color: '#7c3aed' }, Developer: { text: pt, color: '#2563eb' },
    Employee: { text: pt, color: '#059669' }, Contractor: { text: pt, color: '#d97706' },
    Consultant: { text: pt, color: '#d97706' }, Intern: { text: pt, color: '#0891b2' },
    'Temp Staff': { text: pt, color: '#0891b2' }, 'Vendor User': { text: pt, color: '#dc2626' },
    'Third-Party User': { text: pt, color: '#dc2626' }, 'Service Account': { text: pt, color: '#6b7280' },
    'Shared Account': { text: pt, color: '#6b7280' },
  };
  return map[pt] || { text: pt, color: '#6b7280' };
};
const accountTypeBadge = (at: string) => {
  const map: Record<string, string> = { Standard: '#059669', Privileged: '#7c3aed', Service: '#6b7280', Shared: '#d97706', Admin: '#dc2626' };
  return { text: at, color: map[at] || '#6b7280' };
};
const statusBadge = (st: string) => {
  const map: Record<string, string> = { Active: '#059669', Suspended: '#d97706', Offboarding: '#dc2626' };
  return { text: st, color: map[st] || '#6b7280' };
};
const riskBadge = (rl: string) => {
  const map: Record<string, { color: string; bar: string }> = { Low: { color: '#059669', bar: '25%' }, Medium: { color: '#d97706', bar: '55%' }, High: { color: '#dc2626', bar: '85%' } };
  return { text: rl, ...(map[rl] || { color: '#6b7280', bar: '0%' }) };
};
const trainingStatusIcon = (s: string) => {
  if (s === 'Complete') return <i className="ti ti-circle-check" style={{ color: '#059669' }}></i>;
  if (s === 'Due') return <i className="ti ti-clock" style={{ color: '#d97706' }}></i>;
  if (s === 'Overdue') return <i className="ti ti-alert-triangle" style={{ color: '#dc2626' }}></i>;
  if (s === 'Flagged') return <i className="ti ti-flag" style={{ color: '#dc2626' }}></i>;
  return <i className="ti ti-minus" style={{ color: '#9ca3af' }}></i>;
};
const trainingStatusBadge = (s: string) => {
  const map: Record<string, string> = { Complete: '#059669', Due: '#d97706', Overdue: '#dc2626', Flagged: '#dc2626' };
  return { text: s === 'Complete' ? 'Complete' : s === 'Due' ? 'Due' : s === 'Overdue' ? 'Overdue' : 'Flagged', color: map[s] || '#9ca3af' };
};
const deviceIcon = (t: string) => {
  const map: Record<string, string> = { laptop: 'ti ti-device-laptop', phone: 'ti ti-device-mobile', tablet: 'ti ti-device-tablet', token: 'ti ti-shield' };
  return map[t] || 'ti ti-device-laptop';
};

const initials = (first: string, last: string) => {
  if (!first && !last) return '?';
  if (!last) return first.substring(0, 2).toUpperCase();
  return (first[0] + last[0]).toUpperCase();
};

const avatarBg = (name: string) => {
  const colors = ['#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626', '#0891b2', '#6b7280', '#db2777', '#9333ea', '#0d9488'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return colors[Math.abs(hash) % colors.length];
};

/* ===== MFA HELPERS ===== */
const mfaStrength = (method: string) => {
  if (method === 'FIDO2') return 'Strong';
  if (method === 'TOTP' || method === 'Push') return 'Moderate';
  if (method === 'SMS' || method === 'Email OTP') return 'Weak';
  return 'None';
};

const mfaBadgeConfig = (mfa: any) => {
  if (!mfa) return { text: 'Unknown', color: '#6b7280', bg: '#6b728015' };
  if (mfa.enrolled && mfa.method === 'FIDO2') return { text: 'Strong MFA', color: '#7c3aed', bg: '#7c3aed15' };
  if (mfa.enrolled && (mfa.method === 'TOTP' || mfa.method === 'Push')) return { text: 'MFA Active', color: '#0d9488', bg: '#0d948815' };
  if (mfa.enrolled && (mfa.method === 'SMS' || mfa.method === 'Email OTP')) return { text: 'Weak MFA', color: '#d97706', bg: '#d9770615' };
  if (!mfa.enrolled && mfa.exceptionGranted) return { text: 'Exception', color: '#d97706', bg: '#d9770615' };
  if (!mfa.enrolled && !mfa.exceptionGranted) return { text: 'Non-compliant', color: '#dc2626', bg: '#dc262615' };
  return { text: 'Unknown', color: '#6b7280', bg: '#6b728015' };
};

const mfaStatusValue = (mfa: any) => {
  if (!mfa) return 'Unknown';
  if (mfa.enrolled && mfa.method === 'FIDO2') return 'Strong';
  if (mfa.enrolled && (mfa.method === 'TOTP' || mfa.method === 'Push')) return 'Active';
  if (mfa.enrolled && (mfa.method === 'SMS' || mfa.method === 'Email OTP')) return 'Weak';
  if (!mfa.enrolled && mfa.exceptionGranted) return 'Exception';
  if (!mfa.enrolled && !mfa.exceptionGranted) return 'Non-compliant';
  return 'Unknown';
};

const daysAgo = (dateStr: string) => {
  if (!dateStr) return Infinity;
  const diff = Date.now() - new Date(dateStr).getTime();
  return Math.floor(diff / 86400000);
};

/* ===== HELPERS ===== */
const apiToPerson = (a: any) => {
  const parts = a.name ? a.name.split(' ') : ['', ''];
  const firstName = parts[0] || '';
  const lastName = parts.slice(1).join(' ') || '';
  let extra: any = {};
  try { if (a.description) extra = JSON.parse(a.description); } catch {}
  return {
    id: a.id,
    firstName,
    lastName,
    email: a.email || '',
    displayName: a.name,
    employeeId: extra.employeeId || '',
    personType: a.asset_type || 'Employee',
    employmentType: extra.employmentType || '',
    accountType: extra.accountType || 'Standard',
    department: a.department || '',
    jobTitle: a.job_title || '',
    manager: a.manager || '',
    location: extra.location || '',
    workArrangement: extra.workArrangement || 'On-site',
    status: a.archived_at ? 'Inactive' : (a.status || 'Active'),
    riskLevel: extra.riskLevel || 'Low',
    riskScore: extra.riskScore != null ? extra.riskScore : 10,
    dataClassification: extra.dataClassification || 'Internal',
    ...extra,
    mfa: extra.mfa || { enrolled: false, enforced: false, method: 'None', enforcedVia: [], enrollmentDate: '', lastVerifiedDate: '', verificationSource: '', exceptionGranted: false, exceptionReason: '', exceptionApprovedBy: '', exceptionExpiryDate: '', evidence: [], notes: '' },
    startDate: extra.startDate || (a.start_date ? a.start_date.split('T')[0] : ''),
    endDate: extra.terminationDate || (a.end_date ? a.end_date.split('T')[0] : null),
    lastAccessReview: a.last_access_review || extra.lastAccessReview || null,
    nextReviewDue: extra.nextReviewDue || null,
    accessReviewStatus: extra.accessReviewStatus || 'N/A',
    onboardingComplete: extra.onboardingComplete ?? true,
    offboardingDate: extra.offboardingDate || null,
    authMethod: extra.authMethod || 'SSO',
    pamVault: extra.pamVault ?? false,
    vpnAccess: extra.vpnAccess ?? false,
    backgroundCheck: extra.backgroundCheck || null,
    ndaSigned: extra.ndaSigned ?? false,
    lastLogin: extra.lastLogin || null,
    lastLoginIp: extra.lastLoginIp || null,
    lastLoginGeo: extra.lastLoginGeo || null,
    anomalousActivity: extra.anomalousActivity ?? false,
    createdAt: a.created_at || '',
    createdSource: extra.createdSource || 'API',
    lastModified: a.updated_at || '',
    lastModifiedBy: extra.lastModifiedBy || '',
    lastPasswordChange: extra.lastPasswordChange || null,
    dataSource: 'API',
    assignedDevices: extra.assignedDevices || [],
    softwareLicences: extra.softwareLicences || [],
    linkedPolicies: extra.linkedPolicies || [],
    vendorOrg: extra.vendorOrg || null,
    openIncidents: extra.openIncidents ?? 0,
    auditLog: extra.auditLog || [{ event: 'Account created', date: a.created_at || '' }],
    complianceTraining: extra.complianceTraining || { securityAwareness: 'N/A', gdpr: 'N/A', aup: 'N/A', codeOfConduct: 'N/A', phishing: 'N/A' },
  };
};

const toApiFormat = (p: any) => ({
  name: `${p.firstName} ${p.lastName}`.trim(),
  email: p.email,
  asset_type: p.personType || 'Employee',
  department: p.department,
  job_title: p.jobTitle,
  manager: p.manager,
  status: p.status || 'Active',
  start_date: p.startDate ? new Date(p.startDate).toISOString() : null,
  end_date: p.endDate ? new Date(p.endDate).toISOString() : null,
  description: JSON.stringify({
    employeeId: p.employeeId, accountType: p.accountType, riskLevel: p.riskLevel, riskScore: p.riskScore,
    dataClassification: p.dataClassification, location: p.location, workArrangement: p.workArrangement,
    authMethod: p.authMethod, pamVault: p.pamVault, vpnAccess: p.vpnAccess,
    mfa: p.mfa, lastAccessReview: p.lastAccessReview, nextReviewDue: p.nextReviewDue,
    accessReviewStatus: p.accessReviewStatus, backgroundCheck: p.backgroundCheck,
    ndaSigned: p.ndaSigned, lastLogin: p.lastLogin, lastLoginIp: p.lastLoginIp,
    lastLoginGeo: p.lastLoginGeo, anomalousActivity: p.anomalousActivity,
    createdSource: p.createdSource, lastModifiedBy: p.lastModifiedBy,
    assignedDevices: p.assignedDevices, softwareLicences: p.softwareLicences,
    linkedPolicies: p.linkedPolicies, vendorOrg: p.vendorOrg, openIncidents: p.openIncidents,
    auditLog: p.auditLog, complianceTraining: p.complianceTraining,
    onboardingComplete: p.onboardingComplete, offboardingDate: p.offboardingDate,
    lastPasswordChange: p.lastPasswordChange,
    joinDate: p.joinDate, transferDate: p.transferDate,
    exitDate: p.exitDate, offboardingStatus: p.offboardingStatus,
    roles: p.roles, groups: p.groups, privilegedAccess: p.privilegedAccess,
    assetOwner: p.assetOwner, reviewer: p.reviewer, reviewFrequency: p.reviewFrequency,
    evidenceAttachments: p.evidenceAttachments, exceptions: p.exceptions, findings: p.findings,
  }),
});

/* ===== COMPONENT ===== */
const PeopleGRC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isSuperAdmin = user?.roles?.some(r => r === 'super_admin');
  const [people, setPeople] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPerson, setSelectedPerson] = useState<any>(null);

  const [filters, setFilters] = useState<Record<string, string>>({});
  const [search, setSearch] = useState('');
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [evidenceForm, setEvidenceForm] = useState({ url: '', type: 'Per-user status report', notes: '' });
  const [showEditModal, setShowEditModal] = useState(false);
  const [editPerson, setEditPerson] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);

  const fetchReviews = async (personId: number) => {
    try {
      const res = await api.get(`/api/people-assets/${personId}/reviews`);
      setReviews(res.data || []);
    } catch {
      setReviews([]);
    }
  };

  const handleReview = async (person: any) => {
    if (!window.confirm(`Record an access review for ${person.firstName} ${person.lastName}?`)) return;
    try {
      await api.post(`/api/people-assets/${person.id}/review`);
      const personRes = await api.get(`/api/people-assets/${person.id}`);
      const updated = apiToPerson(personRes.data);
      setPeople(prev => prev.map(p => p.id === person.id ? updated : p));
      setSelectedPerson(updated);
      fetchReviews(person.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record review');
    }
  };

  useEffect(() => {
    if (selectedPerson) fetchReviews(selectedPerson.id);
  }, [selectedPerson]);

  useEffect(() => {
    const fetchPeople = async () => {
      try {
        const res = await api.get('/api/people-assets/');
        const apiPeople = (res.data || []).map(apiToPerson);
        const mockByEmail: Record<string, any> = {};
        mockPeople.forEach(m => { mockByEmail[m.email] = m; });
        const merged = apiPeople.map((ap: any) => mockByEmail[ap.email] ? { ...ap, ...mockByEmail[ap.email], id: ap.id } : ap);
        setPeople(merged);
      } catch {
        setPeople([...mockPeople]);
      }
      setLoading(false);
    };
    fetchPeople();
  }, []);

  const toggleFilter = (key: string, value: string) => {
    setFilters(prev => prev[key] === value ? { ...prev, [key]: '' } : { ...prev, [key]: value });
  };

  const clearFilter = (key: string) => {
    setFilters(prev => ({ ...prev, [key]: '' }));
  };

  const filtered = useMemo(() => {
    let data = [...people];
    if (search) {
      const q = search.toLowerCase();
      data = data.filter(p => p.firstName.toLowerCase().includes(q) || p.lastName.toLowerCase().includes(q) || p.email.toLowerCase().includes(q) || p.employeeId.toLowerCase().includes(q));
    }
    if (filters.personType) data = data.filter(p => p.personType === filters.personType);
    if (filters.accountType) data = data.filter(p => p.accountType === filters.accountType);
    if (filters.department) data = data.filter(p => p.department === filters.department);
    if (filters.status) data = data.filter(p => p.status === filters.status);
    if (filters.riskLevel) data = data.filter(p => p.riskLevel === filters.riskLevel);
    if (filters.mfaStatus) data = data.filter(p => mfaStatusValue(p.mfa) === filters.mfaStatus);
    if (filters.mfaMethod) data = data.filter(p => p.mfa.method === filters.mfaMethod);
    return data;
  }, [people, search, filters]);

  const handleEvidenceAdd = () => {
    if (!selectedPerson) return;
    const newEvidence = {
      id: 'ev-' + Date.now(),
      type: evidenceForm.type,
      url: evidenceForm.url,
      uploadedDate: new Date().toISOString().split('T')[0],
      notes: evidenceForm.notes,
    };
    selectedPerson.mfa.evidence.push(newEvidence);
    setSelectedPerson({ ...selectedPerson });
    setShowEvidenceModal(false);
    setEvidenceForm({ url: '', type: 'Per-user status report', notes: '' });
  };

  const mfaControlStatus = (mfa: any) => {
    if (!mfa.enrolled && !mfa.exceptionGranted) return 'Non-compliant';
    if (!mfa.enrolled && mfa.exceptionGranted) return 'Partially compliant';
    if (mfa.method === 'SMS' || mfa.method === 'Email OTP') return 'Partially compliant';
    return 'Compliant';
  };

  const show = (v: any) => v !== null && v !== undefined && v !== '' && v !== '-' && v !== 'N/A' && v !== 'Never' && v !== 'Not completed' && v !== 'Not enrolled';

  const Field = ({ label, value, primary }: { label: string; value: any; primary?: boolean }) => (
    <div style={{ borderLeft: primary ? '3px solid var(--primary)' : undefined, paddingLeft: primary ? 8 : 0, display: 'flex', flexDirection: 'column', gap: 2, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.3, fontWeight: 600 }}>{label}</span>
      <span style={{ fontSize: 13 }}>{value}</span>
    </div>
  );

  const StatusBadge = ({ status }: { status: string }) => {
    const colorMap: Record<string, string> = { Active: '#059669', Suspended: '#d97706', Offboarding: '#dc2626', Inactive: '#6b7280' };
    const c = colorMap[status] || '#6b7280';
    return (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.3, fontWeight: 600 }}>Status</span>
        <span style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: '999px', fontSize: 11, fontWeight: 600, color: c, background: `${c}15` }}>{status}</span>
      </div>
    );
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      {/* PAGE HEADER */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People Assets</p>
          <h1>People Assets</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-primary" onClick={() => navigate('/assets/people/new')}>
            <i className="ti ti-plus"></i> Add Person
          </button>
          <button className="btn btn-outline" onClick={() => navigate('/assets/people/import')}>
            <i className="ti ti-file-spreadsheet"></i> Import CSV
          </button>
          <button className="btn btn-outline" onClick={() => navigate('/assets/people/integrations')}>
            <i className="ti ti-plug-connected"></i> Integrations
          </button>
        </div>
      </div>



      {/* FILTER BAR */}
      <div className="card" style={{ padding: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: '1 1 200px' }}>
            <i className="ti ti-search" style={{ position: 'absolute', left: '0.625rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 16 }}></i>
            <input className="form-control" style={{ paddingLeft: '2rem' }} placeholder="Search by name, email, or ID..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <select className="form-control" style={{ width: 'auto', minWidth: '140px' }} value={filters.personType || ''} onChange={e => toggleFilter('personType', e.target.value)}>
            <option value="">Person Type</option>
            {PERSON_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '140px' }} value={filters.department || ''} onChange={e => toggleFilter('department', e.target.value)}>
            <option value="">Department</option>
            {DEPARTMENTS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '120px' }} value={filters.mfaMethod || ''} onChange={e => toggleFilter('mfaMethod', e.target.value)}>
            <option value="">MFA Method</option>
            {MFA_METHODS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="form-control" style={{ width: 'auto', minWidth: '120px' }} value={filters.status || ''} onChange={e => toggleFilter('status', e.target.value)}>
            <option value="">Status</option>
            {STATUSES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

      </div>

      {/* TABLE */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ minWidth: '220px' }}>Name</th>
                <th>Person Type</th>
                <th>Account Type</th>
                <th>Department</th>
                <th>Status</th>
                <th style={{ width: '140px' }}>MFA</th>
                <th>Last Review</th>
                <th style={{ width: '80px' }}></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}><i className="ti ti-loader" style={{ fontSize: 24 }}></i><br />Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>No matching people found.</td></tr>
              ) : (
                  filtered.map(person => {
                  const pt = personTypeBadge(person.personType);
                  const at = accountTypeBadge(person.accountType);
                  const st = statusBadge(person.status);
                  return (
                    <tr key={person.id} style={{ cursor: 'pointer' }} onClick={() => { setSelectedPerson(person); }}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                          <div style={{ width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 11, fontWeight: 700, flexShrink: 0, background: avatarBg(person.firstName + person.lastName) }}>
                            {initials(person.firstName, person.lastName)}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600 }}>{person.firstName} {person.lastName}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{person.email}</div>
                          </div>
                        </div>
                      </td>
                      <td><span style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: '999px', fontSize: 11, fontWeight: 600, color: pt.color, background: pt.color + '15' }}>{pt.text}</span></td>
                      <td><span style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: '999px', fontSize: 11, fontWeight: 600, color: at.color, background: at.color + '15' }}>{at.text}</span></td>
                      <td>{person.department}</td>
                      <td><span style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: '999px', fontSize: 11, fontWeight: 600, color: st.color, background: st.color + '15' }}>{st.text}</span></td>
                      <td>
                        {(() => {
                          const cfg = mfaBadgeConfig(person.mfa);
                          const warnings: string[] = [];
                          if (person.mfa.lastVerifiedDate && daysAgo(person.mfa.lastVerifiedDate) > 30) warnings.push('Verification outdated');
                          if (person.mfa.exceptionGranted && person.mfa.exceptionExpiryDate && daysAgo(person.mfa.exceptionExpiryDate) > -7) warnings.push('Exception expiring');
                          if (person.mfa.enrolled && (person.mfa.method === 'SMS' || person.mfa.method === 'Email OTP')) warnings.push('Weak method');
                          return <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <span style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: '999px', fontSize: 11, fontWeight: 600, color: cfg.color, backgroundColor: cfg.color + '18', whiteSpace: 'nowrap' }} title={`MFA: ${person.mfa.method || 'None'}`}>{cfg.text}</span>
                            {warnings.map(w => <span key={w} style={{ display: 'inline-flex', color: '#d97706' }} title={w}><i className={`ti ti-${w === 'Verification outdated' ? 'clock' : 'alert-triangle'}`} style={{ fontSize: 14 }}></i></span>)}
                          </div>;
                        })()}
                      </td>
                      <td style={{ fontSize: 12, color: person.lastAccessReview ? 'var(--text-muted)' : '#d97706' }}>
                        {person.lastAccessReview ? new Date(person.lastAccessReview).toLocaleDateString() : 'Never'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 2 }} onClick={e => e.stopPropagation()}>
                          <button className="btn btn-ghost" style={{ padding: '0.25rem' }} title="View" onClick={() => { setSelectedPerson(person); }}>
                            <i className="ti ti-eye" style={{ fontSize: 16 }}></i>
                          </button>
                          <button className="btn btn-ghost" style={{ padding: '0.25rem' }} title="Edit" onClick={() => { setEditPerson(person); setShowEditModal(true); }}>
                            <i className="ti ti-edit" style={{ fontSize: 16 }}></i>
                          </button>
                          <button className="btn btn-ghost" style={{ padding: '0.25rem', color: '#dc2626' }} title="Delete" onClick={(e) => { e.stopPropagation(); setDeleteConfirm(person); }}>
                            <i className="ti ti-trash" style={{ fontSize: 16 }}></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* DRAWER */}
      {selectedPerson && (
        <>
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100 }} onClick={() => setSelectedPerson(null)}></div>
          <div style={{ position: 'fixed', top: 0, right: 0, width: 480, maxWidth: '100vw', height: '100vh', background: 'var(--surface)', borderLeft: '1px solid var(--border)', zIndex: 101, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 40, height: 40, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0, background: avatarBg(selectedPerson.firstName + selectedPerson.lastName) }}>
                  {initials(selectedPerson.firstName, selectedPerson.lastName)}
                </div>
                <div>
                  <h3 style={{ fontSize: 16, margin: 0, color: 'var(--text-main)' }}>{selectedPerson.firstName} {selectedPerson.lastName}</h3>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>{selectedPerson.jobTitle} · {selectedPerson.department}</p>
                </div>
              </div>
              <button className="btn btn-ghost" style={{ padding: '0.25rem' }} onClick={() => setSelectedPerson(null)}>
                <i className="ti ti-x" style={{ fontSize: 20 }}></i>
              </button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 16, border: '1px solid var(--border)', borderRadius: 'var(--radius)', marginBottom: 16 }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 16, fontWeight: 700, flexShrink: 0, background: avatarBg(selectedPerson.firstName + selectedPerson.lastName) }}>
                  {initials(selectedPerson.firstName, selectedPerson.lastName)}
                </div>
                <div>
                  <h2 style={{ fontSize: 18, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                    {selectedPerson.firstName} {selectedPerson.lastName}
                    <span style={{ width: 8, height: 8, borderRadius: '50%', display: 'inline-block', background: (selectedPerson.status || selectedPerson.employmentStatus) === 'Active' ? '#059669' : (selectedPerson.status || selectedPerson.employmentStatus) === 'Suspended' ? '#d97706' : '#dc2626' }}></span>
                  </h2>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '2px 0 0', display: 'flex', alignItems: 'center', gap: 8 }}>
                    {selectedPerson.jobTitle} · {selectedPerson.department}
                  </p>
                </div>
              </div>

              <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}><i className="ti ti-user" style={{ fontSize: 12 }}></i> Identity</h4>
              <div style={{ display: 'grid', gap: 12 }}>
                {show(selectedPerson.firstName) && <Field label="First Name" value={selectedPerson.firstName} />}
                {show(selectedPerson.lastName) && <Field label="Last Name" value={selectedPerson.lastName} />}
                {show(selectedPerson.email) && <Field label="Work Email" value={selectedPerson.email} primary />}
                {show(selectedPerson.employeeId) && <Field label="Employee / User ID" value={selectedPerson.employeeId} primary />}
                {show(selectedPerson.department) && <Field label="Department" value={selectedPerson.department} />}
                {show(selectedPerson.jobTitle) && <Field label="Job Title" value={selectedPerson.jobTitle} />}
                {show(selectedPerson.employmentType) && <Field label="Employment Type" value={selectedPerson.employmentType} />}
                {show(selectedPerson.manager) && <Field label="Manager" value={selectedPerson.manager} />}
                {show(selectedPerson.location) && <Field label="Location" value={selectedPerson.location} />}
                {show(selectedPerson.startDate) && <Field label="Start Date" value={selectedPerson.startDate} />}
                {show(selectedPerson.endDate) && <Field label="Termination Date" value={selectedPerson.endDate} />}
              </div>

              <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, margin: '16px 0 8px' }}><i className="ti ti-shield" style={{ fontSize: 12 }}></i> Security & Access</h4>
              <div style={{ display: 'grid', gap: 12 }}>
                {show(selectedPerson.status) && <StatusBadge status={selectedPerson.status} />}
                {show(selectedPerson.privilegedAccess) && <Field label="Privileged Access" value={selectedPerson.privilegedAccess ? 'Granted' : 'Standard'} />}
                {selectedPerson.mfa?.enrolled && <Field label="MFA Enrolled" value={selectedPerson.mfa.enrolled ? 'Yes' : 'No'} />}
                {show(selectedPerson.mfa?.method) && <Field label="MFA Method" value={selectedPerson.mfa.method} />}
                {show(selectedPerson.lastLogin) && <Field label="Last Login" value={selectedPerson.lastLogin} />}
                {show(selectedPerson.lastPasswordChange) && <Field label="Password Changed" value={selectedPerson.lastPasswordChange} />}
                {show(selectedPerson.lastAccessReview) && <Field label="Last Access Review" value={selectedPerson.lastAccessReview} />}
                {show(selectedPerson.nextReviewDue) && <Field label="Next Review Due" value={selectedPerson.nextReviewDue} />}
              </div>

              {selectedPerson.groups?.length > 0 && (
              <div>
                <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, margin: '16px 0 8px' }}><i className="ti ti-users" style={{ fontSize: 12 }}></i> Groups</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {selectedPerson.groups.map((g: string, i: number) => (
                    <span key={i} style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 500, background: 'var(--background)', border: '1px solid var(--border)' }}>{g}</span>
                  ))}
                </div>
              </div>)}

              <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, margin: '16px 0 8px' }}><i className="ti ti-shield-check" style={{ fontSize: 12 }}></i> Access Review</h4>
              <div style={{ display: 'grid', gap: 12 }}>
                <Field label="Last Access Review" value={selectedPerson.lastAccessReview ? new Date(selectedPerson.lastAccessReview).toLocaleString() : 'Never reviewed'} />
                {show(selectedPerson.nextReviewDue) && <Field label="Next Review Due" value={selectedPerson.nextReviewDue} />}
                {isSuperAdmin && (
                  <div style={{ paddingTop: 8 }}>
                    <button className="btn btn-outline" style={{ color: '#059669', borderColor: '#059669', width: '100%' }} onClick={() => handleReview(selectedPerson)}>
                      <i className="ti ti-shield-check" style={{ fontSize: 14 }}></i> Record Review
                    </button>
                  </div>
                )}
                {reviews.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.3 }}>Review History</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {reviews.map(r => (
                        <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', background: 'var(--background)', borderRadius: 6, fontSize: 12 }}>
                          <span style={{ fontWeight: 500 }}>{new Date(r.reviewed_at).toLocaleString()}</span>
                          <span style={{ color: 'var(--text-muted)' }}>by user #{r.reviewed_by}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, margin: '16px 0 8px' }}><i className="ti ti-refresh" style={{ fontSize: 12 }}></i> Sync Metadata</h4>
              <div style={{ display: 'grid', gap: 12 }}>
                {show(selectedPerson.identityProvider) && <Field label="Identity Provider" value={selectedPerson.identityProvider} />}
                {show(selectedPerson.syncedAt) && <Field label="Last Synced" value={selectedPerson.syncedAt} />}
                {show(selectedPerson.createdAt) && <Field label="Okta Created" value={selectedPerson.createdAt} />}
              </div>

            </div>
          </div>
        </>
      )}

      {/* EVIDENCE UPLOAD MODAL */}
      {showEvidenceModal && selectedPerson && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 210, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setShowEvidenceModal(false)}>
          <div style={{ background: 'var(--surface)', borderRadius: 12, width: 480, maxWidth: '95vw', padding: '20px 24px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 style={{ fontSize: 16, margin: 0 }}>Add MFA Evidence</h3>
              <button className="btn btn-ghost" style={{ padding: '0.25rem' }} onClick={() => { setShowEvidenceModal(false); setEvidenceForm({ url: '', type: 'Per-user status report', notes: '' }); }}><i className="ti ti-x" style={{ fontSize: 20 }}></i></button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Evidence Type</label>
                <select className="form-control" value={evidenceForm.type} onChange={e => setEvidenceForm(prev => ({ ...prev, type: e.target.value }))}>{MFA_EVIDENCE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}</select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>URL / Reference</label>
                <input className="form-control" value={evidenceForm.url} onChange={e => setEvidenceForm(prev => ({ ...prev, url: e.target.value }))} placeholder="https://admin-console.example.com/..." />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Notes</label>
                <textarea className="form-control" style={{ minHeight: 60, resize: 'vertical' }} value={evidenceForm.notes} onChange={e => setEvidenceForm(prev => ({ ...prev, notes: e.target.value }))} placeholder="Optional notes..." />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn btn-ghost" onClick={() => { setShowEvidenceModal(false); setEvidenceForm({ url: '', type: 'Per-user status report', notes: '' }); }}>Cancel</button>
              <button className="btn btn-primary" onClick={handleEvidenceAdd} disabled={!evidenceForm.type}>Add Evidence</button>
            </div>
          </div>
        </div>
      )}


      {/* EDIT MODAL */}
      {showEditModal && editPerson && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 210, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setShowEditModal(false)}>
          <div style={{ background: 'var(--surface)', borderRadius: 12, width: 680, maxWidth: '95vw', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px 0' }}>
              <h2 style={{ fontSize: 18, color: 'var(--text-main)' }}>Edit Person</h2>
              <button className="btn btn-ghost" style={{ padding: '0.25rem' }} onClick={() => setShowEditModal(false)}><i className="ti ti-x" style={{ fontSize: 20 }}></i></button>
            </div>
            <EditPersonForm person={editPerson} onSave={async (updated: any) => {
              try { await api.patch(`/api/people-assets/${updated.id}`, toApiFormat(updated)); } catch {}
              setPeople(prev => prev.map(p => p.id === updated.id ? updated : p));
              if (selectedPerson?.id === updated.id) setSelectedPerson(updated);
              setShowEditModal(false);
              setEditPerson(null);
            }} onCancel={() => { setShowEditModal(false); setEditPerson(null); }} />
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION */}
      {deleteConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setDeleteConfirm(null)}>
          <div style={{ background: 'var(--surface)', borderRadius: 12, width: 400, maxWidth: '90vw', padding: '24px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#dc262615', color: '#dc2626' }}>
                <i className="ti ti-alert-triangle" style={{ fontSize: 20 }}></i>
              </div>
              <div>
                <h3 style={{ fontSize: 16, margin: 0, color: 'var(--text-main)' }}>Delete Person</h3>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '4px 0 0' }}>This action cannot be undone.</p>
              </div>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text-main)', marginBottom: 20 }}>
              Are you sure you want to delete <strong>{deleteConfirm.firstName} {deleteConfirm.lastName}</strong> ({deleteConfirm.employeeId})?
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button className="btn btn-ghost" onClick={() => setDeleteConfirm(null)}>Cancel</button>
              <button className="btn" style={{ background: '#dc2626', color: '#fff' }} onClick={async () => {
                try { await api.delete(`/api/people-assets/${deleteConfirm.id}`); } catch {}
                setPeople(prev => prev.filter(p => p.id !== deleteConfirm.id));
                if (selectedPerson?.id === deleteConfirm.id) setSelectedPerson(null);
                setDeleteConfirm(null);
              }}><i className="ti ti-trash" style={{ fontSize: 14 }}></i> Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/* ===== EDIT PERSON FORM ===== */
const EditPersonForm = ({ person, onSave, onCancel }: { person: any; onSave: (p: any) => void; onCancel: () => void }) => {
  const [form, setForm] = useState({
    firstName: person.firstName || '',
    lastName: person.lastName || '',
    email: person.email || '',
    employeeId: person.employeeId || '',
    personType: person.personType || 'Employee',
    department: person.department || 'Engineering',
    jobTitle: person.jobTitle || '',
    manager: person.manager || '',
    location: person.location || '',
    workArrangement: person.workArrangement || 'On-site',
    authMethod: person.authMethod || 'SSO',
    status: person.status || 'Active',
    startDate: person.startDate || '',
    endDate: person.endDate || '',
    joinDate: person.joinDate || '',
    transferDate: person.transferDate || '',
    exitDate: person.exitDate || '',
    offboardingStatus: person.offboardingStatus || 'N/A',
    mfaEnrolled: person.mfa?.enrolled ?? true,
    mfaMethod: person.mfa?.method || 'TOTP',
    mfaEnforcementDate: person.mfa?.enrollmentDate || '',
    mfaVerificationSource: person.mfa?.verificationSource || 'Okta API',
    mfaException: person.mfa?.exceptionGranted || false,
    mfaExceptionReason: person.mfa?.exceptionReason || '',
    mfaExceptionApprovedBy: person.mfa?.exceptionApprovedBy || '',
    mfaExceptionExpiryDate: person.mfa?.exceptionExpiryDate || '',
    mfaEvidenceUrl: '',
    mfaEvidenceType: 'Per-user status report',
    lastPasswordChange: person.lastPasswordChange || '',
    backgroundCheck: person.backgroundCheck || 'Completed',
    nda: person.ndaSigned || false,
    securityTrainingStatus: person.complianceTraining?.securityAwareness || 'N/A',
    acceptableUseAgreed: person.complianceTraining?.aup === 'Complete' ? 'Yes' : 'No',
    dataClassification: person.dataClassification || 'Internal',
    vpnAccess: person.vpnAccess || false,
    pamVault: person.pamVault || false,
    privilegedAccess: person.privilegedAccess || false,
    roles: (person.roles || []).join(', '),
    groups: (person.groups || []).join(', '),
    lastLogin: person.lastLogin || '',
    lastAccessReviewDate: person.lastAccessReview || '',
    assetOwner: person.assetOwner || '',
    reviewer: person.reviewer || '',
    reviewFrequency: person.reviewFrequency || 'Quarterly',
    evidenceAttachments: (person.evidenceAttachments || []).join(', '),
    exceptions: (person.exceptions || []).join(', '),
    findings: (person.findings || []).join(', '),
  });

  const update = (field: string, value: string | boolean) => setForm(prev => ({ ...prev, [field]: value }));

  const handleSave = () => {
    const rolesArr = form.roles.split(',').map(s => s.trim()).filter(Boolean);
    const groupsArr = form.groups.split(',').map(s => s.trim()).filter(Boolean);
    const evidenceArr = form.evidenceAttachments.split(',').map(s => s.trim()).filter(Boolean);
    const exceptionsArr = form.exceptions.split(',').map(s => s.trim()).filter(Boolean);
    const findingsArr = form.findings.split(',').map(s => s.trim()).filter(Boolean);
    const aupComplete = form.acceptableUseAgreed === 'Yes';
    const updated = {
      ...person,
      firstName: form.firstName,
      lastName: form.lastName,
      displayName: `${form.firstName} ${form.lastName}`.trim(),
      email: form.email,
      employeeId: form.employeeId,
      personType: form.personType,
      department: form.department,
      jobTitle: form.jobTitle || '',
      manager: form.manager || '',
      location: form.location || '',
      workArrangement: form.workArrangement,
      authMethod: form.authMethod,
      status: form.status,
      startDate: form.startDate,
      endDate: form.endDate,
      joinDate: form.joinDate,
      transferDate: form.transferDate,
      exitDate: form.exitDate,
      offboardingStatus: form.offboardingStatus,
      vpnAccess: form.vpnAccess,
      pamVault: form.pamVault,
      privilegedAccess: form.privilegedAccess,
      roles: rolesArr,
      groups: groupsArr,
      lastLogin: form.lastLogin,
      lastAccessReview: form.lastAccessReviewDate,
      assetOwner: form.assetOwner,
      reviewer: form.reviewer,
      reviewFrequency: form.reviewFrequency,
      evidenceAttachments: evidenceArr,
      exceptions: exceptionsArr,
      findings: findingsArr,
      backgroundCheck: form.backgroundCheck,
      ndaSigned: form.nda,
      lastPasswordChange: form.lastPasswordChange,
      dataClassification: form.dataClassification,
      lastModified: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
      lastModifiedBy: form.firstName + ' ' + form.lastName,
      complianceTraining: {
        ...((person.complianceTraining) || {}),
        securityAwareness: form.securityTrainingStatus,
        aup: aupComplete ? 'Complete' : 'N/A',
      },
      mfa: {
        ...person.mfa,
        enrolled: form.mfaEnrolled,
        enforced: form.mfaEnrolled,
        method: form.mfaEnrolled ? form.mfaMethod : 'None',
        enrollmentDate: form.mfaEnforcementDate || person.mfa?.enrollmentDate || '',
        verificationSource: form.mfaVerificationSource || '',
        exceptionGranted: form.mfaException,
        exceptionReason: form.mfaExceptionReason || '',
        exceptionApprovedBy: form.mfaExceptionApprovedBy || '',
        exceptionExpiryDate: form.mfaExceptionExpiryDate || '',
      },
    };
    if (form.mfaEvidenceUrl) {
      updated.mfa.evidence = [
        ...(updated.mfa.evidence || []),
        { id: 'ev-' + Date.now(), type: form.mfaEvidenceType, url: form.mfaEvidenceUrl, uploadedDate: new Date().toISOString().split('T')[0], notes: '' },
      ];
    }
    onSave(updated);
  };

  const OFFBOARDING_STATUSES = ['N/A', 'Not Started', 'In Progress', 'Completed'];
  const REVIEW_FREQUENCIES = ['Monthly', 'Quarterly', 'Annually', 'Ad-hoc'];
  const TRAINING_STATUSES = ['Complete', 'Due', 'Overdue', 'N/A'];

  return (
    <div style={{ padding: '20px 24px', overflowY: 'auto' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}><i className="ti ti-user" style={{ fontSize: 12 }}></i> Identity</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>First Name</label>
              <input className="form-control" value={form.firstName} onChange={e => update('firstName', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Last Name</label>
              <input className="form-control" value={form.lastName} onChange={e => update('lastName', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Email</label>
              <input className="form-control" value={form.email} onChange={e => update('email', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Employee ID</label>
              <input className="form-control" value={form.employeeId} onChange={e => update('employeeId', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Person Type</label>
              <select className="form-control" value={form.personType} onChange={e => update('personType', e.target.value)}>{mockPersonTypes.map(t => <option key={t} value={t}>{t}</option>)}</select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Department</label>
              <select className="form-control" value={form.department} onChange={e => update('department', e.target.value)}>{mockDepartments.map(t => <option key={t} value={t}>{t}</option>)}</select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Job Title</label>
              <input className="form-control" value={form.jobTitle} onChange={e => update('jobTitle', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Manager</label>
              <input className="form-control" value={form.manager} onChange={e => update('manager', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Location</label>
              <input className="form-control" value={form.location} onChange={e => update('location', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Work Arrangement</label>
              <select className="form-control" value={form.workArrangement} onChange={e => update('workArrangement', e.target.value)}><option>On-site</option><option>Hybrid</option><option>Remote</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Auth Method</label>
              <select className="form-control" value={form.authMethod} onChange={e => update('authMethod', e.target.value)}><option>SSO</option><option>SSO + MFA</option><option>Password</option><option>Password Only</option><option>Token-based</option></select>
            </div>
          </div>
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />
        <div>
          <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}><i className="ti ti-file-text" style={{ fontSize: 12 }}></i> Compliance</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Asset Owner</label>
              <input className="form-control" value={form.assetOwner} onChange={e => update('assetOwner', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Reviewer</label>
              <input className="form-control" value={form.reviewer} onChange={e => update('reviewer', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Review Frequency</label>
              <select className="form-control" value={form.reviewFrequency} onChange={e => update('reviewFrequency', e.target.value)}>{REVIEW_FREQUENCIES.map(t => <option key={t} value={t}>{t}</option>)}</select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>MFA Method</label>
              <select className="form-control" value={form.mfaMethod} onChange={e => update('mfaMethod', e.target.value)}>{mockMfaMethods.map(t => <option key={t} value={t}>{t}</option>)}</select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Evidence Attachments (comma-separated URLs)</label>
              <input className="form-control" value={form.evidenceAttachments} onChange={e => update('evidenceAttachments', e.target.value)} placeholder="https://example.com/evidence, https://..." />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Exceptions (comma-separated)</label>
              <input className="form-control" value={form.exceptions} onChange={e => update('exceptions', e.target.value)} placeholder="e.g. Exception for legacy system access" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Findings (comma-separated URLs)</label>
              <input className="form-control" value={form.findings} onChange={e => update('findings', e.target.value)} placeholder="https://example.com/finding, https://..." />
            </div>
          </div>
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />
        <div>
          <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}><i className="ti ti-calendar-stats" style={{ fontSize: 12 }}></i> Life Cycle</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Status</label>
              <select className="form-control" value={form.status} onChange={e => update('status', e.target.value)}><option>Active</option><option>Suspended</option><option>Offboarding</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Start Date</label>
              <input className="form-control" type="date" value={form.startDate} onChange={e => update('startDate', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>End Date</label>
              <input className="form-control" type="date" value={form.endDate} onChange={e => update('endDate', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Join Date</label>
              <input className="form-control" type="date" value={form.joinDate} onChange={e => update('joinDate', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Transfer Date</label>
              <input className="form-control" type="date" value={form.transferDate} onChange={e => update('transferDate', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Exit Date</label>
              <input className="form-control" type="date" value={form.exitDate} onChange={e => update('exitDate', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Offboarding Status</label>
              <select className="form-control" value={form.offboardingStatus} onChange={e => update('offboardingStatus', e.target.value)}>{OFFBOARDING_STATUSES.map(t => <option key={t} value={t}>{t}</option>)}</select>
            </div>
          </div>
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />
        <div>
          <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}><i className="ti ti-shield-lock" style={{ fontSize: 12 }}></i> Access</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>VPN Access</label>
              <select className="form-control" value={String(form.vpnAccess)} onChange={e => update('vpnAccess', e.target.value === 'true')}><option value="true">Enabled</option><option value="false">Disabled</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>PAM Vault</label>
              <select className="form-control" value={String(form.pamVault)} onChange={e => update('pamVault', e.target.value === 'true')}><option value="true">Enabled</option><option value="false">Disabled</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Privileged Access</label>
              <select className="form-control" value={String(form.privilegedAccess)} onChange={e => update('privilegedAccess', e.target.value === 'true')}><option value="true">Granted</option><option value="false">Standard</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Last Login</label>
              <input className="form-control" type="date" value={form.lastLogin} onChange={e => update('lastLogin', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Last Access Review Date</label>
              <input className="form-control" type="date" value={form.lastAccessReviewDate} onChange={e => update('lastAccessReviewDate', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Roles (comma-separated)</label>
              <input className="form-control" value={form.roles} onChange={e => update('roles', e.target.value)} placeholder="e.g. Admin, Developer, Auditor" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Groups (comma-separated)</label>
              <input className="form-control" value={form.groups} onChange={e => update('groups', e.target.value)} placeholder="e.g. Engineering, Security Team" />
            </div>
          </div>
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 0 }} />
        <div>
          <h4 style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}><i className="ti ti-fingerprint" style={{ fontSize: 12 }}></i> Security</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>MFA Enabled</label>
              <select className="form-control" value={String(form.mfaEnrolled)} onChange={e => update('mfaEnrolled', e.target.value === 'true')}><option value="true">Yes</option><option value="false">No</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Last Password Change</label>
              <input className="form-control" type="date" value={form.lastPasswordChange} onChange={e => update('lastPasswordChange', e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Background Check Status</label>
              <select className="form-control" value={form.backgroundCheck} onChange={e => update('backgroundCheck', e.target.value)}><option>Completed</option><option>Pending</option><option>Not Required</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>NDA Signed</label>
              <select className="form-control" value={form.nda ? 'Yes' : 'No'} onChange={e => update('nda', e.target.value === 'Yes')}><option value="Yes">Yes</option><option value="No">No</option></select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Security Training Status</label>
              <select className="form-control" value={form.securityTrainingStatus} onChange={e => update('securityTrainingStatus', e.target.value)}>{TRAINING_STATUSES.map(t => <option key={t} value={t}>{t}</option>)}</select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)' }}>Acceptable Use Agreement Signed</label>
              <select className="form-control" value={form.acceptableUseAgreed} onChange={e => update('acceptableUseAgreed', e.target.value)}><option>Yes</option><option>No</option></select>
            </div>
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={handleSave}><i className="ti ti-device-floppy" style={{ fontSize: 14 }}></i> Save Changes</button>
      </div>
    </div>
  );
};

const mockPersonTypes = ['Employee', 'Contractor', 'Consultant', 'Intern', 'Temp Staff', 'Vendor User', 'Third-Party User', 'Service Account', 'Shared Account', 'Privileged Account', 'Administrator', 'Developer', 'Security Personnel'];
const mockDepartments = ['Engineering', 'Security', 'Finance', 'HR', 'Sales', 'Marketing', 'Legal', 'Operations', 'Product', 'IT'];
const mockAccountTypes = ['Standard', 'Privileged', 'Service', 'Shared', 'Admin'];
const mockRiskLevels = ['Low', 'Medium', 'High'];
const mockMfaMethods = ['FIDO2', 'TOTP', 'Push', 'SMS', 'Email OTP', 'None'];
const mockEvidenceTypes = ['Policy screenshot', 'Per-user status report', 'Sign-in log', 'Admin console export', 'Manual upload'];

export default PeopleGRC;
