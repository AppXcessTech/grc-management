select
  instance_id,
  instance_state,
  launch_time,
  maintenance_options ->> 'AutoRecovery' as auto_recovery
from
  aws_ec2_instance;