select
  arn,
  certificate ->> 'CertificateArn' as certificate_arn,
  certificate ->> 'CertificateType' as certificate_type,
  certificate ->> 'ValidFrom' as valid_from,
  certificate ->> 'ValidTill' as valid_till
from
  aws_rds_db_instance
where
  (certificate ->> 'ValidTill')::timestamp <= (current_date - interval '90' day);