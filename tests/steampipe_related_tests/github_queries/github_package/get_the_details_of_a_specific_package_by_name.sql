select
  id,
  name,
  package_type,
  repository_full_name,
  created_at,
  updated_at,
  url
from
  github_package
where
  organization = 'turbot'
  and name = 'steampipe/plugin/turbot/aws';