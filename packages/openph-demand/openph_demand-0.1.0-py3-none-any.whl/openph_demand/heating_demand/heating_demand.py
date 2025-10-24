# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Calculation class and with methods for: PHPP | Heating."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

from openph.model import enums
from openph_solar.get_solvers import get_openph_solar_solver
from openph_solar.solvers import OpPhSolarRadiationSolver

from openph_demand.get_solvers import get_openph_ground_solver
from openph_demand.heating_demand.calc_periods import OpPhHeatingDemandCalcPeriod


@dataclass
class OpPhHeatingDemand:
    phpp: "OpPhPHPP"
    _periods: list[OpPhHeatingDemandCalcPeriod] = field(default_factory=list)
    solar_radiation: OpPhSolarRadiationSolver = field(init=False)

    def __post_init__(self) -> None:
        """Setup all of the calculation-periods for the cooling demand."""
        ground_solver = get_openph_ground_solver(self.phpp)
        self.solar_radiation = get_openph_solar_solver(self.phpp)
        for climate_period, ground_period, solar_radiation_period in zip(
            self.phpp.climate.periods,
            ground_solver.periods,
            self.solar_radiation.annual_demand.periods,
        ):
            self._periods.append(
                OpPhHeatingDemandCalcPeriod(
                    self.phpp,
                    climate_period,
                    ground_period,
                    solar_radiation_period,
                )
            )

    @property
    def periods(self) -> list[OpPhHeatingDemandCalcPeriod]:
        return self._periods

    @property
    def period_hours(self) -> list[int]:
        """Monthly hours for each calculation period in the heating-demand calculation.

        PHPP V10 | Heating | T88:AE88 (Stunden/Monat - Hours per Month)

        Returns a list of the total number of hours in each calculation period,
        typically representing calendar months. These values are used as time
        multipliers in monthly cooling calculations including:
        - Internal heat gain integrations over time
        - Heat loss and gain accumulations
        - Thermal mass and time constant calculations

        Example: [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
        (hours for Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)

        Units: hours per month
        """
        return [p.period_climate.period_length_hours for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heating Degree Hours  -----------------------------------------------------------------------------------------
    @property
    def kilodegree_hours_air(self) -> list[float]:
        """Temperature-time product for ground thermal coupling calculations.

        PHPP V10 | Cooling | T97:AE97

        Formula: =IF(Moni!AJ9,T$96*($R98-T69)/1000,T$96*(Moni!$AK118-T69)/1000)

        Units: kKh (kilodegree-hours)
        """
        return [p.kilodegree_hours_air for p in self.periods]

    @property
    def kilodegree_hours_sky(self) -> list[float]:
        """Temperature-time product for ground thermal coupling calculations.

        PHPP V10 | Cooling | T98:AE98

        Formula: =IF(Moni!AJ9,T$96*($R98-T75)/1000,T$96*(Moni!$AK118-T75)/1000)

        Units: kKh (kilodegree-hours)
        """
        return [p.kilodegree_hours_sky for p in self.periods]

    @property
    def kilodegree_hours_ground(self) -> list[float]:
        """Temperature-time product for ground thermal coupling calculations.

        PHPP V10 | Heating | T99:AE99

        Formula: =IF($R$102>0, T102/$R$102, 0)

        Units: kKh (kilodegree-hours)
        """
        return [p.kilodegree_hours_ground for p in self.periods]

    @property
    def kilodegree_hours_EWU(self) -> list[float]:
        """
        PHPP V10 | Heating | T100:AE100

        =IF(Moni!AJ9,T$96*($R98-Ground!$P$11)/1000,T$96*(Moni!$AK118-Ground!$P$11)/1000)

        Units: kKh (kilodegree-hours)
        """
        return [p.kilodegree_hours_EWU for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat-Loss Factors  --------------------------------------------------------------------------------------------
    @property
    def ground_conductivity_for_time_constant(self) -> float:
        """
        PHPP V10 | Heating R100

        =IF(ISNUMBER(Ground!H119),Ground!H119,IF(ISNUMBER(Ground!H218),Ground!H218,R102))

        Units: W/K
        """
        # TODO: Implement this once we have User-defined Foundations
        if False:
            pass
            # return GroundH119
        else:
            if False:
                pass
                # return GroundH218
            else:
                return 40.5
                return self.conductance_factor_to_ground

    @property
    def conductance_factor_to_outdoor_air(self) -> float:
        """
        PHPP V10 | Heating | R101

        Formula: =SUMPRODUCT($G$14:$G$25,$I$14:$I$25,$K$14:$K$25)+O31*K40*(G35*(1-K35)+M35)-R102-R103

        Units: W/K (watts per kelvin)
        """
        return (
            self.phpp.areas.envelop_conductance_to_ambient_air_W_K  # note: Already excludes to-soil heat-loss (R102)
            + self.phpp.rooms.total_ventilated_volume_m3
            * self.phpp.constants.c_air
            * (
                self.phpp.hvac.ventilation_system.winter.vent_system_ach
                * (1 - self.phpp.hvac.ventilation_system.effective_heat_recovery)
                + self.phpp.infiltration.n_v_res
            )
            - self.conductance_factor_to_EWU
        )

    @property
    def conductance_factor_to_ground(self) -> float:
        """
        PHPP V10 | Heating | R102

        Formula: =SUMPRODUCT($G$14:$G$25,$I$14:$I$25,
        IF($F$14:$F$25="B",1,0))+SUMPRODUCT($G$14:$G$25,$I$14:$I$25,IF($F$14:$F$25="P",1,0))

        Units: W/K (watts per kelvin)
        """
        return self.phpp.areas.envelop_conductance_to_ground_W_K

    @property
    def conductance_factor_to_EWU(self) -> float:
        """
        PHPP V10 | Heating | R103

        Formula: =O31 * K40 * I35 * G35 * (1 - K35)

        Units: W/K (watts per kelvin)
        """
        return (
            self.phpp.rooms.total_ventilated_volume_m3
            * self.phpp.constants.c_air
            * self.phpp.hvac.ventilation_system.effective_subsoil_heat_recovery
            * self.phpp.hvac.ventilation_system.winter.vent_system_ach
            * (1 - self.phpp.hvac.ventilation_system.effective_heat_recovery)
        )

    @property
    def convection_factor_W_K(self) -> float:
        """
        PHPP V10 | Heating | R104

        Formula: =Areas!BU35

        Units: W/K (watts per kelvin)
        """
        return self.phpp.areas.envelope_convective_factor_W_K

    @property
    def radiation_factor_W_K(self) -> float:
        """
        PHPP V10 | Heating | R105

        Formula: =Areas!BT35

        Units: W/K (watts per kelvin)
        """
        return self.phpp.areas.envelope_radiative_factor_W_K

    @property
    def time_constant(self) -> float:
        """
        PHPP V10 | Heating | R117

        =IF(R101+R100+R103+R104+R105=0,0,R114/(R101+R100+R103+R104+R105))
        """
        if (
            self.conductance_factor_to_outdoor_air
            + self.ground_conductivity_for_time_constant
            + self.conductance_factor_to_EWU
            + self.convection_factor_W_K
            + self.radiation_factor_W_K
            == 0
        ):
            return 0.0
        else:
            return self.heat_capacity_Wh_K / (
                self.conductance_factor_to_outdoor_air
                + self.ground_conductivity_for_time_constant
                + self.conductance_factor_to_EWU
                + self.convection_factor_W_K
                + self.radiation_factor_W_K
            )

    @property
    def a_monthly_procedure(self) -> float:
        """
        PHPP V10 | Heating | R118

        =1+R117/16
        """
        return 1 + self.time_constant / 16

    # ------------------------------------------------------------------------------------------------------------------
    # -- Effective Window Areas  ---------------------------------------------------------------------------------------
    @property
    def north_effective_window_area_m2(self) -> float:
        """
        PHPP V10 | Heating | R106

        =IF(ISNUMBER(I54),G54*I54*K54,0)

        Units: M2
        """
        return self.phpp.areas.windows.north.winter_eff_solar_gain_area_m2

    @property
    def east_effective_window_area_m2(self) -> float:
        """
        PHPP V10 | Heating | R106

        =IF(ISNUMBER(I55),G55*I55*K55,0)

        Units: M2
        """

        return self.phpp.areas.windows.east.winter_eff_solar_gain_area_m2

    @property
    def south_effective_window_area_m2(self) -> float:
        """
        PHPP V10 | Heating | R106

        =IF(ISNUMBER(I56),G56*I56*K56,0)

        Units: M2
        """
        return self.phpp.areas.windows.south.winter_eff_solar_gain_area_m2

    @property
    def west_effective_window_area_m2(self) -> float:
        """
        PHPP V10 | Heating | R106

        =IF(ISNUMBER(I57),G57*I57*K57,0)

        Units: M2
        """
        return self.phpp.areas.windows.west.winter_eff_solar_gain_area_m2

    @property
    def horizontal_effective_window_area_m2(self) -> float:
        """
        PHPP V10 | Heating | R110

        =IF(ISNUMBER(I58),G58*I58*K58,0)

        Units: M2
        """
        return self.phpp.areas.windows.horizontal.winter_eff_solar_gain_area_m2

    # ------------------------------------------------------------------------------------------------------------------
    # -- Internal Gains  -----------------------------------------------------------------------------------------------
    @property
    def internal_heat_gain_rate_W(self) -> float:
        """
        PHPP V10 | Heating | R112

        =$K$65*$M$65

        Units: W
        """
        return self.phpp.ihg.average_annual_internal_heat_gain_W

    @property
    def specific_heat_capacity_Wh_m2K(self) -> float:
        """
        PHPP V10 | Heating | R113

        =IF(ISNUMBER(O10),IF(O10<10,10,IF(O10>500,500,O10)),10)

        Units: Wh/m2-K
        """
        return max(min(self.phpp.areas.specific_heat_capacity_Wh_m2K, 500), 10)

    @property
    def heat_capacity_Wh_K(self) -> float:
        """
        PHPP V10 | Heating | R114

        =R113*O9

        Units: Wh/K
        """
        return (
            self.specific_heat_capacity_Wh_m2K
            * self.phpp.rooms.total_weighted_floor_area_m2
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Losses  --------------------------------------------------------------------------------------------------
    @property
    def transmission_heat_loss_to_ambient(self) -> list[float]:
        """
        PHPP V10 | Heating | T101:AE101

        =$R101*T97

        Units: kwh (kilowatt-hours per period)
        """
        return [p.transmission_heat_loss_to_ambient for p in self.periods]

    @property
    def transmission_heat_loss_to_ground(self) -> list[float]:
        """
        PHPP V10 | Heating | T102:AE102

        Ground!E112*T96/1000

        Units: kwh (kilowatt-hours per period)
        """
        return [p.transmission_heat_loss_to_ground for p in self.periods]

    @property
    def convective_heat_loss_to_EWU(self) -> list[float]:
        """
        PHPP V10 | Heating | T103:AE103

        =$R103*T100

        Units: kwh (kilowatt-hours per period)
        """
        return [p.convective_heat_loss_to_EWU for p in self.periods]

    @property
    def convective_heat_loss_to_ambient(self) -> list[float]:
        """
        PHPP V10 | Heating | T104:AE104

        =$R104*T97

        Units: kwh
        """
        return [p.convective_heat_loss_to_ambient for p in self.periods]

    @property
    def radiative_heat_loss_to_sky(self) -> list[float]:
        """
        PHPP V10 | Heating | T105:AE105

        =$R105*T98

        Units: kwh
        """
        return [p.radiative_heat_loss_to_sky for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Gains  ---------------------------------------------------------------------------------------------------
    @property
    def north_window_solar_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T106:AE106

        =$R106*T91

        Units: kwh
        """
        return [p.north_window_solar_heat_gain for p in self.periods]

    @property
    def east_window_solar_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T107:AE107

        =$R107*T92

        Units: kwh
        """
        return [p.east_window_solar_heat_gain for p in self.periods]

    @property
    def south_window_solar_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T108:AE108

        =$R108*T93

        Units: kwh
        """
        return [p.south_window_solar_heat_gain for p in self.periods]

    @property
    def west_window_solar_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T109:AE109

        =$R109*T94

        Units: kwh
        """
        return [p.west_window_solar_heat_gain for p in self.periods]

    @property
    def horizontal_window_solar_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T110:AE110

        =$R110*T95

        Units: kwh
        """
        return [p.horizontal_window_solar_heat_gain for p in self.periods]

    @property
    def opaque_surface_solar_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T111:AE111

        =Areas!CP9

        Units: kwh
        """
        return [p.opaque_surface_solar_heat_gain for p in self.periods]

    @property
    def internal_heat_gain(self) -> list[float]:
        """
        PHPP V10 | Heating | T112:AE112

        =IF(Moni!AJ9,$R112*T96/1000,Moni!AK142*Heating!AD9*T96/1000)

        Units: kwh
        """
        return [p.internal_heat_gain for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Energy Balance  -----------------------------------------------------------------------------------------------
    @property
    def total_heat_losses(self) -> list[float]:
        """
        PHPP V10 | Heating | T113:AE113

        =T101+T102+T103+T104+T105

        Units: kwh
        """
        return [p.total_heat_loss for p in self.periods]

    @property
    def total_heat_gains(self) -> list[float]:
        """
        PHPP V10 | Heating | T114:AE114

        =SUM(T106:T112)

        Units: kwh
        """
        return [p.total_heat_gain for p in self.periods]

    @property
    def gain_to_loss_ratio(self) -> list[float]:
        """
        PHPP V10 | Heating | T115:AE115

        =IF(OR(T113=0,ABS(T113)< 0.001*ABS(T114)),0,T114/T113)

        Units: %
        """
        return [p.gain_to_loss_ratio for p in self.periods]

    @property
    def utilization_factor(self) -> list[float]:
        """
        PHPP V10 | Heating | T116:AE116

        =IF(T115>0,IF(T115=1,$R$118/($R$118+1),(1-T115^$R$118)/(1-T115^($R$118+1))),1)

        Units: %
        """
        return [p.utilization_factor for p in self.periods]

    @property
    def heating_demand(self) -> list[float]:
        """
        PHPP V10 | Heating | T117:AE117

        =MAX(0,T113-T116*T114)

        Units: kwh
        """
        return [p.heating_demand for p in self.periods]

    @property
    def total_yearly_heating_demand(self):
        """

        PHPP V110 | Heating | AF117

        =SUM(T117:AE117)

        Units: kwh
        """
        return sum(self.heating_demand)

    @property
    def in_heating_period(self) -> list[bool]:
        """
        PHPP V10 | Heating | T118:AE118

        =T117>$AF$117*0.001

        Units: kwh
        """
        return [p.in_heating_period for p in self.periods]

    # -------------------------------------------------------------------------
    # -- Window Solar Gain  ---------------------------------------------------
    def get_window_surface_period_total_radiation_for_orientation(
        self, _orientation: enums.CardinalOrientation
    ) -> list[float]:
        """Total effective window radiation for each period by specified orientation.

        PHPP V10 | Windows | GF6:GQ10 (Orientation-Specific Window Radiation)

        Returns a list of total effective window solar radiation values for
        each calculation period, filtered by the specified cardinal orientation.
        This method aggregates radiation across all window surfaces of the
        same orientation to provide orientation-specific totals:
        - Sum of all north-facing windows (if orientation = NORTH)
        - Sum of all south-facing windows (if orientation = SOUTH)
        - Sum of all east-facing windows (if orientation = EAST)
        - Sum of all west-facing windows (if orientation = WEST)

        Data structure format:
        [
            period_1_orientation_total,
            period_2_orientation_total,
            ...
        ]

        Applications:
        - Orientation-specific solar analysis and design optimization
        - Comparative assessment of building facade performance
        - Solar shading strategy development by orientation
        - Building massing and window placement decisions

        Used to understand the solar performance characteristics of
        different building orientations for design optimization.

        Args:
            _orientation: Cardinal orientation enumeration (NORTH, EAST, SOUTH, WEST)

        Units: W/m² or kwh/m² per period (effective solar irradiance/irradiation)
        """
        return [
            p.period_solar_radiation.get_window_surface_total_radiation_for_orientation(
                _orientation
            )
            for p in self.periods
        ]

    def get_window_surface_period_total_radiation_per_m2_for_orientation(
        self, _orientation: enums.CardinalOrientation
    ) -> list[float]:
        """Total effective window radiation per unit glazing area by orientation.

        PHPP V10 | Windows | GF6:GQ10 (Window Radiation Intensity by Orientation)

        Returns a list of total effective window solar radiation values per
        square meter of glazing area for each calculation period, filtered by
        the specified cardinal orientation. This method provides normalized
        radiation intensity values for:
        - Comparison across different window sizes and orientations
        - Glazing area-independent solar performance assessment
        - Window specification and sizing optimization
        - Solar heat gain coefficient (SHGC) analysis

        Calculation: Total Radiation / Total Glazing Area for Orientation

        Data structure format:
        [
            period_1_radiation_per_m2,
            period_2_radiation_per_m2,
            ...
        ]

        Applications:
        - Window glazing specification and selection
        - Solar heat gain coefficient optimization
        - Orientation-specific shading strategy design
        - Building envelope performance benchmarking

        Useful for understanding solar radiation intensity independent
        of total window area for each orientation.

        Args:
            _orientation: Cardinal orientation enumeration (NORTH, EAST, SOUTH, WEST)

        Units: W/m² or kwh/m² per period per m² glazing (radiation intensity)
        """
        return [
            p.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                _orientation
            )
            for p in self.periods
        ]
