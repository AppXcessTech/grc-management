select
  name,
  server_side_encryption_configuration
from
  aws_s3_bucket
where
  server_side_encryption_configuration is null;