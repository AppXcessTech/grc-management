select
  name,
  spdx_version
from
  github_repository_sbom
where
  spdx_version = '2.2'
  and repository_full_name = 'turbot/steampipe';