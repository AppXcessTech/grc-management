select
  user_name,
  access_key_1_last_rotated,
  age(access_key_1_last_rotated) as access_key_1_age,
  access_key_2_last_rotated,
  age(access_key_2_last_rotated) as access_key_2_age
from
  aws_iam_credential_report
where
  access_key_1_last_rotated <= (current_date - interval '90' day)
  or access_key_2_last_rotated <= (current_date - interval '90' day)
order by
  user_name;