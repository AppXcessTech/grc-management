select
  name as workspace,
  slug,
  uuid,
  is_private
from
  bitbucket_workspace
where
  slug = 'np1981';