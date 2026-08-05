select
  id,
  package_name,
  name as digest,
  prerelease,
  created_at,
  visibility
from
  github_package_version
where
  organization = 'turbot'
  and package_name = 'steampipe/plugin/turbot/aws';