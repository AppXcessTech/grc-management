import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import LoginOptions from './pages/LoginOptions';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';

import UserList from './pages/users/UserList';
import RoleList from './pages/roles/RoleList';

import SuggestAsset from './pages/assets/SuggestAsset';
import SuggestionReview from './pages/assets/SuggestionReview';
import ImportRequestReview from './pages/assets/ImportRequestReview';
import CanonicalCategoryPage from './pages/assets/CanonicalCategoryPage';
import ComplianceList from './pages/compliance/ComplianceList';
import RequirementList from './pages/compliance/RequirementList';
import ControlList from './pages/compliance/ControlList';
import ComplianceChecklist from './pages/compliance/ComplianceChecklist';
import ControlEvidence from './pages/compliance/ControlEvidence';
import PolicyList from './pages/policies/PolicyList';
import PolicyDetail from './pages/policies/PolicyDetail';
import PolicyCreate from './pages/policies/PolicyCreate';
import OrganizationList from './pages/organizations/OrganizationList';
import DepartmentList from './pages/organizations/DepartmentList';
import BusinessUnitList from './pages/organizations/BusinessUnitList';
import SubsidiaryList from './pages/organizations/SubsidiaryList';
import OverlookLayout from './pages/overlook/OverlookLayout';
import OverlookDashboard from './pages/overlook/Dashboard';
import OverlookOrganizationList from './pages/overlook/OrganizationList';

import PeopleGRC from './pages/people/PeopleGRC';
import PeopleCreate from './pages/people/PeopleCreate';
import PeopleIntegrations from './pages/people/PeopleIntegrations';
import PeopleIntegrationsSetup from './pages/people/PeopleIntegrationsSetup';
import PeopleImport from './pages/people/PeopleImport';
import AssetsLayout from './components/AssetsLayout';
import IntegrationsLayout from './components/IntegrationsLayout';
import IntegrationDashboard from './pages/integrations/IntegrationDashboard';
import IntegrationPlaceholder from './pages/integrations/IntegrationPlaceholder';
import AWSConfig from './pages/integrations/cloud/AWSConfig';
import AzureConfig from './pages/integrations/cloud/AzureConfig';
import GenericServiceConfig from './pages/integrations/GenericServiceConfig';
import GCPConfig from './pages/integrations/cloud/GCPConfig';
import GitHubConfig from './pages/integrations/GitHubConfig';
import EndpointDashboard from './pages/endpoint/EndpointDashboard';
import EndpointList from './pages/endpoint/EndpointList';
import EndpointCreate from './pages/endpoint/EndpointCreate';
import EndpointDetail from './pages/endpoint/EndpointDetail';
import EndpointIntegrations from './pages/endpoint/EndpointIntegrations';
import EndpointIntegrationsSetup from './pages/endpoint/EndpointIntegrationsSetup';
import ComputeDashboard from './pages/compute/ComputeDashboard';
import ComputeList from './pages/compute/ComputeList';
import ComputeCreate from './pages/compute/ComputeCreate';
import ComputeDetail from './pages/compute/ComputeDetail';

import './App.css';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const ProtectedOverlookRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('platform_token');
  return token ? <>{children}</> : <Navigate to="/overlook/login" />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/login/options" element={<LoginOptions />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          <Route path="/overlook/login" element={<Login />} />
          <Route path="/overlook" element={<ProtectedOverlookRoute><OverlookLayout /></ProtectedOverlookRoute>}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<OverlookDashboard />} />
            <Route path="organizations" element={<OverlookOrganizationList />} />
            <Route path="staff" element={<div className="card"><h1>Staff Management</h1><p>Staff CRUD coming soon...</p></div>} />
          </Route>

          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="users" element={<UserList />} />
            <Route path="roles" element={<RoleList />} />
            <Route path="assets" element={<AssetsLayout />}>
              <Route index element={<Navigate to="/assets/compute" replace />} />
              <Route path="people" element={<PeopleGRC />} />
              <Route path="people/new" element={<PeopleCreate />} />
              <Route path="people/integrations" element={<PeopleIntegrations />} />
              <Route path="people/integrations/setup" element={<PeopleIntegrationsSetup />} />
              <Route path="people/import" element={<PeopleImport />} />
              <Route path="import-requests/:id/review" element={<ImportRequestReview />} />
              <Route path="suggest-asset" element={<SuggestAsset />} />
              <Route path="suggestions/:id/review" element={<SuggestionReview />} />
              <Route path="devices" element={<EndpointDashboard />} />
              <Route path="devices/list" element={<EndpointList />} />
              <Route path="devices/new" element={<EndpointCreate />} />
              <Route path="devices/:id" element={<EndpointDetail />} />
              <Route path="devices/integrations" element={<EndpointIntegrations />} />
              <Route path="devices/integrations/setup" element={<EndpointIntegrationsSetup />} />
              <Route path="servers" element={<ComputeDashboard />} />
              <Route path="servers/list" element={<ComputeList />} />
              <Route path="servers/new" element={<ComputeCreate />} />
              <Route path="servers/:id" element={<ComputeDetail />} />
              <Route path=":group" element={<CanonicalCategoryPage />} />
              <Route path=":group/:type" element={<CanonicalCategoryPage />} />
            </Route>
            <Route path="compliance" element={<ComplianceList />} />
            <Route path="compliance/:frameworkId/requirements" element={<RequirementList />} />
            <Route path="compliance/:frameworkId/controls" element={<ControlList />} />
            <Route path="compliance/:frameworkId/checklist" element={<ComplianceChecklist />} />
            <Route path="compliance/:frameworkId/requirements/:controlId/evidence" element={<ControlEvidence />} />
            <Route path="policies" element={<PolicyList />} />
            <Route path="policies/create" element={<PolicyCreate />} />
            <Route path="policies/:policyId" element={<PolicyDetail />} />
            <Route path="organizations" element={<OrganizationList />} />
            <Route path="organizations/departments" element={<DepartmentList />} />
            <Route path="organizations/business-units" element={<BusinessUnitList />} />
            <Route path="organizations/subsidiaries" element={<SubsidiaryList />} />
            <Route path="risk" element={<div className="card"><h1>Risk Management</h1><p>Coming soon...</p></div>} />
            <Route path="integrations" element={<IntegrationsLayout />}>
              <Route index element={<IntegrationDashboard />} />
              {/* Cloud Providers */}
              <Route path="cloud-providers/aws" element={<AWSConfig />} />
              <Route path="cloud-providers/azure" element={<AzureConfig />} />
              <Route path="cloud-providers/gcp" element={<GCPConfig />} />
              {/* Identity Providers */}
              <Route path="identity-providers/okta" element={<GenericServiceConfig />} />
              {/* Version Control */}
              <Route path="version-control/github" element={<GitHubConfig />} />
              <Route path="version-control/gitlab" element={<GenericServiceConfig />} />
              <Route path="version-control/bitbucket" element={<GenericServiceConfig />} />
              {/* Endpoint Security */}
              <Route path="endpoint-security/crowdstrike" element={<GenericServiceConfig />} />
              <Route path="endpoint-security/sentinelone" element={<GenericServiceConfig />} />
              {/* Task Management */}
              <Route path="task-management/jira" element={<GenericServiceConfig />} />
              <Route path="task-management/servicenow" element={<GenericServiceConfig />} />
              <Route path="task-management/linear" element={<GenericServiceConfig />} />
              {/* Communication Platforms */}
              <Route path="communication-platforms/slack" element={<GenericServiceConfig />} />
              <Route path="communication-platforms/teams" element={<GenericServiceConfig />} />
              <Route path="communication-platforms/zoom" element={<GenericServiceConfig />} />
              {/* Observability */}
              <Route path="observability/datadog" element={<GenericServiceConfig />} />
              <Route path="observability/newrelic" element={<GenericServiceConfig />} />
              <Route path="observability/splunk" element={<GenericServiceConfig />} />
              {/* Incident Management */}
              <Route path="incident-management/pagerduty" element={<GenericServiceConfig />} />
              <Route path="incident-management/opsgenie" element={<GenericServiceConfig />} />
              {/* Data Warehouse Providers */}
              <Route path="data-warehouse-providers/snowflake" element={<GenericServiceConfig />} />
              <Route path="data-warehouse-providers/databricks" element={<GenericServiceConfig />} />
              {/* Datastore Providers */}
              <Route path="datastore-providers/mongodb" element={<GenericServiceConfig />} />
              {/* CRM Platforms */}
              <Route path="crm-platforms/salesforce" element={<GenericServiceConfig />} />
              <Route path="crm-platforms/hubspot" element={<GenericServiceConfig />} />
              {/* Catch-all for category listing pages */}
              <Route path=":integration" element={<IntegrationPlaceholder />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
