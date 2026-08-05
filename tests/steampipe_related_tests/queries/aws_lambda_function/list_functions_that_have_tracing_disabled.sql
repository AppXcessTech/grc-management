select
  name,
  arn,
  jsonb_pretty(tracing_config) as tracing_config
from
  aws_lambda_function
where
  tracing_config ->> 'Mode' = 'PassThrough';