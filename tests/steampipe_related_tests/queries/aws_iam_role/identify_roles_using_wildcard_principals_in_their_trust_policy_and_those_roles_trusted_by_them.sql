select
  maintenance.name,
  admin.name,
  jsonb_pretty(maintenance_stmt),
  jsonb_pretty(admin_stmt)
from
  -- use the account to get the organization_id
  aws_account as a,
  -- check any role as the "maintenance-role"
  aws_iam_role as maintenance,
  -- Combine via join with any role as the "admin-role"
  aws_iam_role as admin,
  jsonb_array_elements(maintenance.assume_role_policy_std -> 'Statement') as maintenance_stmt,
  jsonb_array_elements(admin.assume_role_policy_std -> 'Statement') as admin_stmt
where
  -- maintenance role can be assumed by any AWS principal
  maintenance_stmt -> 'Principal' -> 'AWS' ? '*'
  -- maintenance role principal must be in same account
  and maintenance_stmt -> 'Condition' -> 'StringEquals' -> 'aws:principalorgid' ? a.organization_id
  -- admin role specifically allow maintenance role
  and admin_stmt -> 'Principal' -> 'AWS' ? maintenance.arn;