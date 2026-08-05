import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bell, Search, UserCircle, LogOut, ChevronDown, ShieldCheck, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

interface Notification {
  id: number;
  title: string;
  message: string | null;
  notification_type: string;
  reference_type: string | null;
  reference_id: number | null;
  is_read: boolean;
  created_at: string;
}

const Topbar = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [showPerms, setShowPerms] = useState(false);
  const [showNotifs, setShowNotifs] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const popoverRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  const fetchUnread = useCallback(async () => {
    try {
      const res = await api.get('/api/notifications/unread-count');
      setUnreadCount(res.data.count);
    } catch {}
  }, []);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await api.get('/api/notifications/');
      setNotifications(res.data);
    } catch {}
  }, []);

  useEffect(() => {
    fetchUnread();
    const interval = setInterval(fetchUnread, 15000);
    return () => clearInterval(interval);
  }, [fetchUnread]);

  useEffect(() => {
    if (showNotifs) fetchNotifications();
  }, [showNotifs, fetchNotifications]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowPerms(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifs(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markRead = async (id: number) => {
    try {
      await api.post(`/api/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {}
  };

  const handleNotificationClick = async (n: Notification) => {
    if (!n.is_read) await markRead(n.id);
    setShowNotifs(false);
    if (n.reference_type === 'asset_suggestion' && n.reference_id) {
      navigate(`/assets/suggestions/${n.reference_id}/review`);
    } else if ((n.reference_type === 'import_request' || n.reference_type === 'asset_import_request') && n.reference_id) {
      navigate(`/assets/import-requests/${n.reference_id}/review`);
    }
  };

  const markAllRead = async () => {
    try {
      await api.post('/api/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {}
  };

  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || 'User';
  const primaryRole = user?.roles?.[0] || 'employee';
  const permissions = user?.permissions || [];

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <header className="topbar">
      <div className="search-bar">
      </div>
      <div className="topbar-actions" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <div style={{ position: 'relative' }} ref={notifRef}>
          <button
            className="btn-icon"
            onClick={() => setShowNotifs(!showNotifs)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', transition: 'color 0.2s', position: 'relative' }}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute', top: '-4px', right: '-4px',
                width: '16px', height: '16px', borderRadius: '50%',
                backgroundColor: 'var(--danger)', color: '#fff',
                fontSize: '10px', fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifs && (
            <div style={{
              position: 'absolute', right: 0, top: 'calc(100% + 8px)',
              width: '360px', backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)', borderRadius: '10px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.3)', zIndex: 1000,
              overflow: 'hidden',
            }}>
              <div style={{
                padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  Notifications
                </span>
                {unreadCount > 0 && (
                  <button className="btn btn-ghost" style={{ fontSize: '0.75rem', padding: '0.125rem 0.5rem' }} onClick={markAllRead}>
                    Mark all read
                  </button>
                )}
              </div>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {notifications.length === 0 ? (
                  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                    No notifications
                  </div>
                ) : notifications.map(n => (
                  <div
                    key={n.id}
                    onClick={() => handleNotificationClick(n)}
                    style={{
                      padding: '0.75rem 1rem', cursor: 'pointer',
                      borderBottom: '1px solid var(--border)',
                      backgroundColor: n.is_read ? 'transparent' : 'rgba(99, 102, 241, 0.04)',
                      transition: 'background-color 0.2s',
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(99, 102, 241, 0.08)'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = n.is_read ? 'transparent' : 'rgba(99, 102, 241, 0.04)'}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.125rem' }}>
                          {n.title}
                        </div>
                        {n.message && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                            {n.message}
                          </div>
                        )}
                      </div>
                      <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {timeAgo(n.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.5rem 1rem', borderRadius: '12px', backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border)' }}>
          <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-main)' }}>{displayName}</span>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{user?.email || ''}</span>
          </div>
          <div style={{ position: 'relative' }} ref={popoverRef}>
            <div
              onClick={() => setShowPerms(!showPerms)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.375rem',
                padding: '0.25rem 0.5rem', borderRadius: '6px',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                color: 'var(--secondary)', fontSize: '0.75rem', fontWeight: 600,
                cursor: 'pointer', whiteSpace: 'nowrap',
                border: '1px solid rgba(99, 102, 241, 0.2)',
              }}
            >
              <ShieldCheck size={12} />
              {primaryRole.replace(/_/g, ' ')}
              <ChevronDown size={12} style={{ transform: showPerms ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
            </div>

            {showPerms && (
              <div style={{
                position: 'absolute', right: 0, top: 'calc(100% + 6px)',
                width: '280px', backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)', borderRadius: '10px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.3)', zIndex: 1000, overflow: 'hidden',
              }}>
                <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Permissions ({permissions.length})
                </div>
                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                  {permissions.length === 0 ? (
                    <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8125rem', textAlign: 'center' }}>
                      No granular permissions assigned
                    </div>
                  ) : (
                    permissions.map((perm) => (
                      <div key={perm} style={{
                        padding: '0.5rem 1rem', fontSize: '0.8125rem',
                        color: 'var(--text-main)', borderBottom: '1px solid var(--border)',
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                      }}>
                        <ShieldCheck size={12} color="var(--secondary)" />
                        {perm}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--secondary)' }}>
            <UserCircle size={24} />
          </div>
          <button
            onClick={logout}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '0.5rem', marginLeft: '0.5rem', transition: 'color 0.2s' }}
            onMouseOver={(e) => e.currentTarget.style.color = 'var(--danger)'}
            onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
            title="Logout"
          >
            <LogOut size={20} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
