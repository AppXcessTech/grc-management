select
  conversation_id,
  member_id
from
  slack_conversation_member
where
  conversation_id in (select id from slack_conversation where is_general);