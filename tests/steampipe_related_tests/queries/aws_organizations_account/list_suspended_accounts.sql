select
  id,
  name,
  arn,
  email,
  joined_method,
  joined_timestamp,
  status
from
  aws_organizations_account
where
  status = 'SUSPENDED';