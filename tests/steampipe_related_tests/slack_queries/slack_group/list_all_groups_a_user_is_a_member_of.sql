select
  g.id,
  g.name
from
  slack_group as g,
  slack_user as u
where
  g.users ? u.id
  and u.email = 'dwight.schrute@dundermifflin.com';