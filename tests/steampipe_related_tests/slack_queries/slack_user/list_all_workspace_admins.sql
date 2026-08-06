select
  id,
  display_name,
  real_name
from
  slack_user
where
  is_admin;