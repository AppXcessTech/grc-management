select
  id,
  name,
  package_type,
  repository_full_name,
  visibility,
  html_url
from
  github_package
where
  organization = 'turbot'
  and visibility = 'public';