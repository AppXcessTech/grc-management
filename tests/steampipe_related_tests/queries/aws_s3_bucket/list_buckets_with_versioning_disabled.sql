select
  name,
  region,
  account_id,
  versioning_enabled
from
  aws_s3_bucket
where
  not versioning_enabled;