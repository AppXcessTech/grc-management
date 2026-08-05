select
  organization_id,
  jsonb_pretty(essential_contacts) as essential_contacts
from
  gcp_organization;