from policyengine_us.model_api import *


class investment_interest_expense(Variable):
    value_type = float
    entity = Person
    label = "Investment interest expense"
    unit = USD
    definition_period = YEAR
