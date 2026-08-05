select
  organization,
  count(*) as variable_count
from
  github_actions_organization_variable
where
  organization in ('org-1', 'org-2', 'org-3')
group by
  organization;