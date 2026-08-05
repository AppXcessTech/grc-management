select
  id,
  package_name,
  prerelease,
  created_at,
  html_url
from
  github_package_version
where
  organization = 'turbot'
  and package_name = 'steampipe/plugin/turbot/aws'
  and prerelease = true;