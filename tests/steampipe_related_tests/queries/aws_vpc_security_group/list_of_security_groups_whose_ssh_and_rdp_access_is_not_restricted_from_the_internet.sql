select
  sg.group_name,
  sg.group_id,
  sgr.type,
  sgr.ip_protocol,
  sgr.from_port,
  sgr.to_port,
  cidr_ipv4
from
  aws_vpc_security_group as sg
  join aws_vpc_security_group_rule as sgr on sg.group_id = sgr.group_id
where
  sgr.type = 'ingress'
  and sgr.cidr_ipv4 = '0.0.0.0/0'
  and (
    (
      sgr.ip_protocol = '-1' -- all traffic
      and sgr.from_port is null
    )
    or (
      sgr.from_port <= 22
      and sgr.to_port >= 22
    )
    or (
      sgr.from_port <= 3389
      and sgr.to_port >= 3389
    )
  );