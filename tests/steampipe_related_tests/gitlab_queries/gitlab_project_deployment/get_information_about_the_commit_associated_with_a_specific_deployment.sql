select
  d.id,
  d.environment_name,
  c.author_email,
  c.short_id,
  c.title,
  c.message
from
  gitlab_project_deployment d
left outer join 
  gitlab_commit c
on
  d.project_id = c.project_id
and
  d.deployable_commit_id = c.id
where
  d.project_id = 14597683;