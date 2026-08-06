select
  g.name as group_name,
  u.email as user_email
from
  slack_group as g
  left join lateral jsonb_array_elements_text(g.users) as gu on true
  left join lateral (
    select
      id,
      email
    from
      slack_user
  ) as u on u.id = gu
order by
  g.name,
  u.email;