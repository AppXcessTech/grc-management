select
  name,
  is_private,
  full_name,
  owner_display_name
from
  bitbucket_my_repository
where
  not is_private;