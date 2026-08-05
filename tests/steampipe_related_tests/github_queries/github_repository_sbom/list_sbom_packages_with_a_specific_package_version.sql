select
  spdx_id,
  spdx_version,
  p ->> 'name' as package_name,
  p ->> 'versionInfo' as package_version,
  p ->> 'licenseConcluded' as package_license
from
  github_repository_sbom,
  jsonb_array_elements(packages) p
where
  p ->> 'versionInfo' = '2.6.0'
  and repository_full_name = 'turbot/steampipe';