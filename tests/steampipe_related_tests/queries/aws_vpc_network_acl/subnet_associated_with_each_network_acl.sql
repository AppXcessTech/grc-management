select
  network_acl_id,
  vpc_id,
  association ->> 'SubnetId' as subnet_id,
  association ->> 'NetworkAclAssociationId' as network_acl_association_id
from
  aws_vpc_network_acl
  cross join jsonb_array_elements(associations) as association;