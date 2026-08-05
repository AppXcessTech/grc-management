select
  name,
  listener_description -> 'Listener' ->> 'InstancePort' as instance_port,
  listener_description -> 'Listener' ->> 'InstanceProtocol' as instance_protocol,
  listener_description -> 'Listener' ->> 'LoadBalancerPort' as load_balancer_port,
  listener_description -> 'Listener' ->> 'Protocol' as load_balancer_protocol,
  listener_description -> 'SSLCertificateId' ->> 'SSLCertificateId' as ssl_certificate,
  listener_description -> 'Listener' ->> 'PolicyNames' as policy_names
from
  aws_ec2_classic_load_balancer
  cross join jsonb_array_elements(listener_descriptions) as listener_description;