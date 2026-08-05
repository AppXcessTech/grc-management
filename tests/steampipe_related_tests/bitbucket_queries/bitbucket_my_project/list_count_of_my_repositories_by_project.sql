select
  count(r.project_key),
  p.key as project_key,
  p.name as project_name,
  p.owner_display_name
from
  bitbucket_my_project as p
  left join bitbucket_my_repository as r on r.project_key = p.key
group by
  p.key,
  p.name,
  p.owner_display_name
order by
  count,
  p.name;