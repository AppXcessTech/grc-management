select
  name,
  num_members
from
  slack_conversation
where
  num_members is not null
order by
  num_members desc
limit
  5;