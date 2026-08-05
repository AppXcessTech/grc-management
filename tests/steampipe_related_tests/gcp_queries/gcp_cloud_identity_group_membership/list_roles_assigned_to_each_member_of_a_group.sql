select
  name,
  group_name,
  create_time,
  type,
  preferred_member_key ->> 'id' as member_id,
  role ->> 'name' as role_name,
  role -> 'expiryDetail' ->> 'expireTime' as role_expiry_time
from
  gcp_cloud_identity_group_membership,
  jsonb_array_elements(roles) as role
where
  group_name = '123j0zll4288gmz';