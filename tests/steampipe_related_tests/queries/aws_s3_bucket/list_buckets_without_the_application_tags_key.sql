select
  name,
  tags ->> 'fizz' as fizz
from
  aws_s3_bucket
where
  tags ->> 'application' is null;