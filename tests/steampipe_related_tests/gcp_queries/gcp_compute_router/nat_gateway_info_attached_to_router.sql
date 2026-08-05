select
  name,
  nat ->> 'name' as nat_name,
  nat ->> 'enableEndpointIndependentMapping' as enable_endpoint_independent_mapping,
  nat ->> 'natIpAllocateOption' as nat_ip_allocate_option,
  nat ->> 'sourceSubnetworkIpRangesToNat' as source_subnetwork_ip_ranges_to_nat
from
  gcp_compute_router,
  jsonb_array_elements(nats) as nat;