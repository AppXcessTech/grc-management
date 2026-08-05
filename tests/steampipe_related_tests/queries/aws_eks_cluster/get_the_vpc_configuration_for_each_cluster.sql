select
  name,
  resources_vpc_config ->> 'ClusterSecurityGroupId' as cluster_security_group_id,
  resources_vpc_config ->> 'EndpointPrivateAccess' as endpoint_private_access,
  resources_vpc_config ->> 'EndpointPublicAccess' as endpoint_public_access,
  resources_vpc_config ->> 'PublicAccessCidrs' as public_access_cidrs,
  resources_vpc_config ->> 'SecurityGroupIds' as security_group_ids,
  resources_vpc_config -> 'SubnetIds' as subnet_ids,
  resources_vpc_config ->> 'VpcId' as vpc_id
from
  aws_eks_cluster;