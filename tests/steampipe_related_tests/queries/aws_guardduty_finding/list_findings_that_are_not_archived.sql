select
  id,
  detector_id,
  arn,
  created_at
from
  aws_guardduty_finding
where
  service ->> 'Archived' = 'false';