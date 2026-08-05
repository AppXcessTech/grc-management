select
  name,
  jsonb_pretty(access_approval_settings) as access_approval_settings
from
  gcp_organization_project;