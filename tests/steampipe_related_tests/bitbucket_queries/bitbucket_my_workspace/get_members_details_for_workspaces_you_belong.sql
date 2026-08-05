select
  u.display_name as member_name,
  u.uuid as user_uuid,
  w.name as workspace,
  u.workspace_slug,
  u.account_id
from
  bitbucket_workspace_member as u,
  bitbucket_my_workspace as w
where
  w.slug = u.workspace_slug
order by
  w.slug;