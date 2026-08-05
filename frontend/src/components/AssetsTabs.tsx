import { NavLink, useLocation } from 'react-router-dom';
import { SIDEBAR } from '../data/sidebarConfig';

const AssetsTabs = () => {
  const location = useLocation();
  const pathSegment = location.pathname.split('/')[2] || '';

  const activeFromPath = SIDEBAR.find((g) => {
    if (g.slug === pathSegment) return true;
    return g.items.some((i) => i.path === `/assets/${pathSegment}`);
  });

  return (
    <div className="assets-tabs">
      <nav className="assets-tabs-nav">
        {SIDEBAR.map((group) => {
          const isActive = activeFromPath?.slug === group.slug;
          return (
            <NavLink
              key={group.slug}
              to={`/assets/${group.slug}`}
              className={`assets-tab ${isActive ? 'active' : ''}`}
            >
              <group.icon size={14} />
              <span>{group.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};

export default AssetsTabs;
