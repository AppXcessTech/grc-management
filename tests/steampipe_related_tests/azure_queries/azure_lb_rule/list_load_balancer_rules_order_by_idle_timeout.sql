select
  id,
  name,
  type,
  idle_timeout_in_minutes
from
  azure_lb_rule
order by 
  idle_timeout_in_minutes;