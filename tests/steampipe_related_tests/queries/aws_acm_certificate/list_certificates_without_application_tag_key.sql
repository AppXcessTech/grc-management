select
  certificate_arn,
  tags
from
  aws_acm_certificate
where
  not tags :: JSONB ? 'application';