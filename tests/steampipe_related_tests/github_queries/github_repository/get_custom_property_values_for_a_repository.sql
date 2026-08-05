select
  full_name,
  custom_properties
from
  github_repository
where
  full_name = 'my-org/my-repo';