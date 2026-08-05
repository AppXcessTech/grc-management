select
  certificate_arn,
  domain_name,
  status
from
  aws_acm_certificate
where
  status = 'EXPIRED';