select
  name,
  display_name,
  ((threshold_rule ->> 'thresholdPercent')::numeric) * 100 || '%' as threshold_percent,
  threshold_rule ->> 'spendBasis' as spend_basis
from
  gcp_billing_budget,
  jsonb_array_elements(threshold_rules) as threshold_rule;