select
  name,
  data_license
from
  github_repository_sbom
where
  data_license = 'CC0-1.0'
  and repository_full_name = 'turbot/steampipe';