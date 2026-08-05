select
  name,
  is_logging
from
  aws_cloudtrail_trail
where
  not is_logging;