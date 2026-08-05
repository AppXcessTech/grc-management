select
  bucket,
  name as object_name,
  a ->> 'entity' as entity,
  a ->> 'role' as role,
  a ->> 'email' as email,
  a ->> 'domain' as domain,
  a ->> 'projectTeam' as project_team
from
  gcp_storage_object,
  jsonb_array_elements(acl) as a
where
  bucket = 'steampipe-test';