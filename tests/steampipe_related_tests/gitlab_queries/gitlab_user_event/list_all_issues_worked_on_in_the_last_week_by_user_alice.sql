select
  project.full_path, 
  event.target_iid, 
  event.action_name
from
  gitlab_user_event as event, 
  gitlab_project as project, 
  gitlab_user as u
where
  event.project_id = project.id 
  and target_type = 'Issue' 
  and event.created_at > current_date - interval '7 days' 
  and event.author_id = u.id 
  and u.username = 'alice';