select
  name as group_name,
  inline_policies
from
  aws_iam_group
where 
  inline_policies is not null;