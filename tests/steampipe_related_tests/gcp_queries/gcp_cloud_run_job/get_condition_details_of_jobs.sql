select
  name,
  c ->> 'ExecutionReason' as execution_reason,
  c ->> 'LastTransitionTime' as last_transition_time,
  c ->> 'Message' as message,
  c ->> 'Reason' as reason,
  c ->> 'RevisionReason' as revision_reason,
  c ->> 'State' as state,
  c ->> 'Type' as type
from
  gcp_cloud_run_job,
  jsonb_array_elements(conditions) as c;