import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  Shield, 
  Building2, 
  LayoutDashboard, 
  Key,
  LogOut,
  Users,
  Activity
} from 'lucide-react';

const OverlookLayout = () => {
  const navigate = useNavigate();
  
  const handleLogout = () => {
    localStorage.removeItem('platform_token');
    navigate('/overlook/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/overlook/dashboard', icon: LayoutDashboard },
    { name: 'Organizations', path: '/overlook/organizations', icon: Building2 },

    { name: 'Staff Management', path: '/overlook/staff', icon: Users },
  ];

  return (
    <div className="app-container">
      <aside className="sidebar" style={{ backgroundColor: '#1e293b' }}>
        <div className="sidebar-header">
          <Activity size={32} color="#f43f5e" />
          <span style={{ color: 'white' }}>Overlook</span>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink 
              key={item.name} 
              to={item.path} 
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              style={({ isActive }) => ({
                color: isActive ? 'white' : '#94a3b8',
                backgroundColor: isActive ? '#334155' : 'transparent'
              })}
            >
              <item.icon size={20} />
              <span>{item.name}</span>
            </NavLink>
          ))}
          <button 
            onClick={handleLogout}
            className="nav-item"
            style={{ marginTop: 'auto', color: '#94a3b8', background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </nav>
      </aside>
      
      <main className="main-content">
        <header className="topbar" style={{ borderBottom: '1px solid #e2e8f0' }}>
          <div className="topbar-search">
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Platform Administration Portal</span>
          </div>
          <div className="topbar-actions">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#f43f5e', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>P</div>
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>Platform Admin</span>
            </div>
          </div>
        </header>
        <div className="content-area">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default OverlookLayout;
