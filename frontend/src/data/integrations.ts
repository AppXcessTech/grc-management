export interface IntegrationVendor {
  name: string;
}

export interface IntegrationCategory {
  slug: string;
  name: string;
  vendors: IntegrationVendor[];
}

export const integrationCategories: IntegrationCategory[] = [
  {
    slug: 'cloud-providers',
    name: 'Cloud Providers',
    vendors: [
      { name: 'AWS' },
      { name: 'Azure' },
      { name: 'GCP' },
    ],
  },
  {
    slug: 'identity-providers',
    name: 'Identity Providers',
    vendors: [
      { name: 'Okta' },
      { name: 'Azure AD / Entra ID' },
      { name: 'Google Workspace' },
    ],
  },
  {
    slug: 'version-control',
    name: 'Version Control Systems',
    vendors: [
      { name: 'GitHub' },
      { name: 'GitLab' },
      { name: 'Bitbucket' },
    ],
  },
  {
    slug: 'vulnerability-scanners',
    name: 'Vulnerability Scanners',
    vendors: [
      { name: 'Snyk' },
      { name: 'Tenable' },
      { name: 'Qualys' },
      { name: 'AWS Inspector' },
    ],
  },
  {
    slug: 'hris',
    name: 'HRIS',
    vendors: [
      { name: 'BambooHR' },
      { name: 'Rippling' },
      { name: 'Workday' },
      { name: 'Gusto' },
    ],
  },
  {
    slug: 'endpoint-security',
    name: 'Endpoint Security',
    vendors: [
      { name: 'CrowdStrike' },
      { name: 'SentinelOne' },
    ],
  },
  {
    slug: 'mdm',
    name: 'MDM',
    vendors: [
      { name: 'Jamf' },
      { name: 'Kandji' },
      { name: 'Microsoft Intune' },
    ],
  },
  {
    slug: 'task-management',
    name: 'Task Management',
    vendors: [
      { name: 'Jira' },
      { name: 'ServiceNow' },
      { name: 'Linear' },
    ],
  },
  {
    slug: 'communication-platforms',
    name: 'Communication Platforms',
    vendors: [
      { name: 'Slack' },
      { name: 'Microsoft Teams' },
      { name: 'Zoom' },
    ],
  },
  {
    slug: 'security-training',
    name: 'Security Training',
    vendors: [
      { name: '360Learning' },
      { name: 'CanIPhish' },
      { name: 'AdaptiveSecurity' },
    ],
  },
  {
    slug: 'background-checkers',
    name: 'Background Checkers',
    vendors: [
      { name: 'Checkr' },
      { name: 'HirePass' },
    ],
  },
  {
    slug: 'observability',
    name: 'Observability',
    vendors: [
      { name: 'Datadog' },
      { name: 'New Relic' },
      { name: 'Splunk' },
    ],
  },
  {
    slug: 'incident-management',
    name: 'Incident Management',
    vendors: [
      { name: 'PagerDuty' },
      { name: 'Opsgenie' },
    ],
  },
  {
    slug: 'data-warehouse-providers',
    name: 'Data Warehouse Providers',
    vendors: [
      { name: 'Snowflake' },
      { name: 'Databricks' },
    ],
  },
  {
    slug: 'datastore-providers',
    name: 'Datastore Providers',
    vendors: [
      { name: 'MongoDB' },
    ],
  },
  {
    slug: 'crm-platforms',
    name: 'CRM Platforms',
    vendors: [
      { name: 'Salesforce' },
      { name: 'HubSpot' },
    ],
  },
  {
    slug: 'document-management',
    name: 'Document Management',
    vendors: [
      { name: 'Google Drive' },
      { name: 'SharePoint' },
      { name: 'Box' },
    ],
  },
  {
    slug: 'audit-management',
    name: 'Audit Management Solutions',
    vendors: [
      { name: 'External CPA / Auditing Firms' },
    ],
  },
];

export function getCategoryBySlug(slug: string): IntegrationCategory | undefined {
  return integrationCategories.find((c) => c.slug === slug);
}
