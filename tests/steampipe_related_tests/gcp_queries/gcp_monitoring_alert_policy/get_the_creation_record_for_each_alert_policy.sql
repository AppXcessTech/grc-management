select
  display_name,
  name,
  creation_record ->> 'mutateTime' as mutation_time,
  creation_record ->> 'mutatedBy' as mutated_by
from
  gcp_monitoring_alert_policy;