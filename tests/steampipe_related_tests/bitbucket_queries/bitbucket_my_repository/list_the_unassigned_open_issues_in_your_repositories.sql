select
  i.repository_full_name,
  i.id,
  i.title,
  i.state,
  i.assignee_display_name,
  i.assignee_uuid
from
  bitbucket_issue as i,
  bitbucket_my_repository as r
where
  repository_full_name = r.full_name
  and i.assignee_uuid is null
  and i.state = 'new';