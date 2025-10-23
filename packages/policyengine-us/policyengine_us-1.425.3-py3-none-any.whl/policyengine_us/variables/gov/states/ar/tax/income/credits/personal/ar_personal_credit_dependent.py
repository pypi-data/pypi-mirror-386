from policyengine_us.model_api import *


class ar_personal_credit_dependent(Variable):
    value_type = float
    entity = Person
    label = "Arkansas personal tax credit dependent amount"
    unit = USD
    definition_period = YEAR
    reference = (
        "https://www.dfa.arkansas.gov/images/uploads/incomeTaxOffice/2021_AR1000F_FullYearResidentIndividualIncomeTaxReturn.pdf"
        "https://www.dfa.arkansas.gov/images/uploads/incomeTaxOffice/2022_AR1000F_FullYearResidentIndividualIncomeTaxReturn.pdf#page=1"
        "https://www.dfa.arkansas.gov/images/uploads/incomeTaxOffice/2022_AR1000F_and_AR1000NR_Instructions.pdf#page=12"
    )
    defined_for = StateCode.AR

    def formula(person, period, parameters):
        dependent = person("is_tax_unit_dependent", period)
        p = parameters(period).gov.states.ar.tax.income.credits.personal.amount
        return dependent * p.base
