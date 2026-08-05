select
  trail.name as trail_name,
  bucket.name as bucket_name,
  logging
from
  aws_cloudtrail_trail as trail
  join aws_s3_bucket as bucket on trail.s3_bucket_name = bucket.name
where
  not versioning_enabled;