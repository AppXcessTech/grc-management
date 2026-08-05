select
  arn,
  dead_letter_config_target_arn
from
  aws_lambda_function
where
  dead_letter_config_target_arn is null;