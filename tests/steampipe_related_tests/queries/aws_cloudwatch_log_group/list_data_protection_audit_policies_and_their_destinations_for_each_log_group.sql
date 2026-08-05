select
  i as data_identifier,
  s -> 'Operation' -> 'Audit' -> 'FindingsDestination' -> 'S3' -> 'Bucket' as  destination_bucket,
  s -> 'Operation' -> 'Audit' -> 'FindingsDestination' -> 'CloudWatchLogs' -> 'LogGroup'as destination_log_group,
  s -> 'Operation' -> 'Audit' -> 'FindingsDestination' -> 'Firehose' -> 'DeliveryStream'as destination_delivery_stream
from
  aws_cloudwatch_log_group,
  jsonb_array_elements(data_protection_policy -> 'Statement') as s,
  jsonb_array_elements_text(s -> 'DataIdentifier') as i
where
  s ->> 'Sid' = 'audit-policy'
  and name = 'log-group-name';