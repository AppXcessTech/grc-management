select
  name,
  arn,
  jsonb_pretty(url_config) as url_config
from
  aws_lambda_function;