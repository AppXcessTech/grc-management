select
  runtime,
  count(*)
from
  aws_lambda_function
group by
  runtime;