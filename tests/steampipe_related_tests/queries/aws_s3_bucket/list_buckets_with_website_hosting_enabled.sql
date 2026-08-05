select
  name,
  website_configuration -> 'IndexDocument' ->> 'Suffix' as suffix
from
  aws_s3_bucket
where
  website_configuration -> 'IndexDocument' ->> 'Suffix' is not null;