select
  id,
  package_name,
  jsonb_pretty(metadata) as metadata
from
  github_package_version
where
  organization = 'turbot'
  and package_name = 'steampipe/plugin/turbot/aws'
  and id = 12345;