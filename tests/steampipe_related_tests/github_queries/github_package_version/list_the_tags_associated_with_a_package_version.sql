select
  id,
  package_name,
  jsonb_array_elements_text(tags) as tag
from
  github_package_version
where
  organization = 'turbot'
  and package_name = 'steampipe/plugin/turbot/aws'
  and id = 12345;