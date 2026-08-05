select
  db_cluster_identifier,
  member ->> 'DBClusterParameterGroupStatus' as db_cluster_parameter_group_status,
  member ->> 'DBInstanceIdentifier' as db_instance_identifier,
  member ->> 'IsClusterWriter' as is_cluster_writer,
  member ->> 'PromotionTier' as promotion_tier
from
  aws_docdb_cluster
  cross join jsonb_array_elements(members) as member;