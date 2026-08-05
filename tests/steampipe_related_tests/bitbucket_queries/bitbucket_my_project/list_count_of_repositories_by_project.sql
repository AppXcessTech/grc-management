select
  count(*),
  project_key,
  project_name,
  owner_display_name
from
  bitbucket_my_repository
group by
  project_key,
  project_name,
  owner_display_name
order by
  project_name;