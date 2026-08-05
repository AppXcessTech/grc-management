import { NavLink } from 'react-router-dom';
import {
  ClipboardCheck,
  Search,
  Cloud,
  MessageSquare,
  Users,
  Database,
  Warehouse,
  FileText,
  Shield,
  Building2,
  Fingerprint,
  AlertTriangle,
  Smartphone,
  BarChart3,
  GraduationCap,
  CheckSquare,
  GitBranch,
  Bug,
} from 'lucide-react';

const items = [
  { name: 'Audit Management', path: '/integrations/audit-management', icon: ClipboardCheck },
  { name: 'Background Checkers', path: '/integrations/background-checkers', icon: Search },
  { name: 'Cloud Providers', path: '/integrations/cloud-providers', icon: Cloud },
  { name: 'Communication Platforms', path: '/integrations/communication-platforms', icon: MessageSquare },
  { name: 'CRM Platforms', path: '/integrations/crm-platforms', icon: Users },
  { name: 'Datastore Providers', path: '/integrations/datastore-providers', icon: Database },
  { name: 'Data Warehouse Providers', path: '/integrations/data-warehouse-providers', icon: Warehouse },
  { name: 'Document Management', path: '/integrations/document-management', icon: FileText },
  { name: 'Endpoint Security', path: '/integrations/endpoint-security', icon: Shield },
  { name: 'HRIS', path: '/integrations/hris', icon: Building2 },
  { name: 'Identity Providers', path: '/integrations/identity-providers', icon: Fingerprint },
  { name: 'Incident Management', path: '/integrations/incident-management', icon: AlertTriangle },
  { name: 'MDM', path: '/integrations/mdm', icon: Smartphone },
  { name: 'Observability', path: '/integrations/observability', icon: BarChart3 },
  { name: 'Security Training', path: '/integrations/security-training', icon: GraduationCap },
  { name: 'Task Management', path: '/integrations/task-management', icon: CheckSquare },
  { name: 'Version Control', path: '/integrations/version-control', icon: GitBranch },
  { name: 'Vulnerability Scanners', path: '/integrations/vulnerability-scanners', icon: Bug },
];

const IntegrationsSidebar = () => (
  <aside className="integrations-sidebar">
    <div className="integrations-sidebar-header">Integrations</div>
    <nav className="integrations-sidebar-nav">
      {items.map((item) => (
        <NavLink
          key={item.name}
          to={item.path}
          end={item.end}
          className={({ isActive }) => `integrations-nav-item ${isActive ? 'active' : ''}`}
        >
          <item.icon size={18} />
          <span>{item.name}</span>
        </NavLink>
      ))}
    </nav>
  </aside>
);

export default IntegrationsSidebar;
