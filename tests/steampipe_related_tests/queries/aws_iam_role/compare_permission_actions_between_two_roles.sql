with roles as (
  select
    name,
    attached_policy_arns
  from
    aws_iam_role
  where
    name in ('AWSServiceRoleForSSO', 'AWSServiceRoleForRDS')
),
policies as (
  select
    name,
    arn,
    policy_std
  from
    aws_iam_policy
),
role1_permissions as (
  select
    r.name,
    a.action,
    a.access_level,
    a.description
  from
    roles as r,
    jsonb_array_elements_text(r.attached_policy_arns) as pol_arn,
    policies as p,
    jsonb_array_elements(p.policy_std -> 'Statement') as stmt,
    jsonb_array_elements_text(stmt -> 'Action') as action_glob,
    glob (action_glob) as action_regex
    join aws_iam_action a on a.action like action_regex
  where
    pol_arn = p.arn
    and stmt ->> 'Effect' = 'Allow'
    and r.name = 'AWSServiceRoleForSSO'
),
role2_permissions as (
  select
    r.name,
    a.action,
    a.access_level,
    a.description
  from
    roles as r,
    jsonb_array_elements_text(r.attached_policy_arns) as pol_arn,
    policies as p,
    jsonb_array_elements(p.policy_std -> 'Statement') as stmt,
    jsonb_array_elements_text(stmt -> 'Action') as action_glob,
    glob (action_glob) as action_regex
    join aws_iam_action a on a.action like action_regex
  where
    pol_arn = p.arn
    and stmt ->> 'Effect' = 'Allow'
    and r.name = 'AWSServiceRoleForRDS'
)
select
  *
from
  role2_permissions
where
  action not in ( select action from role1_permissions)
order by
  action;