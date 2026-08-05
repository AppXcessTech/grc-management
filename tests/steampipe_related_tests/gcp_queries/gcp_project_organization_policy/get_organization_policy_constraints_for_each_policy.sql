select
  id,
  version,
  list_policy ->> 'allValues' as policy_value
from
  gcp_project_organization_policy;