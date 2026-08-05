select
  detector_id,
  created_at,
  status
from
  aws_guardduty_detector
where
  status = 'ENABLED';