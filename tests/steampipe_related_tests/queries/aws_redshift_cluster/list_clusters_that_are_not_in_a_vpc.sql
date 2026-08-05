select
  cluster_identifier,
  node_type,
  number_of_nodes,
  vpc_id
from
  aws_redshift_cluster
where
  vpc_id is null;