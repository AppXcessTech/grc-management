select
  name as user_name,
  iam_group ->> 'GroupName' as group_name,
  iam_group ->> 'GroupId' as group_id,
  iam_group ->> 'CreateDate' as create_date
from
  aws_iam_user
  cross join jsonb_array_elements(groups) as iam_group;