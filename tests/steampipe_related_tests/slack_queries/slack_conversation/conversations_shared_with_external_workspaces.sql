select
  id,
  name,
  is_shared
from
  slack_conversation
where
  is_ext_shared;