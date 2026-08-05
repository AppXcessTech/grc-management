select
  m.team_id,
  t.display_name as team_name,
  m.member_id,
  m.tenant_id
from
  microsoft365_team_member as m
  left join microsoft365_team as t on m.team_id = t.id;
