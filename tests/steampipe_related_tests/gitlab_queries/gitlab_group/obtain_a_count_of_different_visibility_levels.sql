select
  visibility,
  count(id) as group_count
from
  gitlab_group
group by
  visibility