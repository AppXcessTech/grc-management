select
  r.name,
  a.action,
  a.access_level,
  a.description
from
  aws_iam_role as r,
  jsonb_array_elements_text(r.attached_policy_arns) as pol_arn,
  aws_iam_policy as p,
  jsonb_array_elements(p.policy_std -> 'Statement') as stmt,
  jsonb_array_elements_text(stmt -> 'Action') as action_glob,
  glob(action_glob) as action_regex
  join aws_iam_action as a on a.action like action_regex
where
  pol_arn = p.arn
  and stmt ->> 'Effect' = 'Allow'
  and r.name = 'AWSServiceRoleForRDS'
  and access_level not in ('List', 'Read')
order by
  action;