# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""....."""

import math
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

from openph.model.climate import OpPhClimateCalcPeriod, OpPhClimatePeakHeatingLoad
from openph.model.enums import CardinalOrientation


@dataclass(frozen=True)
class OpPhSolarRadiationCalcPeriod:
    """Solar radiation incident on individual surfaces (window and opaque) for a single calculation period (month)."""

    # -- PHPP Model Data
    phpp: "OpPhPHPP"

    # -- Calc Periods
    period_climate: OpPhClimateCalcPeriod

    # ------------------------------------------------------------------------------------------------------------------
    # -- Window Radiation
    @cached_property
    def window_radiation_north_kwh(self) -> list[float]:
        """Solar radiation incident on each north-facing window surface for this period.

        PHPP V10 | Windows | GX23:HI174

        = FN16 + FN17*cos(P23*FR2 - FN19) - FN23*sin(2*(P23*FR2 - FN19)) + FN18*cos(2*(P23*FR2 - FN19))

        Units: kwh
        """
        return [
            (
                self.period_climate.f_NS_A0
                + self.period_climate.f_NS_A1
                * math.cos(
                    window.angle_from_horizontal * self.period_climate.RAD
                    - self.period_climate.f_alpha
                )
                - self.period_climate.f_B2
                * math.sin(
                    2
                    * (
                        window.angle_from_horizontal * self.period_climate.RAD
                        - self.period_climate.f_alpha
                    )
                )
                + self.period_climate.f_NS_A2
                * math.cos(
                    2
                    * (
                        window.angle_from_horizontal * self.period_climate.RAD
                        - self.period_climate.f_alpha
                    )
                )
            )
            for window in self.phpp.areas.windows
        ]

    @cached_property
    def window_radiation_south_kwh(self) -> list[float]:
        """Solar radiation incident on each south-facing window surface for this period.

        PHPP V10 | Windows | GF23:GQ174

        = FN16 + FN17*cos(P23*FR2 + FN19) + FN23*sin(2*(P23*FR2 + FN19)) + FN18*cos(2*(P23*FR2 + FN19))

        Units: kwh
        """
        return [
            (
                self.period_climate.f_NS_A0
                + self.period_climate.f_NS_A1
                * math.cos(
                    window.angle_from_horizontal * self.period_climate.RAD
                    + self.period_climate.f_alpha
                )
                + self.period_climate.f_B2
                * math.sin(
                    2
                    * (
                        window.angle_from_horizontal * self.period_climate.RAD
                        + self.period_climate.f_alpha
                    )
                )
                + self.period_climate.f_NS_A2
                * math.cos(
                    2
                    * (
                        window.angle_from_horizontal * self.period_climate.RAD
                        + self.period_climate.f_alpha
                    )
                )
            )
            for window in self.phpp.areas.windows
        ]

    @cached_property
    def window_radiation_west_kwh(self) -> list[float]:
        """Solar radiation incident on each west-facing window surface for this period.

        PHPP V10 | Windows | HP23:IA174

        = FN12 + FN13*cos(P23*FR2) + FN14*cos(2*P23*FR2) + FN15*sin(P23*FR2)

        Units: kwh
        """
        return [
            (
                self.period_climate.f_EW_A0
                + self.period_climate.f_EW_A1
                * math.cos(window.angle_from_horizontal * self.period_climate.RAD)
                + self.period_climate.f_EW_A2
                * math.cos(2 * window.angle_from_horizontal * self.period_climate.RAD)
                + self.period_climate.f_EW_B1
                * math.sin(window.angle_from_horizontal * self.period_climate.RAD)
            )
            for window in self.phpp.areas.windows
        ]

    @cached_property
    def window_radiation_east_kwh(self) -> list[float]:
        """Solar radiation incident on each east-facing window surface for this period.

        PHPP V10 | Windows | IH23:IS174

        = FN12 + FN13*cos(P23*FR2) + FN14*cos(2*P23*FR2) - FN15*sin(P23*FR2)

        Units: kwh
        """
        return [
            (
                self.period_climate.f_EW_A0
                + self.period_climate.f_EW_A1
                * math.cos(window.angle_from_horizontal * self.period_climate.RAD)
                + self.period_climate.f_EW_A2
                * math.cos(2 * window.angle_from_horizontal * self.period_climate.RAD)
                - self.period_climate.f_EW_B1
                * math.sin(window.angle_from_horizontal * self.period_climate.RAD)
            )
            for window in self.phpp.areas.windows
        ]

    @cached_property
    def window_total_effective_radiation_kwh(self) -> list[float]:
        """Total effective solar radiation for each individual window surface.

        PHPP V10 | Windows | IZ23:JK174

        =[0.25*(GF23+GX23+HP23+IH23) + 0.5*(GX23-GF23)*cos(O23*FR2) +
                  0.25*(GF23+GX23-HP23-IH23)*cos(2*O23*FR2) + 0.5*(IH23-HP23)*sin(O23*FR2)] * AX23
        Units: kwh
        """
        surface_radiation = []
        for inputs in zip(
            self.phpp.areas.windows,
            self.window_radiation_south_kwh,
            self.window_radiation_north_kwh,
            self.window_radiation_west_kwh,
            self.window_radiation_east_kwh,
        ):
            window, rad_south, rad_north, rad_west, rad_east = inputs
            glazing_area = window.glazing_area_m2
            orientation_angle = window.cardinal_orientation_angle
            result = (
                0.25 * (rad_south + rad_north + rad_west + rad_east)
                + 0.5
                * (rad_north - rad_south)
                * math.cos(orientation_angle * self.period_climate.RAD)
                + 0.25
                * (rad_south + rad_north - rad_west - rad_east)
                * math.cos(2 * orientation_angle * self.period_climate.RAD)
                + 0.5
                * (rad_east - rad_west)
                * math.sin(orientation_angle * self.period_climate.RAD)
            ) * glazing_area

            surface_radiation.append(result)
        return surface_radiation

    @cached_property
    def window_total_period_radiation_kwh(self) -> float:
        """Total effective radiation across all window surfaces for this calculation period.

        PHPP V10 | Windows | Calculated sum of IZ23:JK174

        Units: kwh
        """
        return sum(self.window_total_effective_radiation_kwh)

    def get_window_surface_total_radiation_for_orientation(
        self, _orientation: CardinalOrientation
    ) -> float:
        """Return the total effective window solar radiation, for the orientation specified.

        PHPP 10 | Windows | GF6:GQ10 (first part).

        Units: ?
        """

        total = sum(
            total_radiation
            for orientation, total_radiation in zip(
                self.phpp.areas.aperture_orientations,
                self.window_total_effective_radiation_kwh,
            )
            if orientation == _orientation
        )

        if total == 0:
            total = self.period_climate.get_radiation_by_orientation(_orientation)

        return total

    def get_window_surface_total_radiation_per_m2_for_orientation(
        self, _orientation: CardinalOrientation
    ) -> float:
        """Return the total effective-window-solar-radiation / total-glazing-area, for the orientation specified.

        PHPP 10 | Windows | GF6:GQ10 (second part).

        Units: ?
        """

        total_radiation = self.get_window_surface_total_radiation_for_orientation(
            _orientation
        )
        total_glazing_area = self.phpp.areas.aperture_surfaces.by_orientation(
            _orientation
        ).total_glazing_area_m2

        try:
            return total_radiation / total_glazing_area
        except ZeroDivisionError:
            return total_radiation

    # ------------------------------------------------------------------------------------------------------------------
    # -- Opaque Surface Radiation
    @cached_property
    def opaque_surface_radiation_north_kwh_m2(self) -> list[float]:
        """Solar radiation incident on each north-facing opaque surface for this period.

        PHPP V10 | Areas | DB41:DL140

        = BX17 + BX18*cos(AF41*CB2 - BX20) - BX41*sin(2*(AF41*CB2 - BX20)) + BX19*cos(2*(AF41*CB2 - BX20))

        Units: kwh/m²
        """
        surface_radiation = []
        for surface in self.phpp.areas.opaque_surfaces:
            result = (
                self.period_climate.f_NS_A0
                + self.period_climate.f_NS_A1
                * math.cos(
                    surface.angle_from_horizontal * self.period_climate.RAD
                    - self.period_climate.f_alpha
                )
                - self.period_climate.f_B2
                * math.sin(
                    2
                    * (
                        surface.angle_from_horizontal * self.period_climate.RAD
                        - self.period_climate.f_alpha
                    )
                )
                + self.period_climate.f_NS_A2
                * math.cos(
                    2
                    * (
                        surface.angle_from_horizontal * self.period_climate.RAD
                        - self.period_climate.f_alpha
                    )
                )
            )
            surface_radiation.append(result)
        return surface_radiation

    @cached_property
    def opaque_surface_radiation_east_kwh_m2(self) -> list[float]:
        """Solar radiation incident on each east-facing opaque surface for this period.

        PHPP V10 | Areas | EF41:EQ140

        = BX13 + BX14*cos(AF41*CB2) + BX15*cos(2*AF41*CB2) - BX16*sin(AF41*CB2)

        Units: kwh/m²
        """
        surface_radiation = []
        for surface in self.phpp.areas.opaque_surfaces:
            result = (
                self.period_climate.f_EW_A0
                + self.period_climate.f_EW_A1
                * math.cos(surface.angle_from_horizontal * self.period_climate.RAD)
                + self.period_climate.f_EW_A2
                * math.cos(2 * surface.angle_from_horizontal * self.period_climate.RAD)
                - self.period_climate.f_EW_B1
                * math.sin(surface.angle_from_horizontal * self.period_climate.RAD)
            )
            surface_radiation.append(result)
        return surface_radiation

    @cached_property
    def opaque_surface_radiation_south_kwh_m2(self) -> list[float]:
        """A list of solar radiation incident on each south-facing opaque surface for this period.

        PHPP V10 | Areas | CM41:CX140

        = BX17 + BX18*cos(AF41*CB2 + BX20) + BX41*sin(2*(AF41*CB2 + BX20)) + BX19*cos(2*(AF41*CB2 + BX20))

        Units: kwh/m²
        """
        surface_radiation = []
        for surface in self.phpp.areas.opaque_surfaces:
            result = (
                self.period_climate.f_NS_A0
                + self.period_climate.f_NS_A1
                * math.cos(
                    surface.angle_from_horizontal * self.period_climate.RAD
                    + self.period_climate.f_alpha
                )
                + self.period_climate.f_B2
                * math.sin(
                    2
                    * (
                        surface.angle_from_horizontal * self.period_climate.RAD
                        + self.period_climate.f_alpha
                    )
                )
                + self.period_climate.f_NS_A2
                * math.cos(
                    2
                    * (
                        surface.angle_from_horizontal * self.period_climate.RAD
                        + self.period_climate.f_alpha
                    )
                )
            )
            surface_radiation.append(result)
        return surface_radiation

    @cached_property
    def opaque_surface_radiation_west_kwh_m2(self) -> list[float]:
        """Solar radiation incident on each west-facing opaque surface for this period.

        PHPP V10 | Areas | DQ41:EB140

        = BX13 + BX14*cos(AF41*CB2) + BX15*cos(2*AF41*CB2) + BX16*sin(AF41*CB2)

        Units: kwh/m²
        """
        surface_radiation = []
        for surface in self.phpp.areas.opaque_surfaces:
            result = (
                self.period_climate.f_EW_A0
                + self.period_climate.f_EW_A1
                * math.cos(surface.angle_from_horizontal * self.period_climate.RAD)
                + self.period_climate.f_EW_A2
                * math.cos(2 * surface.angle_from_horizontal * self.period_climate.RAD)
                + self.period_climate.f_EW_B1
                * math.sin(surface.angle_from_horizontal * self.period_climate.RAD)
            )

            surface_radiation.append(result)
        return surface_radiation

    @cached_property
    def opaque_surface_total_effective_radiation(self) -> list[float]:
        """Total effective solar radiation for each individual opaque surface.

        PHPP V10 | Areas | EU41:FF140

        = [0.25*(CM41+DB41+DQ41+EF41) + 0.5*(DB41-CM41)*cos(AE41*CB2)
        + 0.25*(CM41+DB41-DQ41-EF41)*cos(2*AE41*CB2)
        + 0.5*(EF41-DQ41)*sin(AE41*CB2)] * BP41

        Units: kwh
        """
        surface_radiation = []
        for inputs in zip(
            self.phpp.areas.opaque_surfaces,
            self.opaque_surface_radiation_south_kwh_m2,
            self.opaque_surface_radiation_north_kwh_m2,
            self.opaque_surface_radiation_west_kwh_m2,
            self.opaque_surface_radiation_east_kwh_m2,
        ):
            surface, rad_south, rad_north, rad_west, rad_east = inputs
            eff_heat_gain_area = surface.heat_gain.summer.eff_heat_gain_area_m2
            orientation_angle = surface.cardinal_orientation_angle
            result = (
                0.25 * (rad_south + rad_north + rad_west + rad_east)
                + 0.5
                * (rad_north - rad_south)
                * math.cos(orientation_angle * self.period_climate.RAD)
                + 0.25
                * (rad_south + rad_north - rad_west - rad_east)
                * math.cos(2 * orientation_angle * self.period_climate.RAD)
                + 0.5
                * (rad_east - rad_west)
                * math.sin(orientation_angle * self.period_climate.RAD)
            ) * eff_heat_gain_area
            surface_radiation.append(result)
        return surface_radiation

    @cached_property
    def opaque_surface_solar_heat_gain_kwh(self) -> float:
        """Total effective radiation across all opaque surfaces for this calculation period.

        PHPP V10 | Areas | CP5:DA5

        Units: kwh
        """
        return sum(self.opaque_surface_total_effective_radiation)

    @cached_property
    def thermal_bridge_solar_heat_gain_kwh(self) -> float:
        """Solar heat gain through thermal bridges during this calculation period.

        PHPP V10 | Areas | CP6:DA6 (Thermal Bridge Solar Gain)

        Units: kwh
        """
        # TODO: Calculate Thermal Bridge Solar Gain
        return 0.0

    @cached_property
    def window_frame_solar_heat_gain_kwh(self) -> float:
        """Solar heat gain through window frames and mullions during this period with summer temporary shading.

        PHPP V10 | Areas | CP8:DA8 (Window Frame Solar Gain)

        Units: kwh
        """
        return sum(
            rad
            * surface.heat_gain.summer.eff_heat_gain_area_m2
            * surface.heat_gain.summer.shading_factor
            for rad, surface in zip(
                self.window_total_effective_radiation_kwh, self.phpp.areas.windows
            )
        )

    @cached_property
    def all_opaque_elements_solar_heat_gain_kwh(self) -> float:
        """Return the total Opaque-Element (Surface, TB, Window-Frame) Solar Heat Gain.

        PHPP V10 | Areas | CP10:DC10

        Units: kwh
        """
        return (
            self.opaque_surface_solar_heat_gain_kwh
            + self.thermal_bridge_solar_heat_gain_kwh
            + self.window_frame_solar_heat_gain_kwh
        )


@dataclass
class OpPhSolarRadiationCalcPeriods:
    phpp: "OpPhPHPP"
    _periods: list[OpPhSolarRadiationCalcPeriod] = field(default_factory=list)

    @classmethod
    def from_periods(
        cls,
        phpp: "OpPhPHPP",
        _periods: list[OpPhClimateCalcPeriod | OpPhClimatePeakHeatingLoad],
    ):
        obj = cls(phpp)
        for period_climate in _periods:
            obj._periods.append(OpPhSolarRadiationCalcPeriod(phpp, period_climate))
        return obj

    @cached_property
    def periods(self) -> list[OpPhSolarRadiationCalcPeriod]:
        return self._periods

    @cached_property
    def number_of_periods(self) -> int:
        return len(self.periods)

    # ------------------------------------------------------------------------------------------------------------------
    # -- Window Solar Heat Gain

    def get_window_surface_period_total_radiation_for_orientation(
        self, _orientation: CardinalOrientation
    ) -> list[float]:
        """Total effective window radiation for each period by specified orientation.

        PHPP V10 | Windows | GF6:GQ10 (Orientation-Specific Window Radiation)

        Data structure format:
        [
            period_1_orientation_total,
            period_2_orientation_total,
            ...
        ]

        Units: ?
        """
        return [
            p.get_window_surface_total_radiation_for_orientation(_orientation)
            for p in self.periods
        ]

    def get_window_surface_period_total_radiation_per_m2_for_orientation(
        self, _orientation: CardinalOrientation
    ) -> list[float]:
        """Total effective window radiation per unit glazing area by orientation.

        PHPP V10 | Windows | GF6:GQ10 (Window Radiation Intensity by Orientation)

        Data structure format:
        [
            period_1_radiation_per_m2,
            period_2_radiation_per_m2,
            ...
        ]

        Units: ?
        """
        return [
            p.get_window_surface_total_radiation_per_m2_for_orientation(_orientation)
            for p in self.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Opaque Element Solar Heat Gain

    @cached_property
    def opaque_surface_solar_heat_gain_kwh(self) -> float:
        """Return the total Opaque-Element (Surface, TB, Window-Frame) Solar Heat Gain.

        PHPP V10 | Areas | CP5:DC5

        Units: kwh
        """
        return sum(p.opaque_surface_solar_heat_gain_kwh for p in self.periods)

    @cached_property
    def thermal_bridge_solar_heat_gain_kwh(self) -> float:
        """Return the total Opaque-Element (Surface, TB, Window-Frame) Solar Heat Gain.

        PHPP V10 | Areas | CP6:DC6

        Units: kwh
        """
        return sum(p.thermal_bridge_solar_heat_gain_kwh for p in self.periods)

    @cached_property
    def window_frame_solar_heat_gain_kwh(self) -> float:
        """Return the total Opaque-Element (Surface, TB, Window-Frame) Solar Heat Gain.

        PHPP V10 | Areas | CP8:DC8

        Units: kwh
        """
        return sum(p.window_frame_solar_heat_gain_kwh for p in self.periods)

    @cached_property
    def all_opaque_elements_solar_heat_gain_kwh(self) -> float:
        """Return the total Opaque-Element (Surface, TB, Window-Frame) Solar Heat Gain.

        PHPP V10 | Areas | CP10:DC10

        Units: kwh
        """
        return sum(p.all_opaque_elements_solar_heat_gain_kwh for p in self.periods)
