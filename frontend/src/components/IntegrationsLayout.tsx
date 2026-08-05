import { Outlet } from 'react-router-dom';
import IntegrationsSidebar from './IntegrationsSidebar';

const IntegrationsLayout = () => (
  <div className="integrations-layout">
    <IntegrationsSidebar />
    <div className="integrations-content">
      <Outlet />
    </div>
  </div>
);

export default IntegrationsLayout;
