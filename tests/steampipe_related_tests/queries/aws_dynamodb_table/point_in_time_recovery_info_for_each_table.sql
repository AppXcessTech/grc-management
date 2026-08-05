select
  name,
  point_in_time_recovery_description ->> 'EarliestRestorableDateTime' as earliest_restorable_date_time,
  point_in_time_recovery_description ->> 'LatestRestorableDateTime' as latest_restorable_date_time,
  point_in_time_recovery_description ->> 'PointInTimeRecoveryStatus' as point_in_time_recovery_status
from
  aws_dynamodb_table;