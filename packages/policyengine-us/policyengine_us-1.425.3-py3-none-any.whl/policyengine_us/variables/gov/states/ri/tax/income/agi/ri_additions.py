from policyengine_us.model_api import *


class ri_additions(Variable):
    value_type = float
    entity = TaxUnit
    label = "Rhode Island AGI Additions"
    unit = USD
    definition_period = YEAR
    reference = "https://tax.ri.gov/sites/g/files/xkgbur541/files/2022-12/2022%201041%20Schedule%20M_w.pdf#page=2"
    defined_for = StateCode.RI
    adds = "gov.states.ri.tax.income.agi.additions.additions"
