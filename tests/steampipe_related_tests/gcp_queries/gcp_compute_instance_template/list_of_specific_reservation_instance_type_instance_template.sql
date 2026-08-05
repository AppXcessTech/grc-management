select
  name,
  id,
  instance_reservation_affinity ->> 'consumeReservationType' as consume_reservation_type
from
  gcp_compute_instance_template
where
  instance_reservation_affinity ->> 'consumeReservationType' = 'SPECIFIC_RESERVATION';