select
  detector_id,
  arn,
  created_at,
  status,
  service_role
from
  aws_guardduty_detector;