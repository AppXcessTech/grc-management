import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import api from '../services/api';
import { Shield, Loader2, Key, CheckCircle, ArrowLeft } from 'lucide-react';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/api/auth/reset-password', { token, password });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Reset failed. The link may be expired.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
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
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>Password Reset!</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: '2rem' }}>
            Your password has been updated successfully.
          </p>
          <Link to="/login" className="btn btn-primary" style={{ textDecoration: 'none', display: 'inline-flex' }}>
            Sign In
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
            <Key size={40} color="var(--primary)" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
            Reset Password
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem' }}>
            Choose a new password for your account.
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

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                New Password
              </label>
              <input
                type="password"
                className="form-control"
                style={{ width: '100%' }}
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                Confirm Password
              </label>
              <input
                type="password"
                className="form-control"
                style={{ width: '100%' }}
                placeholder="Repeat your new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.875rem' }} disabled={loading}>
              {loading ? <Loader2 className="animate-spin" size={18} /> : 'Reset Password'}
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

export default ResetPassword;
