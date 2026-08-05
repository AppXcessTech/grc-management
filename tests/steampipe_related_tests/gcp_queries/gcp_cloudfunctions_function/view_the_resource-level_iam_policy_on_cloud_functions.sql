select
  name,
  jsonb_pretty(iam_policy)
from
  gcp_cloudfunctions_function;