import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Shield, ArrowLeft, Loader2, Mail, CheckCircle } from 'lucide-react';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/api/auth/forgot-password', { email });
      setSent(true);
      setResetToken(response.data.token || null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        backgroundColor: 'var(--background)', padding: '2rem'
      }}>
        <div className="card" style={{ width: '100%', maxWidth: '440px', textAlign: 'center', padding: '3rem' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '50%',
            backgroundColor: 'rgba(16, 185, 129, 0.1)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem'
          }}>
            <CheckCircle size={32} color="var(--success)" />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>Check Your Email</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
            If an account with <strong>{email}</strong> exists, a password reset link has been sent.
          </p>
          {resetToken && (
            <div style={{
              padding: '1rem', backgroundColor: 'rgba(14, 165, 233, 0.1)', borderRadius: 'var(--radius)',
              border: '1px solid rgba(14, 165, 233, 0.2)', marginBottom: '1.5rem', fontSize: '0.8125rem',
              wordBreak: 'break-all', fontFamily: 'monospace'
            }}>
              <p style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                No email service configured — use this token:
              </p>
              <p style={{ color: 'var(--primary)', fontWeight: 600 }}>{resetToken}</p>
              <Link
                to={`/reset-password?token=${resetToken}`}
                className="btn btn-primary"
                style={{ marginTop: '1rem', textDecoration: 'none', display: 'inline-flex' }}
              >
                Reset Password Now
              </Link>
            </div>
          )}
          <Link to="/login" style={{ color: 'var(--primary)', fontSize: '0.875rem', textDecoration: 'none' }}>
            <ArrowLeft size={14} style={{ verticalAlign: 'middle', marginRight: '0.25rem' }} />
            Back to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      backgroundColor: 'var(--background)', padding: '2rem'
    }}>
      <div style={{ width: '100%', maxWidth: '440px', animation: 'fadeIn 0.5s ease-out' }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <div style={{
            display: 'inline-flex', padding: '1rem', backgroundColor: 'var(--surface)',
            borderRadius: '1.25rem', boxShadow: 'var(--shadow-lg)', marginBottom: '1.25rem',
            border: '1px solid var(--border)'
          }}>
            <Shield size={40} color="var(--primary)" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
            Forgot Password
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem' }}>
            Enter your email and we'll send you a reset link.
          </p>
        </div>

        <div className="card" style={{ padding: '2.5rem' }}>
          <form onSubmit={handleSubmit}>
            {error && (
              <div style={{
                padding: '0.875rem', backgroundColor: 'rgba(239, 68, 68, 0.1)',
                color: 'var(--danger)', borderRadius: 'var(--radius)', marginBottom: '1.5rem',
                fontSize: '0.875rem', border: '1px solid rgba(239, 68, 68, 0.2)'
              }}>
                {error}
              </div>
            )}

            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', opacity: 0.5 }} />
                <input
                  type="email"
                  className="form-control"
                  style={{ width: '100%', paddingLeft: '3rem' }}
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.875rem' }} disabled={loading}>
              {loading ? <Loader2 className="animate-spin" size={18} /> : 'Send Reset Link'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
            <Link to="/login" style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textDecoration: 'none', transition: 'color 0.2s' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
            >
              <ArrowLeft size={14} style={{ verticalAlign: 'middle', marginRight: '0.25rem' }} />
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
