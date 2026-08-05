select
  name,
  jsonb_array_elements_text(package_version->'versions') as version
from
  github_package
where
  organization = 'turbot'
  and name = 'steampipe/plugin/turbot/aws';