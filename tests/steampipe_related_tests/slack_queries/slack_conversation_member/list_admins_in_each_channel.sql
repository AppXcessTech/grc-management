select
  c.id as conversation_id,
  c.name as conversation_name,
  u.id as user_id,
  u.real_name as user_name,
  u.email as user_email
from
  slack_conversation as c
  join
    slack_conversation_member as m
    on c.id = m.conversation_id
  join
    slack_user as u
    on m.member_id = u.id
where
  u.is_admin;