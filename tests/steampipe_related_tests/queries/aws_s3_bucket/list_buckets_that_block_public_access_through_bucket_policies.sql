select
  name,
  bucket_policy_is_public
from
  aws_s3_bucket
where
  bucket_policy_is_public;