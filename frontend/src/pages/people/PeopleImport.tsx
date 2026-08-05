import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const EXPECTED_FIELDS = ['employeeId', 'name', 'email', 'department', 'jobTitle', 'manager', 'employmentType', 'location', 'startDate', 'endDate', 'status'] as const;

const HEADER_ALIASES: Record<string, string> = {
  'employee id': 'employeeId',
  'employee_id': 'employeeId',
  'employeeid': 'employeeId',
  'id': 'employeeId',
  'name': 'name',
  'full name': 'name',
  'full_name': 'name',
  'fullname': 'name',
  'employee name': 'name',
  'email': 'email',
  'e-mail': 'email',
  'work email': 'email',
  'work_email': 'email',
  'email address': 'email',
  'department': 'department',
  'dept': 'department',
  'job title': 'jobTitle',
  'job_title': 'jobtitle',
  'jobtitle': 'jobTitle',
  'title': 'jobTitle',
  'position': 'jobTitle',
  'manager': 'manager',
  'supervisor': 'manager',
  'reports to': 'manager',
  'reports_to': 'manager',
  'employment type': 'employmentType',
  'employment_type': 'employmenttype',
  'employmenttype': 'employmentType',
  'employee type': 'employmentType',
  'emp type': 'employmentType',
  'emp_type': 'employmentType',
  'location': 'location',
  'work location': 'location',
  'work_location': 'location',
  'office': 'location',
  'start date': 'startDate',
  'start_date': 'startDate',
  'startdate': 'startDate',
  'hire date': 'startDate',
  'hire_date': 'startDate',
  'date of hire': 'startDate',
  'end date': 'endDate',
  'end_date': 'endDate',
  'enddate': 'endDate',
  'termination date': 'endDate',
  'termination_date': 'endDate',
  'exit date': 'endDate',
  'exit_date': 'endDate',
  'status': 'status',
  'employment status': 'status',
  'employment_status': 'status',
};

const EMPLOYMENT_TYPES = ['Employee', 'Contractor', 'Consultant', 'Intern', 'Temp Staff', 'Vendor User', 'Third-Party User', 'Service Account', 'Shared Account', 'Privileged Account', 'Administrator', 'Developer', 'Security Personnel'];
const DEPARTMENTS = ['Engineering', 'Security', 'Finance', 'HR', 'Sales', 'Marketing', 'Legal', 'Operations', 'Product', 'IT'];
const STATUSES = ['Active', 'Suspended', 'Offboarding'];

interface CsvRow {
  [key: string]: string;
}

interface ImportResult {
  name: string;
  email: string;
  status: 'success' | 'error';
  error?: string;
}

const PeopleImport = () => {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [rawData, setRawData] = useState<CsvRow[]>([]);
  const [columnMap, setColumnMap] = useState<Record<string, string>>({});
  const [headers, setHeaders] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [results, setResults] = useState<ImportResult[] | null>(null);
  const [error, setError] = useState('');

  const parseCSV = (text: string) => {
    const lines = text.split('\n').filter(l => l.trim());
    if (lines.length < 2) {
      setError('CSV must have a header row and at least one data row');
      return;
    }
    const rawHeaders = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    const map: Record<string, string> = {};
    for (const h of rawHeaders) {
      const key = HEADER_ALIASES[h.toLowerCase()] || '';
      if (key) map[h] = key;
    }
    const rows: CsvRow[] = [];
    for (let i = 1; i < lines.length; i++) {
      const vals = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''));
      const row: CsvRow = {};
      for (let j = 0; j < rawHeaders.length; j++) {
        row[rawHeaders[j]] = vals[j] || '';
      }
      rows.push(row);
    }
    setHeaders(rawHeaders);
    setColumnMap(map);
    setRawData(rows);
    setError('');
    setResults(null);
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      parseCSV(text);
    };
    reader.readAsText(file);
  };

  const buildPayload = (row: CsvRow) => {
    const get = (field: string) => {
      const csvHeader = Object.entries(columnMap).find(([, v]) => v === field)?.[0];
      return csvHeader ? row[csvHeader] || '' : '';
    };
    const name = get('name');
    const employeeId = get('employeeId');
    const email = get('email');
    const department = get('department');
    const jobTitle = get('jobTitle');
    const manager = get('manager');
    const employmentType = get('employmentType');
    const location = get('location');
    const startDate = get('startDate');
    const endDate = get('endDate');
    const status = get('status');

    return {
      name,
      email,
      asset_type: EMPLOYMENT_TYPES.includes(employmentType) ? employmentType : 'Employee',
      department: DEPARTMENTS.includes(department) ? department : 'Engineering',
      job_title: jobTitle,
      manager,
      status: STATUSES.includes(status) ? status : 'Active',
      start_date: startDate ? new Date(startDate).toISOString() : null,
      end_date: endDate ? new Date(endDate).toISOString() : null,
      description: JSON.stringify({
        employeeId,
        jobTitle,
        location,
        authMethod: 'SSO',
        workArrangement: 'On-site',
        mfa: { enrolled: false, enforced: false, method: 'None', enforcedVia: [], enrollmentDate: '', lastVerifiedDate: '', verificationSource: '', exceptionGranted: false, exceptionReason: '', exceptionApprovedBy: '', exceptionExpiryDate: '', evidence: [], notes: '' },
        backgroundCheck: 'Not Required',
        ndaSigned: false,
        lastPasswordChange: '',
        complianceTraining: { securityAwareness: 'N/A', gdpr: 'N/A', aup: 'N/A', codeOfConduct: 'N/A', phishing: 'N/A' },
        joinDate: '',
        transferDate: '',
        exitDate: '',
        offboardingStatus: 'N/A',
        roles: [],
        groups: [],
        privilegedAccess: false,
        vpnAccess: false,
        pamVault: false,
        lastLogin: '',
        lastAccessReview: '',
        assetOwner: '',
        reviewer: '',
        reviewFrequency: 'Quarterly',
        evidenceAttachments: [],
        exceptions: [],
        findings: [],
      }),
    };
  };

  const handleImport = async () => {
    setImporting(true);
    setResults(null);
    const res: ImportResult[] = [];
    for (const row of rawData) {
      const name = Object.entries(columnMap).find(([, v]) => v === 'name')?.[0] || '';
      const email = Object.entries(columnMap).find(([, v]) => v === 'email')?.[0] || '';
      try {
        const payload = buildPayload(row);
        await api.post('/api/people-assets/', payload);
        res.push({ name: row[name] || '', email: row[email] || '', status: 'success' });
      } catch (err: any) {
        res.push({ name: row[name] || '', email: row[email] || '', status: 'error', error: err?.response?.data?.detail || err?.message || 'API error' });
      }
    }
    setResults(res);
    setImporting(false);
  };

  const mappedCount = Object.keys(columnMap).length;
  const recognizedHeaders = headers.filter(h => columnMap[h]);
  const unrecognizedHeaders = headers.filter(h => !columnMap[h]);

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>People Assets</p>
          <h1>Import from CSV</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/assets/people')}>
            <i className="ti ti-arrow-left"></i> Back
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <input type="file" ref={fileRef} accept=".csv" style={{ display: 'none' }} onChange={handleFile} />
          <button className="btn btn-primary" onClick={() => fileRef.current?.click()}>
            <i className="ti ti-file-spreadsheet"></i> Select CSV File
          </button>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            {rawData.length > 0 ? `${rawData.length} rows loaded` : 'No file selected'}
          </span>
        </div>
        {error && <p style={{ color: '#dc2626', fontSize: '0.8125rem', marginTop: '0.5rem' }}>{error}</p>}
      </div>

      {rawData.length > 0 && (
        <>
          <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 0.75rem' }}>Column Mapping</h3>
            <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.8125rem' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span style={{ fontWeight: 600 }}>Recognized ({mappedCount}/11):</span>
                {recognizedHeaders.map(h => (
                  <span key={h} style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: 4, background: '#05966915', color: '#059669', border: '1px solid #05966930' }}>
                    {h} → {columnMap[h]}
                  </span>
                ))}
              </div>
              {unrecognizedHeaders.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Discarded:</span>
                  {unrecognizedHeaders.map(h => (
                    <span key={h} style={{ display: 'inline-flex', padding: '2px 8px', borderRadius: 4, background: '#6b728015', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                      {h}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '1.5rem' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Department</th>
                    <th>Job Title</th>
                    <th>Manager</th>
                    <th>Employment Type</th>
                    <th>Location</th>
                    <th>Start Date</th>
                    <th>End Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rawData.map((row, i) => {
                    const get = (field: string) => {
                      const csvHeader = Object.entries(columnMap).find(([, v]) => v === field)?.[0];
                      return csvHeader ? row[csvHeader] || '-' : '-';
                    };
                    return (
                      <tr key={i}>
                        <td>{i + 1}</td>
                        <td>{get('name')}</td>
                        <td>{get('email')}</td>
                        <td>{get('department')}</td>
                        <td>{get('jobTitle')}</td>
                        <td>{get('manager')}</td>
                        <td>{get('employmentType')}</td>
                        <td>{get('location')}</td>
                        <td>{get('startDate')}</td>
                        <td>{get('endDate')}</td>
                        <td>{get('status')}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <button className="btn btn-primary" onClick={handleImport} disabled={importing}>
              <i className="ti ti-device-floppy"></i> {importing ? 'Importing...' : `Import ${rawData.length} Records`}
            </button>
            <button className="btn btn-ghost" onClick={() => { setRawData([]); setHeaders([]); setColumnMap({}); setResults(null); setError(''); }}>
              Clear
            </button>
          </div>

          {results && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 0.75rem' }}>
                Import Results
                <span style={{ fontSize: '0.8125rem', fontWeight: 400, marginLeft: '0.5rem', color: 'var(--text-secondary)' }}>
                  {results.filter(r => r.status === 'success').length} succeeded, {results.filter(r => r.status === 'error').length} failed
                </span>
              </h3>
              {results.filter(r => r.status === 'error').length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {results.filter(r => r.status === 'error').map((r, i) => (
                    <div key={i} style={{ padding: '0.5rem 0.75rem', borderRadius: 6, background: '#dc262615', border: '1px solid #dc262630', fontSize: '0.8125rem' }}>
                      <strong>{r.name}</strong> ({r.email}): {r.error}
                    </div>
                  ))}
                </div>
              )}
              {results.filter(r => r.status === 'success').length === rawData.length && (
                <p style={{ color: '#059669', fontSize: '0.875rem' }}><i className="ti ti-circle-check"></i> All records imported successfully!</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PeopleImport;
