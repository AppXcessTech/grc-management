select
  a.db_instance_identifier,
  b.action,
  a.status,
  b.opt_in_status,
  b.forced_apply_date,
  b.current_apply_date,
  b.auto_applied_after_date
from 
  aws_rds_db_instance as a
  join aws_rds_pending_maintenance_action as b on b.resource_identifier = a.arn;