# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Calculation class and with methods for: PHPP | Heating."""

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

    from openph_demand.solvers import OpPhEnergyDemandSolver

from openph.model.climate import OpPhClimateCalcPeriod
from openph.model.enums import CardinalOrientation
from openph_solar.calc_periods import OpPhSolarRadiationCalcPeriod

from openph_demand.get_solvers import (
    get_openph_energy_demand_solver,
    get_openph_ground_solver,
)
from openph_demand.ground.results_period import OpPhGroundResultPeriod


@dataclass(frozen=True)
class OpPhHeatingDemandCalcPeriod:
    """A single calculation-period (month) of the PHPP Heating worksheet."""

    # -- PHPP Model Data
    phpp: "OpPhPHPP"

    # -- Calc Periods
    period_climate: OpPhClimateCalcPeriod
    period_ground: OpPhGroundResultPeriod
    period_solar_radiation: OpPhSolarRadiationCalcPeriod

    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heating Degree Hours
    @property
    def kilodegree_hours_air(self):
        """
        PHPP V10 | Cooling | T97:AE97

        Formula: =IF(Moni!AJ9,T$96*($R98-T69)/1000,T$96*(Moni!$AK118-T69)/1000)

        Units: kKh (kilodegree-hours)
        """
        return self.period_climate.heating.kilo_degree_hours_ambient_air

    @property
    def kilodegree_hours_sky(self):
        """
        PHPP V10 | Cooling | T98:AE98

        Formula: =IF(Moni!AJ9,T$96*($R98-T75)/1000,T$96*(Moni!$AK118-T75)/1000)

        Units: kKh (kilodegree-hours)
        """
        return self.period_climate.heating.kilo_degree_hours_sky

    @property
    def kilodegree_hours_ground(self) -> float:
        """
        PHPP V10 | Heating | T99:AE99

        Formula: =IF($R$102>0, T102/$R$102, 0)

        Units: kKh (kilodegree-hours)
        """
        try:
            return (
                self.transmission_heat_loss_to_ground
                / self.phpp.areas.envelop_conductance_to_ground_W_K
            )
        except ZeroDivisionError:
            return 0.0

    @property
    def kilodegree_hours_EWU(self) -> float:
        """
        PHPP V10 | Heating | T100:AE100

        =IF(Moni!AJ9,T$96*($R98-Ground!$P$11)/1000,T$96*(Moni!$AK118-Ground!$P$11)/1000)

        Units: kKh (kilodegree-hours)
        """
        ground_solver = get_openph_ground_solver(self.phpp)
        return (
            self.period_climate.period_length_hours
            * (
                self.phpp.set_points.min_interior_temp_c
                - ground_solver.average_ground_surface_temp_C
            )
            / 1000
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Losses  --------------------------------------------------------------------------------------------------
    @property
    def transmission_heat_loss_to_ambient(self) -> float:
        """
        PHPP V10 | Heating | T101:AE101

        =$R101*T97

        Units: kwh (kilowatt-hours per period)
        """

        return (
            self.energy_demand.heating_demand.conductance_factor_to_outdoor_air
            * self.kilodegree_hours_air
        )

    @property
    def transmission_heat_loss_to_ground(self) -> float:
        """
        PHPP V10 | Heating | T102:AE102

        Ground!E112*T96/1000

        Units: kwh (kilowatt-hours per period)
        """
        return (
            self.period_ground.total_heat_flow_to_ground_w
            * self.period_climate.period_length_hours
            / 1000
        )

    @property
    def convective_heat_loss_to_EWU(self) -> float:
        """
        PHPP V10 | Heating | T103:AE103

        =$R103*T100

        Units: kwh (kilowatt-hours per period)
        """

        return (
            self.energy_demand.heating_demand.conductance_factor_to_EWU
            * self.kilodegree_hours_EWU
        )

    @property
    def convective_heat_loss_to_ambient(self) -> float:
        """
        PHPP V10 | Heating | T104:AE104

        =$R104*T97

        Units: kwh
        """

        return (
            self.energy_demand.heating_demand.convection_factor_W_K
            * self.kilodegree_hours_air
        )

    @property
    def radiative_heat_loss_to_sky(self) -> float:
        """
        PHPP V10 | Heating | T105:AE105

        =$R105*T98

        Units: kwh
        """

        return (
            self.energy_demand.heating_demand.radiation_factor_W_K
            * self.kilodegree_hours_sky
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Gains  ---------------------------------------------------------------------------------------------------
    @property
    def north_window_solar_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T106:AE106

        =$R106*T91

        Units: kwh
        """

        return (
            self.phpp.areas.windows.north.winter_eff_solar_gain_area_m2
            * self.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                CardinalOrientation.NORTH
            )
        )

    @property
    def east_window_solar_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T107:AE107

        =$R107*T92

        Units: kwh
        """

        return (
            self.phpp.areas.windows.east.winter_eff_solar_gain_area_m2
            * self.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                CardinalOrientation.EAST
            )
        )

    @property
    def south_window_solar_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T108:AE108

        =$R108*T93

        Units: kwh
        """

        return (
            self.phpp.areas.windows.south.winter_eff_solar_gain_area_m2
            * self.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                CardinalOrientation.SOUTH
            )
        )

    @property
    def west_window_solar_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T109:AE109

        =$R109*T94

        Units: kwh
        """

        return (
            self.phpp.areas.windows.west.winter_eff_solar_gain_area_m2
            * self.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                CardinalOrientation.WEST
            )
        )

    @property
    def horizontal_window_solar_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T110:AE110

        =$R110*T95

        Units: kwh
        """

        return (
            self.phpp.areas.windows.horizontal.winter_eff_solar_gain_area_m2
            * self.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                CardinalOrientation.HORIZONTAL
            )
        )

    @property
    def total_window_frame_solar_gain(self) -> float:
        """Solar heat gain through window frames and mullions during this period without summer temporary shading.

        PHPP V10 | Areas | CP7:DA7 (Window Frame Solar Gain)

        Formula: SUMPRODUCT(total_radiation, solar_aperture, shading_factor)
        For each surface: total_radiation * effective_heat_gain_area * shading_factor

        Calculates solar heat absorption by window frame elements including:
        - Frame materials with higher absorptance than glazing
        - Mullions and structural glazing elements
        - Integration with shading systems and solar exposure

        The calculation multiplies surface radiation by effective heat gain areas
        and applicable shading factors to determine total frame contribution.

        Units: kwh
        """
        return sum(
            rad
            * surface.heat_gain.winter.eff_heat_gain_area_m2
            * surface.heat_gain.winter.shading_factor
            for rad, surface in zip(
                self.period_solar_radiation.window_total_effective_radiation_kwh,
                self.phpp.areas.windows,
            )
        )

    @property
    def opaque_surface_solar_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T111:AE111

        =Areas!CP9

        Units: kwh
        """
        return (
            self.period_solar_radiation.opaque_surface_solar_heat_gain_kwh
            + self.period_solar_radiation.thermal_bridge_solar_heat_gain_kwh
            + self.total_window_frame_solar_gain
        )

    @property
    def internal_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T112:AE112

        =IF(Moni!AJ9,$R112*T96/1000,Moni!AK142*Heating!AD9*T96/1000)

        Units: kwh
        """

        return (
            self.energy_demand.heating_demand.internal_heat_gain_rate_W
            * self.period_climate.period_length_hours
        ) / 1000

    # ------------------------------------------------------------------------------------------------------------------
    # -- Energy Balance  -----------------------------------------------------------------------------------------------
    @property
    def total_heat_loss(self) -> float:
        """
        PHPP V10 | Heating | T113:AE113

        =T101+T102+T103+T104+T105

        Units: kwh
        """
        return (
            self.transmission_heat_loss_to_ambient
            + self.transmission_heat_loss_to_ground
            + self.convective_heat_loss_to_EWU
            + self.convective_heat_loss_to_ambient
            + self.radiative_heat_loss_to_sky
        )

    @property
    def total_heat_gain(self) -> float:
        """
        PHPP V10 | Heating | T114:AE114

        =SUM(T106:T112)

        Units: kwh
        """
        return (
            self.north_window_solar_heat_gain
            + self.east_window_solar_heat_gain
            + self.south_window_solar_heat_gain
            + self.west_window_solar_heat_gain
            + self.horizontal_window_solar_heat_gain
            + self.opaque_surface_solar_heat_gain
            + self.internal_heat_gain
        )

    @property
    def gain_to_loss_ratio(self) -> float:
        """
        PHPP V10 | Heating | T115:AE115

        =IF(OR(T113=0,ABS(T113)< 0.001*ABS(T114)),0,T114/T113)

        Units: %
        """
        if self.total_heat_loss < 0.001:
            return 0.0

        try:
            return self.total_heat_gain / self.total_heat_loss
        except ZeroDivisionError:
            return 0.0

    @property
    def utilization_factor(self) -> float:
        """
        PHPP V10 | Heating | T116:AE116

        =IF(T115>0,IF(T115=1,$R$118/($R$118+1),(1-T115^$R$118)/(1-T115^($R$118+1))),1)

        Units: %
        """
        if self.gain_to_loss_ratio > 0:
            if self.gain_to_loss_ratio == 1:
                return self.energy_demand.heating_demand.a_monthly_procedure / (
                    self.energy_demand.heating_demand.a_monthly_procedure + 1
                )
            else:
                return (
                    1
                    - self.gain_to_loss_ratio
                    ** self.energy_demand.heating_demand.a_monthly_procedure
                ) / (
                    1
                    - self.gain_to_loss_ratio
                    ** (self.energy_demand.heating_demand.a_monthly_procedure + 1)
                )
        else:
            return 1.0

    @property
    def heating_demand(self) -> float:
        """
        PHPP V10 | Heating | T117:AE117

        =MAX(0,T113-T116*T114)

        Units: kwh
        """

        heating_demand = (
            self.total_heat_loss - self.utilization_factor * self.total_heat_gain
        )
        # Heating demand cannot be negative
        return max(0.0, heating_demand)

    @property
    def in_heating_period(self) -> bool:
        """
        PHPP V10 | Heating | T118:AE118

        =T117>$AF$117*0.001

        Units: kwh
        """
        # THRESHOLD = 0.001  # 1 Wh threshold to avoid floating point issues

        return (
            self.heating_demand
            > self.energy_demand.heating_demand.total_yearly_heating_demand * 0.001
        )
