select
  name,
  identity -> 'type' as identity_type,
  jsonb_pretty(identity -> 'userAssignedIdentities') as identity_user_assignedidentities
from
  azure_compute_virtual_machine
where
    exists (
      select
      from
        unnest(regexp_split_to_array(identity ->> 'type', ',')) elem
      where
        trim(elem) = 'UserAssigned'
  );