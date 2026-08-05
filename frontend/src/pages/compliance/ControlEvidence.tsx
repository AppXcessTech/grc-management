import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Upload, FileText, CheckCircle, XCircle, Clock, Hash, Download } from 'lucide-react';
import api from '../../services/api';

interface EvidenceFile {
  id: number;
  file_name: string;
  file_size: number | null;
  mime_type: string | null;
  created_at: string;
}

interface EvidenceReview {
  id: number;
  status: string;
  comment: string | null;
  reviewer_id: number | null;
  reviewed_at: string | null;
  created_at: string;
}

interface Evidence {
  id: number;
  name: string;
  description: string | null;
  evidence_type: string;
  collected_by: number | null;
  collected_at: string;
  created_at: string;
  files: EvidenceFile[];
  reviews: EvidenceReview[];
}

interface Control {
  id: number;
  code: string;
  name: string;
  description: string;
}

const statusIcon: Record<string, typeof CheckCircle> = {
  approved: CheckCircle,
  rejected: XCircle,
  pending: Clock,
};

const statusColor: Record<string, string> = {
  approved: 'var(--success)',
  rejected: 'var(--danger)',
  pending: 'var(--warning)',
};

const ControlEvidence = () => {
  const { frameworkId, controlId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [control, setControl] = useState<Control | null>(null);
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [evidenceName, setEvidenceName] = useState('');
  const [evidenceDesc, setEvidenceDesc] = useState('');
  const [hasFile, setHasFile] = useState(false);

  const reloadEvidence = async () => {
    try {
      const [controlRes, evidenceRes] = await Promise.all([
        api.get(`/api/controls/${controlId}`),
        api.get(`/api/controls/${controlId}/evidence`),
      ]);
      setControl(controlRes.data);
      setEvidenceList(evidenceRes.data);
    } catch {
      setError('Failed to load evidence.');
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [controlRes, evidenceRes] = await Promise.all([
          api.get(`/api/controls/${controlId}`),
          api.get(`/api/controls/${controlId}/evidence`),
        ]);
        if (!cancelled) {
          setControl(controlRes.data);
          setEvidenceList(evidenceRes.data);
        }
      } catch {
        if (!cancelled) setError('Failed to load evidence.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [controlId]);

  const handleFileChange = () => {
    setHasFile(!!fileInputRef.current?.files?.length);
  };

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file || !evidenceName) return;

    setUploading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const params = new URLSearchParams({ name: evidenceName });
      if (evidenceDesc) params.append('description', evidenceDesc);

      await api.post(`/api/controls/${controlId}/evidence/upload?${params}`, formData);
      setEvidenceName('');
      setEvidenceDesc('');
      setHasFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await reloadEvidence();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Upload failed.';
      setError(detail);
    } finally {
      setUploading(false);
    }
  };

  const getLatestReviewStatus = (reviews: EvidenceReview[]) => {
    if (reviews.length === 0) return null;
    return reviews[reviews.length - 1];
  };

  const handleDownload = async (evidenceId: number, fileId: number, fileName: string) => {
    try {
      const res = await api.get(`/api/controls/${controlId}/evidence/${evidenceId}/files/${fileId}/download`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError('Download failed.');
    }
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} color="var(--primary)" />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            className="btn btn-secondary"
            onClick={() => navigate(`/compliance/${frameworkId}/requirements`)}
            style={{ padding: '0.5rem', borderRadius: '50%' }}
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              Evidence Management
            </p>
            <h1>{control?.code}: {control?.name}</h1>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {/* Upload Section */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.125rem', fontWeight: 700 }}>
          <Upload size={18} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Upload Evidence
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>Evidence Name *</label>
            <input
              type="text"
              className="form-control"
              style={{ width: '100%' }}
              placeholder="e.g. Access Control Audit Screenshot"
              value={evidenceName}
              onChange={(e) => setEvidenceName(e.target.value)}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>File</label>
            <input
              type="file"
              ref={fileInputRef}
              className="form-control"
              style={{ width: '100%', padding: '0.625rem 1rem' }}
              onChange={handleFileChange}
            />
          </div>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>Description (optional)</label>
          <textarea
            className="form-control"
            style={{ width: '100%', minHeight: '60px', resize: 'vertical' }}
            placeholder="Describe what this evidence covers..."
            value={evidenceDesc}
            onChange={(e) => setEvidenceDesc(e.target.value)}
          />
        </div>
        <button
          className="btn btn-primary"
          onClick={handleUpload}
          disabled={uploading || !evidenceName || !hasFile}
        >
          {uploading ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
          {uploading ? 'Uploading...' : 'Upload Evidence'}
        </button>
      </div>

      {/* Evidence List */}
      <h3 style={{ marginBottom: '1rem', fontSize: '1.125rem', fontWeight: 700 }}>
        <FileText size={18} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
        Collected Evidence ({evidenceList.length})
      </h3>

      {evidenceList.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
          <FileText size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <p>No evidence has been collected for this control yet.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {evidenceList.map((evidence) => {
            const latestReview = getLatestReviewStatus(evidence.reviews);
            const StatusIcon = latestReview ? statusIcon[latestReview.status] : Clock;

            return (
              <div key={evidence.id} className="card" style={{ marginBottom: 0, padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                      <span className="badge badge-indigo" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}>
                        <Hash size={12} />#{evidence.id}
                      </span>
                      <h4 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0 }}>{evidence.name}</h4>
                      {latestReview && (
                        <span className="badge" style={{
                          backgroundColor: `${statusColor[latestReview.status]}15`,
                          color: statusColor[latestReview.status],
                          display: 'inline-flex', alignItems: 'center', gap: '0.25rem'
                        }}>
                          <StatusIcon size={12} />
                          {latestReview.status}
                        </span>
                      )}
                    </div>
                    {evidence.description && (
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: '0.25rem 0 0 0' }}>{evidence.description}</p>
                    )}
                  </div>
                </div>

                {/* Files */}
                {evidence.files.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                    {evidence.files.map((file) => (
                      <div key={file.id} style={{
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                        padding: '0.5rem 0.75rem', backgroundColor: 'rgba(255,255,255,0.02)',
                        borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.8125rem'
                      }}>
                        <FileText size={14} color="var(--primary)" />
                        <span style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {file.file_name}
                        </span>
                        {file.file_size && (
                          <span style={{ color: 'var(--text-muted)' }}>({formatFileSize(file.file_size)})</span>
                        )}
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.5rem', marginLeft: 'auto', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', border: 'none', cursor: 'pointer' }}
                          onClick={() => handleDownload(evidence.id, file.id, file.file_name)}
                          title="Download file"
                        >
                          <Download size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Reviews */}
                {evidence.reviews.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                    <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Review History</p>
                    {evidence.reviews.map((review) => (
                      <div key={review.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                        <span className="badge" style={{
                          backgroundColor: `${statusColor[review.status]}15`,
                          color: statusColor[review.status],
                          padding: '0.125rem 0.5rem',
                          fontSize: '0.6875rem',
                        }}>
                          {review.status}
                        </span>
                        <span>{review.comment}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
                  Collected {new Date(evidence.collected_at).toLocaleDateString()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ControlEvidence;
