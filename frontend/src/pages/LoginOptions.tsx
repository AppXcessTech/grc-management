import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Loader2, ArrowLeft } from 'lucide-react';

declare global {
  interface Window {
    google?: any;
  }
}

const GoogleSignInButton = () => {
  const { login } = useAuth();
  const buttonRef = useRef<HTMLDivElement>(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState(false);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (window.google?.accounts?.id) {
      setScriptLoaded(true);
      return;
    }
    if (document.getElementById('google-gsi-script')) return;

    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setScriptLoaded(true);
    script.onerror = () => setScriptError(true);
    document.body.appendChild(script);
  }, []);

  useEffect(() => {
    if (!scriptLoaded || !buttonRef.current || !window.google?.accounts?.id || initializedRef.current) return;
    initializedRef.current = true;

    window.google.accounts.id.initialize({
      client_id: '369022549081-qbv4ivuvlvpgu5cch1ksi0vajlevgns5.apps.googleusercontent.com',
      callback: async (response: any) => {
        try {
          const res = await api.post('/api/auth/google', { id_token: response.credential });
          login(res.data.access_token, res.data.refresh_token);
          window.location.href = '/';
        } catch {
          alert('Google sign-in failed');
        }
      },
    });

    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      width: buttonRef.current.offsetWidth || 320,
    });
  }, [scriptLoaded, login]);

  return (
    <div ref={buttonRef} style={{ width: '100%', minHeight: '40px', display: 'flex', justifyContent: 'center' }}>
      {!scriptLoaded && !scriptError && <Loader2 className="animate-spin" size={24} color="var(--text-muted)" />}
      {scriptError && <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Google sign-in unavailable</p>}
    </div>
  );
};

const MicrosoftSignInSection = () => {
  const handleSignIn = () => {
    window.location.href = '/api/auth/sso/microsoft/login?org_id=1';
  };

  return (
    <button
      onClick={handleSignIn}
      className="btn"
      style={{
        width: '100%',
        padding: '0.875rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem',
        border: '1px solid var(--border)',
        backgroundColor: 'var(--surface)',
        color: 'var(--text-main)',
        fontSize: '0.9375rem',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      <svg width="20" height="20" viewBox="0 0 23 23" fill="none">
        <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
        <rect x="12" y="1" width="9" height="9" fill="#7FBA00"/>
        <rect x="1" y="12" width="9" height="9" fill="#00A4EF"/>
        <rect x="12" y="12" width="9" height="9" fill="#FFB900"/>
      </svg>
      Sign in with Microsoft
    </button>
  );
};

const LoginOptions = () => {
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
        <h1 style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: '0.5rem', color: 'var(--text-main)' }}>Login Options</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Choose an alternative sign-in method</p>
      </div>

      <div className="card" style={{
        width: '100%',
        maxWidth: '420px',
        padding: '2.5rem',
        animation: 'fadeIn 0.5s ease-out',
        borderTop: '4px solid var(--primary)'
      }}>
        <GoogleSignInButton />

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', margin: '1.5rem 0' }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border)' }} />
          <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>or</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border)' }} />
        </div>

        <MicrosoftSignInSection />

        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
          <Link
            to="/login"
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
            <ArrowLeft size={16} />
            Back to Login
          </Link>
        </div>
      </div>

      <div style={{ marginTop: '3rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
        &copy; 2026 AppXcess Inc. All rights reserved.
      </div>
    </div>
  );
};

export default LoginOptions;
