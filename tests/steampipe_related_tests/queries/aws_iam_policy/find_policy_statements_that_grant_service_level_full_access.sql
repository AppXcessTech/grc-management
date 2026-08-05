select
  name,
  arn,
  action,
  s ->> 'Effect' as effect
from
  aws_iam_policy,
  jsonb_array_elements(policy_std -> 'Statement') as s,
  jsonb_array_elements_text(s -> 'Action') as action
where
  s ->> 'Effect' = 'Allow'
  and (
    action = '*'
    or action like '%:*'
  );