select
  name,
  arn,
  region,
  home_region
from
  aws_cloudtrail_trail
where
  is_multi_region_trail
  and home_region <> region;