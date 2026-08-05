select
  id,
  name,
  identity -> 'type' as identity_type
from
  azure_synapse_workspace
where
    exists (
      select
      from
        unnest(regexp_split_to_array(identity ->> 'type', ',')) elem
      where
        trim(elem) = 'UserAssigned'
  );