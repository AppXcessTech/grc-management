select
  package_name,
  package_type,
  name as digest,
  visibility,
  created_at,
  updated_at
from
  github_package_version
where
  organization = 'turbot'
  and visibility = 'public';