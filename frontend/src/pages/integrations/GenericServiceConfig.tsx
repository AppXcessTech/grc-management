import { useLocation } from 'react-router-dom';
import IntegrationConfigForm from '../../components/IntegrationConfigForm';
import type { FieldDef } from '../../components/IntegrationConfigForm';

interface VendorConfig {
  title: string;
  categoryLabel: string;
  fields: FieldDef[];
}

const VENDOR_CONFIGS: Record<string, VendorConfig> = {
  gcp: {
    title: 'GCP',
    categoryLabel: 'Cloud Providers',
    fields: [
      { name: 'project', label: 'Project ID', type: 'text', required: true, placeholder: 'my-gcp-project-123' },
      { name: 'credentials', label: 'Service Account Credentials (JSON)', type: 'text', required: true, placeholder: '/path/to/service-account-creds.json' },
      { name: 'region', label: 'Region', type: 'text', required: false, defaultValue: 'us-central1', placeholder: 'us-central1', hint: 'Default GCP region for resource discovery.' },
    ],
  },
  okta: {
    title: 'Okta',
    categoryLabel: 'Identity Providers',
    fields: [
      { name: 'okta_domain', label: 'Okta Domain', type: 'text', required: true, placeholder: 'dev-123456.okta.com' },
      { name: 'okta_token', label: 'Okta API Token', type: 'password', required: true, placeholder: '00sampleTokenAbCdEfGhIjKlMnOpQrStUvWxYz' },
    ],
  },
  github: {
    title: 'GitHub',
    categoryLabel: 'Version Control Systems',
    fields: [
      { name: 'token', label: 'Personal Access Token', type: 'password', required: true, placeholder: 'ghp_yourPersonalAccessToken' },
    ],
  },
  gitlab: {
    title: 'GitLab',
    categoryLabel: 'Version Control Systems',
    fields: [
      { name: 'baseurl', label: 'GitLab Base URL', type: 'text', required: true, defaultValue: 'https://gitlab.com/api/v4', placeholder: 'https://gitlab.mycompany.com/api/v4' },
      { name: 'token', label: 'Personal Access Token', type: 'password', required: true, placeholder: 'glpat_yourPersonalAccessToken', hint: "Fine-grained tokens need 'Project: Read' and 'Group: Read' user permissions; classic tokens need the 'read_api' scope." },
    ],
  },
  bitbucket: {
    title: 'Bitbucket',
    categoryLabel: 'Version Control Systems',
    fields: [
      { name: 'base_url', label: 'Base URL', type: 'text', required: false, defaultValue: 'https://api.bitbucket.org/2.0', placeholder: 'https://api.bitbucket.org/2.0', hint: 'Bitbucket Cloud REST API base. Defaults to https://api.bitbucket.org/2.0.' },
      { name: 'username', label: 'Email', type: 'text', required: true, placeholder: 'your-atlassian-account-email@example.com', hint: 'Your Atlassian account email — required for API-token authentication (the Bitbucket username will NOT work with API tokens).' },
      { name: 'password', label: 'API Token', type: 'password', required: true, placeholder: 'your-api-token', hint: 'Create an API token at bitbucket.org → Account settings → API tokens. App passwords were removed on July 28, 2026. Grant scopes: Account: Read, Workspace: Read, Workspace membership: Read, Project: Read, Repository: Read (add Repository: Admin for branch restrictions).' },
      { name: 'workspace_slug', label: 'Workspace Slug', type: 'text', required: true, placeholder: 'my-company', hint: 'Required — Bitbucket deprecated workspace-listing endpoints, so discovery must be scoped to one workspace. Use the slug from bitbucket.org/my-company (e.g. "my-company").' },
    ],
  },
  crowdstrike: {
    title: 'CrowdStrike',
    categoryLabel: 'Endpoint Security',
    fields: [
      { name: 'client_id', label: 'Client ID', type: 'text', required: true, placeholder: 'your-client-id' },
      { name: 'client_secret', label: 'Client Secret', type: 'password', required: true, placeholder: 'your-client-secret' },
      { name: 'member_cid', label: 'Member CID (optional)', type: 'text', required: false, placeholder: 'your-member-cid', hint: 'Required for MSSP/multi-tenant setups.' },
      { name: 'cloud', label: 'Cloud', type: 'text', required: false, defaultValue: 'us-1', placeholder: 'us-1', hint: 'us-1, us-2, us-gov-1, eu-1, etc.' },
    ],
  },
  sentinelone: {
    title: 'SentinelOne',
    categoryLabel: 'Endpoint Security',
    fields: [
      { name: 'url', label: 'Console URL', type: 'text', required: true, placeholder: 'https://your-instance.sentinelone.net' },
      { name: 'api_key', label: 'API Token', type: 'password', required: true, placeholder: 'your-api-token' },
    ],
  },
  jira: {
    title: 'Jira',
    categoryLabel: 'Task Management',
    fields: [
      { name: 'base_url', label: 'Jira Base URL', type: 'text', required: true, placeholder: 'https://yourcompany.atlassian.net' },
      { name: 'username', label: 'Email', type: 'text', required: true, placeholder: 'your-email@example.com' },
      { name: 'token', label: 'API Token', type: 'password', required: true, placeholder: 'your-api-token' },
    ],
  },
  servicenow: {
    title: 'ServiceNow',
    categoryLabel: 'Task Management',
    fields: [
      { name: 'instance_url', label: 'Instance URL', type: 'text', required: true, placeholder: 'https://yourinstance.service-now.com' },
      { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'your-username' },
      { name: 'password', label: 'Password', type: 'password', required: true, placeholder: 'your-password' },
    ],
  },
  linear: {
    title: 'Linear',
    categoryLabel: 'Task Management',
    fields: [
      { name: 'token', label: 'API Key', type: 'password', required: true, placeholder: 'lin_api_yourApiKey' },
    ],
  },
  slack: {
    title: 'Slack',
    categoryLabel: 'Communication Platforms',
    fields: [
      { name: 'token', label: 'Bot / User Token', type: 'password', required: true, placeholder: 'xoxp-your-user-or-bot-token' },
    ],
  },
  teams: {
    title: 'Microsoft Teams',
    categoryLabel: 'Communication Platforms',
    fields: [
      { name: 'tenant_id', label: 'Tenant ID', type: 'text', required: true, placeholder: 'your-tenant-id' },
      { name: 'client_id', label: 'Client ID', type: 'text', required: true, placeholder: 'your-app-client-id' },
      { name: 'client_secret', label: 'Client Secret', type: 'password', required: true, placeholder: 'your-client-secret' },
    ],
  },
  zoom: {
    title: 'Zoom',
    categoryLabel: 'Communication Platforms',
    fields: [
      { name: 'account_id', label: 'Account ID', type: 'text', required: true, placeholder: 'your-account-id' },
      { name: 'client_id', label: 'Client ID', type: 'text', required: true, placeholder: 'your-client-id' },
      { name: 'client_secret', label: 'Client Secret', type: 'password', required: true, placeholder: 'your-client-secret' },
    ],
  },
  datadog: {
    title: 'Datadog',
    categoryLabel: 'Observability',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'your-api-key' },
      { name: 'app_key', label: 'Application Key', type: 'password', required: true, placeholder: 'your-app-key' },
      { name: 'api_url', label: 'API URL', type: 'text', required: false, defaultValue: 'https://api.datadoghq.com', placeholder: 'https://api.datadoghq.com', hint: 'Adjust for EU/other regions: https://api.datadoghq.eu' },
    ],
  },
  newrelic: {
    title: 'New Relic',
    categoryLabel: 'Observability',
    fields: [
      { name: 'account_id', label: 'Account ID', type: 'text', required: true, placeholder: 'your-account-id' },
      { name: 'api_key', label: 'User API Key', type: 'password', required: true, placeholder: 'your-user-api-key' },
      { name: 'region', label: 'Region', type: 'text', required: false, defaultValue: 'US', placeholder: 'US', hint: 'US or EU' },
    ],
  },
  splunk: {
    title: 'Splunk',
    categoryLabel: 'Observability',
    fields: [
      { name: 'url', label: 'Splunk URL', type: 'text', required: true, placeholder: 'https://your-splunk-instance:8089' },
      { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'your-username' },
      { name: 'password', label: 'Password', type: 'password', required: true, placeholder: 'your-password' },
    ],
  },
  opsgenie: {
    title: 'Opsgenie',
    categoryLabel: 'Incident Management',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'your-api-key' },
    ],
  },
  pagerduty: {
    title: 'PagerDuty',
    categoryLabel: 'Incident Management',
    fields: [
      { name: 'token', label: 'API Token', type: 'password', required: true, placeholder: 'your-api-token' },
    ],
  },
  snowflake: {
    title: 'Snowflake',
    categoryLabel: 'Data Warehouse Providers',
    fields: [
      { name: 'account', label: 'Account Identifier', type: 'text', required: true, placeholder: 'xy12345.us-east-1' },
      { name: 'user', label: 'Username', type: 'text', required: true, placeholder: 'your-username' },
      { name: 'password', label: 'Password', type: 'password', required: true, placeholder: 'your-password' },
      { name: 'database', label: 'Database', type: 'text', required: true, placeholder: 'your-database' },
      { name: 'warehouse', label: 'Warehouse', type: 'text', required: true, placeholder: 'your-warehouse' },
      { name: 'role', label: 'Role (optional)', type: 'text', required: false, placeholder: 'your-role' },
    ],
  },
  databricks: {
    title: 'Databricks',
    categoryLabel: 'Data Warehouse Providers',
    fields: [
      { name: 'host', label: 'Workspace URL', type: 'text', required: true, placeholder: 'https://your-workspace.cloud.databricks.com' },
      { name: 'token', label: 'Personal Access Token', type: 'password', required: true, placeholder: 'your-personal-access-token' },
      { name: 'account_id', label: 'Account ID (optional)', type: 'text', required: false, placeholder: 'your-account-id', hint: 'For account-level resources.' },
    ],
  },
  mongodb: {
    title: 'MongoDB',
    categoryLabel: 'Datastore Providers',
    fields: [
      { name: 'connection_string', label: 'Connection String', type: 'password', required: true, placeholder: 'mongodb://username:password@host:port/database?authSource=admin' },
    ],
  },
  salesforce: {
    title: 'Salesforce',
    categoryLabel: 'CRM Platforms',
    fields: [
      { name: 'url', label: 'Instance URL', type: 'text', required: true, placeholder: 'https://your-instance.salesforce.com' },
      { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'your-username' },
      { name: 'password', label: 'Password', type: 'password', required: true, placeholder: 'your-password' },
      { name: 'token', label: 'Security Token (optional)', type: 'password', required: false, placeholder: 'your-security-token' },
    ],
  },
  hubspot: {
    title: 'HubSpot',
    categoryLabel: 'CRM Platforms',
    fields: [
      { name: 'token', label: 'Private App Access Token', type: 'password', required: true, placeholder: 'your-private-app-access-token' },
    ],
  },
};

const GenericServiceConfig = () => {
  const location = useLocation();
  const pathParts = location.pathname.split('/').filter(Boolean);
  const vendorSlug = pathParts[pathParts.length - 1]?.toLowerCase();

  // Get the second-to-last segment for the back path (category slug)
  const categorySlug = pathParts[pathParts.length - 2] || '';
  const config = vendorSlug ? VENDOR_CONFIGS[vendorSlug] : undefined;

  // Determine back path
  const backPath = `/integrations/${categorySlug}`;

  if (!config) {
    return (
      <div className="card">
        <h1>Integration Not Found</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          No configuration page available for <strong>{vendorSlug}</strong> in this category.
        </p>
      </div>
    );
  }

  return (
    <IntegrationConfigForm
      title={config.title}
      categoryLabel={config.categoryLabel}
      backPath={backPath}
      apiPath={`/api/integrations/generic/${vendorSlug}`}
      fields={config.fields}
    />
  );
};

export default GenericServiceConfig;
