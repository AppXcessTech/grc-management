select
  cluster_identifier,
  logging_status -> 'LoggingEnabled' as LoggingEnabled
from
  aws_redshift_cluster