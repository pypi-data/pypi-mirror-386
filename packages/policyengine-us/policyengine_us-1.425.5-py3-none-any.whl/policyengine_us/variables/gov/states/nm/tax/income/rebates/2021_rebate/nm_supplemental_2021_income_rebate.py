from policyengine_us.model_api import *


class nm_supplemental_2021_income_rebate(Variable):
    value_type = float
    entity = TaxUnit
    label = "New Mexico supplemental 2021 income tax rebate"
    definition_period = YEAR
    reference = "https://nmonesource.com/nmos/nmsa/en/item/4340/index.do#!fragment/zoupio-_Toc140503706/BQCwhgziBcwMYgK4DsDWszIQewE4BUBTADwBdoAvbRABwEtsBaAfX2zgEYAWABgFYeAZgDsPAGwBKADTJspQhACKiQrgCe0AOSapEQmFwJlqjdt37DIAMp5SAIQ0AlAKIAZZwDUAggDkAws5SpGAARtCk7BISQA"
    defined_for = StateCode.NM

    def formula(tax_unit, period, parameters):
        dependent_elsewhere = tax_unit("head_is_dependent_elsewhere", period)
        p = parameters(period).gov.states.nm.tax.income.rebates["2021_income"]
        filing_status = tax_unit("filing_status", period)
        return ~dependent_elsewhere * p.supplemental.amount[filing_status]
