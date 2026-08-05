select
  name,
  policy_detail ->> 'PolicyName' as policy_name,
  policy_detail ->> 'PolicyTypeName' as policy_type_name,
  policy_detail -> 'PolicyAttributeDescriptions' as policy_attributes
from
  aws_ec2_classic_load_balancer
  cross join jsonb_array_elements(policy_descriptions) as policy_detail
where
  policy_descriptions is not null;