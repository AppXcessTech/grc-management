select
  hub_arn,
  auto_enable_controls
from
  aws_securityhub_hub
where
  not auto_enable_controls;