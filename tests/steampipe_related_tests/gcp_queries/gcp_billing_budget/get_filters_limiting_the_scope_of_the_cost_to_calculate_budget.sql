select
  name,
  display_name,
  string_agg(p, ', ') as applies_to_projects,
  specified_amount ->> 'units' as units,
  specified_amount ->> 'currencyCode' as currency_code,
  budget_filter ->> 'calendarPeriod' as budget_calendar_period,
  budget_filter ->> 'creditTypesTreatment' as budget_credit_types_treatment
from
  gcp_billing_budget,
  jsonb_array_elements_text(budget_filter -> 'projects') as p
group by
  name,
  display_name,
  budget_filter,
  specified_amount;