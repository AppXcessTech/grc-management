select
  repository_full_name,
  creation_info
from
  github_repository_sbom
where
  (creation_info ->> 'created_by' = 'madhushreeray30' or creation_info ->> 'created_at' = '2023-11-16')
  and repository_full_name = 'turbot/steampipe';