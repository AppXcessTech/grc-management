select
  name_with_owner,
  custom_properties
from
  github_my_repository
where
  custom_properties is not null;