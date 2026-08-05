select
  title,
  id,
  network ->> 'DestinationDomain' as network_destination_domain,
  network ->> 'DestinationIpV4' as network_destination_ip_v4,
  network ->> 'DestinationIpV6' as network_destination_ip_v6,
  network ->> 'DestinationPort' as network_destination_port,
  network ->> 'Protocol' as network_protocol,
  network ->> 'SourceIpV4' as network_source_ip_v4,
  network ->> 'SourceIpV6' as network_source_ip_v6,
  network ->> 'SourcePort' as network_source_port
from
  aws_securityhub_finding
where
  title = 'EC2 instance involved in SSH brute force attacks.';