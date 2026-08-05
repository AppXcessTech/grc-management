select
  name as user_name,
  split_part(attachments, '/', 2) as attached_policies
from
  aws_iam_user
  cross join jsonb_array_elements_text(attached_policy_arns) as attachments
where
  split_part(attachments, '/', 2) = 'AdministratorAccess';