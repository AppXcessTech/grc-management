select
  name,
  p as principal,
  a as action,
  s ->> 'Effect' as effect,
  s ->> 'Condition' as conditions,
  ssl
from
  aws_s3_bucket,
  jsonb_array_elements(policy_std -> 'Statement') as s,
  jsonb_array_elements_text(s -> 'Principal' -> 'AWS') as p,
  jsonb_array_elements_text(s -> 'Action') as a,
  jsonb_array_elements_text(
    s -> 'Condition' -> 'Bool' -> 'aws:securetransport'
  ) as ssl
where
  p = '*'
  and s ->> 'Effect' = 'Deny'
  and ssl :: bool = false;