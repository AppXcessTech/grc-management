import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const DEPARTMENTS = ['Engineering', 'Security', 'Finance', 'HR', 'Sales', 'Marketing', 'Legal', 'Operations', 'Product', 'IT'];
const EMPLOYMENT_TYPES = ['Employee', 'Contractor', 'Consultant', 'Intern', 'Temp Staff', 'Vendor User', 'Third-Party User', 'Service Account', 'Shared Account', 'Privileged Account', 'Administrator', 'Developer', 'Security Personnel'];
const BG_CHECK_STATUSES = ['Completed', 'Pending', 'Not Required'];
const TRAINING_STATUSES = ['Complete', 'Due', 'Overdue', 'N/A'];
const STATUSES = ['Active', 'Suspended', 'Offboarding'];
const OFFBOARDING_STATUSES = ['N/A', 'Not Started', 'In Progress', 'Completed'];
const REVIEW_FREQUENCIES = ['Monthly', 'Quarterly', 'Annually', 'Ad-hoc'];
const MFA_METHODS = ['FIDO2', 'TOTP', 'Push', 'SMS', 'Email OTP', 'None'];

const PeopleCreate = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    employeeId: '',
    email: '',
    department: 'Engineering',
    jobTitle: '',
    manager: '',
    employmentType: 'Employee',
    location: '',
    authMethod: 'SSO',
    workArrangement: 'On-site',
    startDate: '',
    endDate: '',
    mfaEnabled: 'No',
    mfaMethod: 'TOTP',
    lastPasswordChange: '',
    bgCheckStatus: 'Not Required',
    ndaSigned: 'No',
    securityTrainingStatus: 'N/A',
    acceptableUseAgreed: 'No',
    status: 'Active',
    joinDate: '',
    transferDate: '',
    exitDate: '',
    offboardingStatus: 'N/A',
    roles: '',
    groups: '',
    privilegedAccess: 'No',
    vpnAccess: 'No',
    pamAccess: 'No',
    lastLogin: '',
    lastAccessReviewDate: '',
    assetOwner: '',
    reviewer: '',
    reviewFrequency: 'Quarterly',
    evidenceAttachments: [] as string[],
    exceptions: '',
    findings: [] as string[],
  });

  const update = (field: string, value: string | number | string[]) => setForm(prev => ({ ...prev, [field]: value }));
  const [evidenceLink, setEvidenceLink] = useState('');
  const [findingLink, setFindingLink] = useState('');
  const evidenceFileRef = useRef<HTMLInputElement>(null);
  const findingFileRef = useRef<HTMLInputElement>(null);

  const uploadFile = async (file: File): Promise<string> => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await api.post('/api/people-assets/upload', fd);
    return res.data.url;
  };

  const handleEvidenceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = await uploadFile(file);
    setForm(prev => ({ ...prev, evidenceAttachments: [...prev.evidenceAttachments, url] }));
    if (e.target) e.target.value = '';
  };

  const handleFindingUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = await uploadFile(file);
    setForm(prev => ({ ...prev, findings: [...prev.findings, url] }));
    if (e.target) e.target.value = '';
  };

  const addEvidenceLink = () => {
    if (!evidenceLink.trim()) return;
    setForm(prev => ({ ...prev, evidenceAttachments: [...prev.evidenceAttachments, evidenceLink.trim()] }));
    setEvidenceLink('');
  };

  const addFindingLink = () => {
    if (!findingLink.trim()) return;
    setForm(prev => ({ ...prev, findings: [...prev.findings, findingLink.trim()] }));
    setFindingLink('');
  };

  const removeEvidenceItem = (idx: number) => {
    setForm(prev => ({ ...prev, evidenceAttachments: prev.evidenceAttachments.filter((_, i) => i !== idx) }));
  };

  const removeFindingItem = (idx: number) => {
    setForm(prev => ({ ...prev, findings: prev.findings.filter((_, i) => i !== idx) }));
  };

  const sections = [
    {
      label: 'Identity', fields: [
        { label: 'Employee ID', key: 'employeeId', type: 'text', col: 1 },
        { label: 'Name', key: 'name', type: 'text', col: 2 },
        { label: 'Email', key: 'email', type: 'text', col: 2 },
        { label: 'Department', key: 'department', type: 'select', options: DEPARTMENTS, col: 1 },
        { label: 'Job Title', key: 'jobTitle', type: 'text', col: 1 },
        { label: 'Manager', key: 'manager', type: 'text', col: 1 },
        { label: 'Employment Type', key: 'employmentType', type: 'select', options: EMPLOYMENT_TYPES, col: 1 },
        { label: 'Auth Method', key: 'authMethod', type: 'select', options: ['SSO', 'SSO + MFA', 'Password', 'Password + MFA', 'LDAP', 'OAuth', 'SAML', 'OpenID'], col: 1 },
        { label: 'Work Arrangement', key: 'workArrangement', type: 'select', options: ['On-site', 'Remote', 'Hybrid'], col: 1 },
        { label: 'Location', key: 'location', type: 'text', col: 1 },
        { label: 'Start Date', key: 'startDate', type: 'date', col: 1 },
        { label: 'End Date', key: 'endDate', type: 'date', col: 1 },
      ],
    },
    {
      label: 'Compliance', fields: [
        { label: 'Asset Owner', key: 'assetOwner', type: 'text', col: 1 },
        { label: 'Reviewer', key: 'reviewer', type: 'text', col: 1 },
        { label: 'MFA Method', key: 'mfaMethod', type: 'select', options: MFA_METHODS, col: 1 },
        { label: 'Review Frequency', key: 'reviewFrequency', type: 'select', options: REVIEW_FREQUENCIES, col: 1 },
        { label: 'Evidence Attachments', key: 'evidenceAttachments', type: 'text', col: 2 },
        { label: 'Exceptions', key: 'exceptions', type: 'text', col: 2 },
        { label: 'Findings', key: 'findings', type: 'text', col: 2 },
      ],
    },
    {
      label: 'Life Cycle', fields: [
        { label: 'Status', key: 'status', type: 'select', options: STATUSES, col: 1 },
        { label: 'Join Date', key: 'joinDate', type: 'date', col: 1 },
        { label: 'Transfer Date', key: 'transferDate', type: 'date', col: 1 },
        { label: 'Exit Date', key: 'exitDate', type: 'date', col: 1 },
        { label: 'Offboarding Status', key: 'offboardingStatus', type: 'select', options: OFFBOARDING_STATUSES, col: 1 },
      ],
    },
    {
      label: 'Access', fields: [
        { label: 'Roles', key: 'roles', type: 'text', col: 2 },
        { label: 'Groups', key: 'groups', type: 'text', col: 2 },
        { label: 'Privileged Access', key: 'privilegedAccess', type: 'select', options: ['Yes', 'No'], col: 1 },
        { label: 'VPN Access', key: 'vpnAccess', type: 'select', options: ['Yes', 'No'], col: 1 },
        { label: 'PAM Access', key: 'pamAccess', type: 'select', options: ['Yes', 'No'], col: 1 },
        { label: 'Last Login', key: 'lastLogin', type: 'date', col: 1 },
        { label: 'Last Access Review Date', key: 'lastAccessReviewDate', type: 'date', col: 1 },
      ],
    },
    {
      label: 'Security', fields: [
        { label: 'MFA Enabled', key: 'mfaEnabled', type: 'select', options: ['Yes', 'No'], col: 1 },
        { label: 'Last Password Change', key: 'lastPasswordChange', type: 'date', col: 1 },
        { label: 'Background Check Status', key: 'bgCheckStatus', type: 'select', options: BG_CHECK_STATUSES, col: 1 },
        { label: 'NDA Signed', key: 'ndaSigned', type: 'select', options: ['Yes', 'No'], col: 1 },
        { label: 'Security Training Status', key: 'securityTrainingStatus', type: 'select', options: TRAINING_STATUSES, col: 1 },
        { label: 'Acceptable Use Agreement Signed', key: 'acceptableUseAgreed', type: 'select', options: ['Yes', 'No'], col: 1 },
      ],
    },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nameParts = form.name.trim().split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || '';
    const mfaOn = form.mfaEnabled === 'Yes';
    const ndaOn = form.ndaSigned === 'Yes';
    const aupOn = form.acceptableUseAgreed === 'Yes';
    const privOn = form.privilegedAccess === 'Yes';
    const vpnOn = form.vpnAccess === 'Yes';
    const pamOn = form.pamAccess === 'Yes';
    const rolesArr = form.roles.split(',').map(s => s.trim()).filter(Boolean);
    const groupsArr = form.groups.split(',').map(s => s.trim()).filter(Boolean);
    const evidenceArr = form.evidenceAttachments;
    const exceptionsArr = form.exceptions.split(',').map(s => s.trim()).filter(Boolean);
    const findingsArr = form.findings;
    const newPerson = {
      id: Date.now(),
      firstName, lastName,
      name: form.name.trim(),
      email: form.email,
      employeeId: form.employeeId,
      department: form.department,
      manager: form.manager,
      personType: form.employmentType,
      location: form.location,
      startDate: form.startDate || '',
      endDate: form.endDate || '',
      mfa: {
        enrolled: mfaOn,
        enforced: mfaOn,
        method: form.mfaMethod,
        enrollmentDate: '',
        lastVerifiedDate: '',
        verificationSource: '',
        exceptionGranted: false,
        exceptionReason: '', exceptionApprovedBy: '', exceptionExpiryDate: '',
        evidence: [],
        notes: '',
      },
      backgroundCheck: form.bgCheckStatus === 'Not Required' ? '' : form.bgCheckStatus,
      ndaSigned: ndaOn,
      lastPasswordChange: form.lastPasswordChange || '',
      complianceTraining: {
        securityAwareness: form.securityTrainingStatus,
        gdpr: 'N/A',
        aup: aupOn ? 'Complete' : 'N/A',
        codeOfConduct: 'N/A',
        phishing: 'N/A',
      },
      roles: rolesArr,
      groups: groupsArr,
      privilegedAccess: privOn,
      vpnAccess: vpnOn,
      pamVault: pamOn,
      lastLogin: form.lastLogin || '',
      lastAccessReview: form.lastAccessReviewDate || '',
      assetOwner: form.assetOwner || '',
      reviewer: form.reviewer || '',
      reviewFrequency: form.reviewFrequency,
      evidenceAttachments: evidenceArr,
      exceptions: exceptionsArr,
      findings: findingsArr,
      employmentStatus: form.status,
      accountType: privOn ? 'Privileged' : 'Standard',
      authMethod: form.authMethod,
      jobTitle: form.jobTitle,
      workArrangement: form.workArrangement,
      status: form.status,
      displayName: form.name.trim(),
      createdAt: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
      lastModified: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
      lastModifiedBy: form.name.trim(),
    };
    try {
      const payload = {
        name: form.name.trim(),
        email: form.email,
        asset_type: form.employmentType,
        department: form.department,
        job_title: '',
        manager: form.manager,
        status: 'Active',
        start_date: form.startDate ? new Date(form.startDate).toISOString() : null,
        end_date: form.endDate ? new Date(form.endDate).toISOString() : null,
        description: JSON.stringify({
          employeeId: form.employeeId,
          jobTitle: form.jobTitle,
          authMethod: form.authMethod,
          workArrangement: form.workArrangement,
          location: form.location,
          mfa: newPerson.mfa,
          backgroundCheck: newPerson.backgroundCheck,
          ndaSigned: ndaOn,
          lastPasswordChange: form.lastPasswordChange || '',
          complianceTraining: newPerson.complianceTraining,
          joinDate: form.joinDate || '',
          transferDate: form.transferDate || '',
          exitDate: form.exitDate || '',
          offboardingStatus: form.offboardingStatus,
          roles: rolesArr,
          groups: groupsArr,
          privilegedAccess: privOn,
          vpnAccess: vpnOn,
          pamVault: pamOn,
          lastLogin: form.lastLogin || '',
          lastAccessReview: form.lastAccessReviewDate || '',
          assetOwner: form.assetOwner || '',
          reviewer: form.reviewer || '',
          reviewFrequency: form.reviewFrequency,
          evidenceAttachments: evidenceArr,
          exceptions: exceptionsArr,
          findings: findingsArr,
        }),
      };
      const res = await api.post('/api/people-assets/', payload);
      navigate('/assets/people');
    } catch {
      navigate('/assets/people');
    }
  };

  const input = (f: any) => {
    const val = (form as any)[f.key];
    if (f.key === 'evidenceAttachments') {
      return (
        <div>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <input className="form-control" value={evidenceLink} onChange={e => setEvidenceLink(e.target.value)} placeholder="Paste a URL..." />
            <button type="button" className="btn btn-primary" style={{ whiteSpace: 'nowrap' }} onClick={addEvidenceLink}>Add Link</button>
            <button type="button" className="btn btn-outline" style={{ whiteSpace: 'nowrap' }} onClick={() => evidenceFileRef.current?.click()}>Upload PDF</button>
          </div>
          <input type="file" ref={evidenceFileRef} accept=".pdf" style={{ display: 'none' }} onChange={handleEvidenceUpload} />
          {val.length > 0 && (
            <ul style={{ margin: 0, padding: 0, listStyle: 'none', fontSize: '0.8125rem' }}>
              {val.map((item: string, i: number) => (
                <li key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                    {item.startsWith('data/uploads/') || item.includes('/uploads/') ? '📎 ' : '🔗 '}{item}
                  </span>
                  <button type="button" className="btn btn-ghost" style={{ padding: '0.25rem', color: 'var(--danger)' }} onClick={() => removeEvidenceItem(i)}>
                    <i className="ti ti-x"></i>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    }
    if (f.key === 'findings') {
      return (
        <div>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <input className="form-control" value={findingLink} onChange={e => setFindingLink(e.target.value)} placeholder="Paste a URL..." />
            <button type="button" className="btn btn-primary" style={{ whiteSpace: 'nowrap' }} onClick={addFindingLink}>Add Link</button>
            <button type="button" className="btn btn-outline" style={{ whiteSpace: 'nowrap' }} onClick={() => findingFileRef.current?.click()}>Upload PDF</button>
          </div>
          <input type="file" ref={findingFileRef} accept=".pdf" style={{ display: 'none' }} onChange={handleFindingUpload} />
          {val.length > 0 && (
            <ul style={{ margin: 0, padding: 0, listStyle: 'none', fontSize: '0.8125rem' }}>
              {val.map((item: string, i: number) => (
                <li key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                    {item.startsWith('data/uploads/') || item.includes('/uploads/') ? '📎 ' : '🔗 '}{item}
                  </span>
                  <button type="button" className="btn btn-ghost" style={{ padding: '0.25rem', color: 'var(--danger)' }} onClick={() => removeFindingItem(i)}>
                    <i className="ti ti-x"></i>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    }
    if (f.type === 'select') {
      const opts = f.options || [];
      return (
        <select className="form-control" value={String(val)} onChange={e => update(f.key, e.target.value)}>
          {opts.map((o: string) => <option key={o} value={o}>{o}</option>)}
        </select>
      );
    }
    if (f.type === 'number') {
      return <input className="form-control" type="number" value={val} onChange={e => update(f.key, e.target.value)} />;
    }
    if (f.type === 'date') {
      return <input className="form-control" type="date" value={val} onChange={e => update(f.key, e.target.value)} />;
    }
    return (
      <input className="form-control" value={val} onChange={e => update(f.key, e.target.value)} placeholder={f.label} />
    );
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/people')} style={{ padding: '0.5rem' }}>
            <i className="ti ti-arrow-left" style={{ fontSize: 20 }}></i>
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People Assets</p>
            <h1>Add New Person</h1>
          </div>
        </div>
      </div>
      <div className="card" style={{ maxWidth: '960px' }}>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {sections.map(section => (
              <div key={section.label}>
                <h3 style={{ fontSize: '0.9375rem', margin: '0 0 0.75rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
                  <i className="ti ti-user" style={{ color: 'var(--primary)', fontSize: 16 }}></i> {section.label}
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                  {section.fields.map((f: any) => (
                    <div key={f.key} style={f.col === 2 ? { gridColumn: 'span 2' } : undefined}>
                      <label style={{ display: 'block', marginBottom: '0.375rem', fontWeight: 500, fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                        {f.label}
                      </label>
                      {input(f)}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
            <button type="button" className="btn btn-outline" onClick={() => navigate('/assets/people')}>Cancel</button>
            <button type="submit" className="btn btn-primary"><i className="ti ti-plus" style={{ fontSize: 14 }}></i><span style={{ marginLeft: '0.5rem' }}>Create Person</span></button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PeopleCreate;
