select
  u.username as creator,
  p.full_path as project,
  p.created_at as created
from
  gitlab_my_project p
inner join
  gitlab_user u
on 
  p.creator_id = u.id;