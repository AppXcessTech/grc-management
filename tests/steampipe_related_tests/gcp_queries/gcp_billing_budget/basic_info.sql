select
  name,
  billing_account
  display_name,
  specified_amount ->> 'units' as units,
  specified_amount ->> 'currencyCode' as currency_code,
  project,
  location
from
  gcp_billing_budget;