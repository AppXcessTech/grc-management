select
  runtime,
  count(*)
from
  gcp_cloudfunctions_function
group by
  runtime;