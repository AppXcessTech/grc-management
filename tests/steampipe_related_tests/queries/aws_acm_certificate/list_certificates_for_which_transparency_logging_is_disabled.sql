select
  certificate_arn,
  domain_name,
  status
from
  aws_acm_certificate
where
  certificate_transparency_logging_preference <> 'ENABLED';