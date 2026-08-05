select
  name,
  logging ->> 'TargetBucket' as target_bucket
from
  aws_s3_bucket
where
  logging ->> 'TargetBucket' = name;