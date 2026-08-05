select
  name,
  kms_key_arn
from
  aws_lambda_function
where
  kms_key_arn is null;