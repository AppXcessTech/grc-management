select
  arn,
  source,
  vendor_severity,
  status,
  severity
from
  aws_inspector2_finding
where
  severity = 'HIGH';