select
  id,
  name,
  user_count
from
  slack_group
where
  deleted_by is not null;