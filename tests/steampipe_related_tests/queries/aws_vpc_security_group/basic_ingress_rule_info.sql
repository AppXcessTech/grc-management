select
  group_name,
  vpc_id,
  perm ->> 'FromPort' as from_port,
  perm ->> 'ToPort' as to_port,
  perm ->> 'IpProtocol' as ip_protocol,
  perm ->> 'IpRanges' as ip_ranges,
  perm ->> 'Ipv6Ranges' as ipv6_ranges,
  perm ->> 'UserIdGroupPairs' as user_id_group_pairs,
  perm ->> 'PrefixListIds' as prefix_list_ids
from
  aws_vpc_security_group as sg
  cross join jsonb_array_elements(ip_permissions) as perm;