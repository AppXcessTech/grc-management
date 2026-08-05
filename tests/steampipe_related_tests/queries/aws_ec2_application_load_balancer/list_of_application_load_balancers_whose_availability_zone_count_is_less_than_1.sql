select
  name,
  count(az ->> 'ZoneName') < 2 as zone_count_1
from
  aws_ec2_application_load_balancer
  cross join jsonb_array_elements(availability_zones) as az
group by
  name;