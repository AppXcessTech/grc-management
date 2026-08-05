select
  name,
  arn,
  handler,
  kms_key_arn
from
  aws_lambda_function;