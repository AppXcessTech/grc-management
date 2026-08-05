import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  Users, 
  Lock, 
  LayoutDashboard, 
  ClipboardCheck,
  AlertTriangle,
  Briefcase,
  FileText,
  Building2,
  Globe,
  GitBranch,
  Puzzle,
} from 'lucide-react';

const Sidebar = () => {
  const { user } = useAuth();

  const isSuperAdmin = user?.roles?.includes('super_admin');

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Policies', path: '/policies', icon: FileText },
    { name: 'Compliance', path: '/compliance', icon: ClipboardCheck },
    { name: 'Risk Management', path: '/risk', icon: AlertTriangle },
    { name: 'Assets', path: '/assets', icon: Briefcase },
    { name: 'Users', path: '/users', icon: Users },
    ...(isSuperAdmin ? [{ name: 'Roles & Permissions', path: '/roles', icon: Lock }] : []),
    { name: 'Organizations', path: '/organizations', icon: Globe },
    { name: 'Departments', path: '/organizations/departments', icon: Building2 },
    { name: 'Business Units', path: '/organizations/business-units', icon: Briefcase },
    { name: 'Subsidiaries', path: '/organizations/subsidiaries', icon: GitBranch },
    { name: 'Integrations', path: '/integrations', icon: Puzzle },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header" style={{ color: 'var(--text-main)', fontSize: '1.25rem', letterSpacing: '-0.02em' }}>
        <Shield size={32} style={{ color: 'var(--primary)' }} />
        <span>AppXcess <span style={{ color: 'var(--primary)', fontWeight: 800 }}>GRC</span></span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink 
            key={item.name} 
            to={item.path} 
            end={item.path === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={20} />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
