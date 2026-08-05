import { Outlet } from 'react-router-dom';
import AssetsSidebar from './AssetsSidebar';
import AssetsTabs from './AssetsTabs';

const AssetsLayout = () => (
  <>
    <AssetsTabs />
    <div className="assets-layout">
      <AssetsSidebar />
      <div className="assets-content">
        <Outlet />
      </div>
    </div>
  </>
);

export default AssetsLayout;
