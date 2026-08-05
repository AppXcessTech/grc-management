import React, { useEffect, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Loader2, ArrowRight, Building2, Users } from 'lucide-react';

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'client' | 'admin'>('client');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    const errorMsg = searchParams.get('error');
    const detailMsg = searchParams.get('detail');
    if (token) {
      login(token);
      navigate('/', { replace: true });
    } else if (errorMsg) {
      setError(detailMsg ? `${errorMsg}: ${detailMsg}` : errorMsg);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'client') {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        const response = await api.post('/api/auth/login', formData);
        login(response.data.access_token, response.data.refresh_token);
        navigate('/');
      } else {
        const response = await api.post('/api/overlook/auth/login', new URLSearchParams({
          username: email,
          password: password,
        }), {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        localStorage.setItem('platform_token', response.data.access_token);
        navigate('/overlook/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setMode(m => m === 'client' ? 'admin' : 'client');
    setError('');
    setEmail('');
    setPassword('');
  };

  const isClient = mode === 'client';

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--background)',
      padding: '2rem'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem', animation: 'fadeIn 0.8s ease-out' }}>
        <div style={{
          display: 'inline-flex',
          padding: '1rem',
          backgroundColor: 'var(--surface)',
          borderRadius: '1.25rem',
          boxShadow: 'var(--shadow-lg)',
          marginBottom: '1.5rem',
          border: '1px solid var(--border)'
        }}>
          <Shield size={48} color="var(--primary)" />
        </div>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: '0.5rem', color: 'var(--text-main)' }}>AppXcess GRC</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Enterprise Governance, Risk & Compliance</p>
      </div>

      <div className="card" style={{
        width: '100%',
        maxWidth: '420px',
        padding: '2.5rem',
        animation: 'fadeIn 0.5s ease-out',
        transition: 'border-color 0.3s',
        borderTop: isClient ? '4px solid var(--success)' : '4px solid var(--primary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: isClient ? 'rgba(16, 185, 129, 0.1)' : 'rgba(14, 165, 233, 0.1)',
            transition: 'background-color 0.3s'
          }}>
            {isClient ? <Building2 size={22} color="var(--success)" /> : <Users size={22} color="var(--primary)" />}
          </div>
          <div>
            <h2 style={{ fontSize: '1.375rem', fontWeight: 700, margin: 0 }}>{isClient ? 'Client Login' : 'Admin Login'}</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.125rem 0 0 0' }}>
              {isClient ? 'Access your compliance dashboard' : 'Platform administration portal'}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ marginTop: '2rem' }}>
          {error && (
            <div style={{
              padding: '0.875rem',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              color: 'var(--danger)',
              borderRadius: 'var(--radius)',
              marginBottom: '1.25rem',
              fontSize: '0.8125rem',
              border: '1px solid rgba(239, 68, 68, 0.2)'
            }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              {isClient ? 'Corporate Email' : 'Staff Email'}
            </label>
            <input
              type="email"
              className="form-control"
              style={{ width: '100%' }}
              placeholder={isClient ? 'name@company.com' : 'admin@appxcess.com'}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.375rem', fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-muted)' }}>Password</label>
            <input
              type="password"
              className="form-control"
              style={{ width: '100%' }}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {isClient && (
            <div style={{ textAlign: 'right', marginBottom: '1.5rem' }}>
              <Link
                to="/forgot-password"
                style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--primary)')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
              >
                Forgot Password?
              </Link>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{
              width: '100%',
              padding: '0.875rem',
              backgroundColor: isClient ? 'var(--success)' : 'var(--primary)',
              borderColor: isClient ? 'var(--success)' : 'var(--primary)',
              transition: 'background-color 0.3s, border-color 0.3s'
            }}
            disabled={loading}
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : (
              <>
                Sign In <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {isClient && (
          <div style={{ marginTop: '1.25rem', textAlign: 'center' }}>
            <Link
              to="/login/options"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: 'var(--text-muted)',
                fontSize: '0.8125rem',
                textDecoration: 'none',
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border)',
                transition: 'all 0.2s',
                width: '100%',
                justifyContent: 'center',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--primary)';
                e.currentTarget.style.color = 'var(--primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.color = 'var(--text-muted)';
              }}
            >
              Other Login Options
            </Link>
          </div>
        )}

        <div style={{ marginTop: isClient ? '1rem' : '1.5rem', textAlign: 'center' }}>
          <button
            onClick={toggleMode}
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              padding: '0.5rem 1.25rem',
              color: 'var(--text-muted)',
              fontSize: '0.8125rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
              width: '100%'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--primary)';
              e.currentTarget.style.color = 'var(--primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.color = 'var(--text-muted)';
            }}
          >
            Switch to {isClient ? 'Admin' : 'Client'} Login
          </button>
        </div>
      </div>

      <div style={{ marginTop: '3rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
        &copy; 2026 AppXcess Inc. All rights reserved.
      </div>
    </div>
  );
};

export default Login;
