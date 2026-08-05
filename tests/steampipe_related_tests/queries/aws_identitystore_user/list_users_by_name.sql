select
  id,
  name
from
  aws_identitystore_user
where identity_store_id = 'd-1234567890' and name = 'test';