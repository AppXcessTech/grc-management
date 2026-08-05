select
  slug,
  organization,
  parent_team ->> 'id' as parent_team_id,
  parent_team ->> 'node_id' as parent_team_node_id,
  parent_team ->> 'slug' as parent_team_slug
from
  github_team
where
  organization = 'turbot'
  and parent_team is not null;