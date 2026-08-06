select
  id,
  real_name
from
  slack_user
where
  is_ultra_restricted;