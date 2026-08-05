select
  name,
  count(az ->> 'ZoneName') as zone_count
from
  aws_ec2_network_load_balancer
  cross join jsonb_array_elements(availability_zones) as az
group by
  name;