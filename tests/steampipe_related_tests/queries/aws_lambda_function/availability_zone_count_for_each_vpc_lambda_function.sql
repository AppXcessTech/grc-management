select
  fn.name,
  fn.region,
  count (availability_zone) as zone_count
from
  aws_lambda_function as fn
  cross join jsonb_array_elements_text(vpc_subnet_ids) as vpc_subnet
  join aws_vpc_subnet as sub on sub.subnet_id = vpc_subnet
group by
  fn.name,
  fn.region
order by
  zone_count;