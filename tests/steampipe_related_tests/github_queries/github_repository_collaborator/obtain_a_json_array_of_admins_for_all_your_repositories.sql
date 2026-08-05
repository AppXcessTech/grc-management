with repos as (
  select
    name_with_owner
  from
    github_my_repository
)
select
  r.name_with_owner as repo,
  json_agg(user_login) as admins
from
  repos as r
  inner join github_repository_collaborator as c on r.name_with_owner = c.repository_full_name and c.permission = 'ADMIN'
group by
  r.name_with_owner;