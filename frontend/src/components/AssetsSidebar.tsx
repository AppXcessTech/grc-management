import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import { SIDEBAR } from '../data/sidebarConfig';

const AssetsSidebar = () => {
  const location = useLocation();
  const pathSegment = location.pathname.split('/')[2] || '';
  const subPath = location.pathname.split('/').slice(3).join('/');

  const activeGroup = SIDEBAR.find((g) => {
    if (g.slug === pathSegment) return true;
    return g.items.some((i) => i.path === `/assets/${pathSegment}`);
  });

  const [counts, setCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('/api/canonical-assets/categories', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.json())
      .then((cats: { slug: string; count: number }[]) => {
        const m: Record<string, number> = {};
        cats.forEach((c) => { m[c.slug] = c.count; });
        setCounts(m);
      })
      .catch(() => {});
  }, [location]);

  if (!activeGroup) return null;

  const isItemActive = (path: string): boolean => {
    const itemSlug = path.split('/').pop() || '';
    if (!subPath) return path === `/assets/${pathSegment}`;
    return subPath === itemSlug || subPath.endsWith(itemSlug) || subPath.startsWith(itemSlug + '/');
  };

  return (
    <aside className="assets-sidebar">
      <div className="assets-sidebar-header">{activeGroup.label}</div>
      <nav className="assets-sidebar-nav">
        {activeGroup.items.map((item) => {
          const isActive = isItemActive(item.path);
          const itemCount = counts[item.slug];
          const isExternal = item.path.startsWith('/org') || item.path === '/assets/people' || item.path === '/assets/devices';
          return (
            <NavLink
              key={item.slug}
              to={item.path}
              end
              className={`sidebar-subitem ${isActive ? 'active' : ''}`}
            >
              <item.icon size={14} />
              <span className="sidebar-subitem-label">{item.label}</span>
              {itemCount !== undefined && itemCount > 0 && (
                <span className="sidebar-subitem-badge">{itemCount}</span>
              )}
              {isExternal && <ExternalLink size={10} className="sidebar-external-icon" />}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};

export default AssetsSidebar;
