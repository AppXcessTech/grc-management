select
  id,
  company_name,
  first_observed_at,
  updated_at,
  criticality,
  verification_state
from
  aws_securityhub_finding
where
  updated_at between '2023-06-26T13:00:21+05:30' and '2024-07-04T14:45:00+05:30';