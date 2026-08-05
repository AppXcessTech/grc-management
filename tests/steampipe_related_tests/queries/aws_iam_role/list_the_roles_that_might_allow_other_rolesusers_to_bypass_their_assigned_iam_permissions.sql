select
  r.name,
  stmt
from
  aws_iam_role as r,
  jsonb_array_elements(r.assume_role_policy_std -> 'Statement') as stmt,
  jsonb_array_elements_text(stmt -> 'Principal' -> 'AWS') as trust
where
  trust = '*'
  or trust like 'arn:aws:iam::%:role/%'