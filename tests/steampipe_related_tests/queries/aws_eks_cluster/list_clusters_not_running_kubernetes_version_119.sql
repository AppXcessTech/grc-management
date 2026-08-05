select
  name,
  arn,
  version
from
  aws_eks_cluster
where
  version <> '1.19';