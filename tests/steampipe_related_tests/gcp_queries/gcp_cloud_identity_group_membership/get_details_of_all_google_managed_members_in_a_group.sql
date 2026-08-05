select
  name,
  group_name,
  create_time,
  preferred_member_key ->> 'id' as member_id
from
  gcp_cloud_identity_group_membership
where
  group_name = '123j0zll4288gmz'
  and preferred_member_key ->> 'namespace' is null;