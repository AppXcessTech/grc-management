select
  name,
  uuid,
  full_name,
  owner_display_name
from
  bitbucket_my_repository
order by
  full_name;