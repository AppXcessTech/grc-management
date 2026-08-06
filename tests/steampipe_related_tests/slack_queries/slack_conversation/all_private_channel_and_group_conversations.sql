select
  name,
  created,
  is_channel,
  is_group,
  is_private
from
  slack_conversation
where
  is_private
  and (
    is_channel
    or (
      is_group
      and not is_mpim
    )
  )
order by
  name;