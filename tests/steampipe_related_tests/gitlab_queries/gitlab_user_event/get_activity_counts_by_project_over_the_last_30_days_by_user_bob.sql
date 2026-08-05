select
  project.full_path, 
  count(project.full_path) as events
from
  gitlab_user_event as event, 
  gitlab_project as project,
  gitlab_user as u
where
  event.project_id = project.id 
  and event.created_at > current_date - interval '30 days' 
  and event.author_id = u.id 
  and u.username = 'bob'
group by
  project.full_path
order by
  events;