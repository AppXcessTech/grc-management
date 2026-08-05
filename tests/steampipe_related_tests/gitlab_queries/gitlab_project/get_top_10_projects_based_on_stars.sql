select
  namespace_full_path as project,
  star_count
from
  gitlab_project
order by
  star_count desc
limit 10;