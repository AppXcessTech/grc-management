select
  r.name as role_name,
  p.name as policy_name,
  stmt ->> 'Sid' as statement,
  action
from
  aws_iam_role as r,
  jsonb_array_elements_text(r.attached_policy_arns) as policy_arn,
  aws_iam_policy as p,
  jsonb_array_elements(p.policy_std -> 'Statement') as stmt,
  jsonb_array_elements_text(stmt -> 'Action') as action
where
  r.name = 'owner'
  and policy_arn = p.arn
  and (
    action like '%*%'
    or action like '%?%'
  );