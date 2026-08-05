select
  fn.name,
  lg.name,
  lg.retention_in_days
from
  aws_lambda_function as fn
  inner join aws_cloudwatch_log_group as lg on (
    (lg.name = '/aws/lambda/')
    or (lg.name = fn.name)
  )
where
  lg.retention_in_days < 30;