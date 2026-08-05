select
  trail.name as trail_name,
  bucket.name as bucket_name,
  bucket.bucket_policy_is_public as is_publicly_accessible
from
  aws_cloudtrail_trail as trail
  join aws_s3_bucket as bucket on trail.s3_bucket_name = bucket.name
where
  bucket.bucket_policy_is_public;