select
  db_cluster_identifier,
  jsonb_array_length(availability_zones) as availability_zones_count
from
  aws_docdb_cluster;