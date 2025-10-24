# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""....."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP


from openph_solar.calc_periods import OpPhSolarRadiationCalcPeriods


@dataclass
class OpPhSolarRadiationSolver:
    """The PHPP Window worksheet data with a collection of OpPhWindowCalcPeriod (months)."""

    phpp: "OpPhPHPP"
    annual_demand: OpPhSolarRadiationCalcPeriods = field(init=False)
    peak_heating_load_1: OpPhSolarRadiationCalcPeriods = field(init=False)
    peak_heating_load_2: OpPhSolarRadiationCalcPeriods = field(init=False)
    peak_cooling_load_1: OpPhSolarRadiationCalcPeriods = field(init=False)
    peak_cooling_load_2: OpPhSolarRadiationCalcPeriods = field(init=False)

    def __post_init__(self):
        self.annual_demand = OpPhSolarRadiationCalcPeriods.from_periods(
            self.phpp, self.phpp.climate.periods
        )
        self.peak_heating_load_1 = OpPhSolarRadiationCalcPeriods.from_periods(
            self.phpp, [self.phpp.climate.peak_heating_1]
        )
        self.peak_heating_load_2 = OpPhSolarRadiationCalcPeriods.from_periods(
            self.phpp, [self.phpp.climate.peak_heating_2]
        )
        self.peak_cooling_load_1 = OpPhSolarRadiationCalcPeriods.from_periods(
            self.phpp, [self.phpp.climate.peak_cooling_1]
        )
        self.peak_cooling_load_2 = OpPhSolarRadiationCalcPeriods.from_periods(
            self.phpp, [self.phpp.climate.peak_cooling_2]
        )
