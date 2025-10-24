# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Calculation class and with methods for: PHPP | Cooling."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

    from openph_demand.solvers import OpPhEnergyDemandSolver, OpPhGroundSolver

from openph.model import enums
from openph_solar.get_solvers import get_openph_solar_solver
from openph_solar.solvers import OpPhSolarRadiationSolver

from openph_demand.cooling_demand.calc_periods import OpPhCoolingDemandCalcPeriod
from openph_demand.cooling_demand.peak_month import OpPhCoolingDemandPeakMonth
from openph_demand.get_solvers import (
    get_openph_energy_demand_solver,
    get_openph_ground_solver,
)


@dataclass
class OpPhCoolingDemand:
    """Annual Cooling Energy Demand solver."""

    phpp: "OpPhPHPP"
    _periods: list[OpPhCoolingDemandCalcPeriod] = field(default_factory=list)
    peak_month: OpPhCoolingDemandPeakMonth = field(init=False)

    def __post_init__(self) -> None:
        """Setup all of the calculation-periods for the cooling demand."""
        for climate_period, ground_period, window_period in zip(
            self.phpp.climate.periods,
            self.ground_solver.periods,
            self.solar_radiation.annual_demand.periods,
        ):
            self._periods.append(
                OpPhCoolingDemandCalcPeriod(
                    self.phpp,
                    climate_period,
                    ground_period,
                    window_period,
                )
            )
        self.peak_month = OpPhCoolingDemandPeakMonth(self.phpp)

    @cached_property
    def solar_radiation(self) -> "OpPhSolarRadiationSolver":
        """Return the instance of the Solar Radiation Solver."""
        return get_openph_solar_solver(self.phpp)

    @cached_property
    def ground_solver(self) -> "OpPhGroundSolver":
        """Return the instance of the Ground Solver."""
        return get_openph_ground_solver(self.phpp)

    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def periods(self) -> list[OpPhCoolingDemandCalcPeriod]:
        """A list of the Cooling-Demand calculation periods."""
        return self._periods

    @property
    def period_hours(self) -> list[int]:
        """Number of hours in each calculation period in the cooling analysis.

        PHPP V10 | Cooling | T107:AE107

        Units: hours per period
        """
        return [p.period_climate.period_length_hours for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Climate Data Inputs PHPP V10 | Cooling | S82:AF92

    @property
    def temperature_ground_c(self) -> list[float]:
        """A list of each period's ground-temperature.

        PHPP V10 | Cooling | T92:AF92

        Ground Temp
        =IF($R$113>0,$E$9-T113*1000/($R$113*T107),Ground!$P$11)

        Units: C
        """
        return [p.temperature_ground_c for p in self.periods]

    # TODO: make aliases for the other climate inputs....

    # ------------------------------------------------------------------------------------------------------------------
    # -- Building Attribute Values | PHPP V10 | Cooling | O106:R151
    @property
    def envelope_total_conductance_W_K(self) -> float:
        """The total envelope heat-loss-coeffient, including conduction, convection, and radiation.

        PHPP V10 | Cooling | R109

        Leitwert Transmission ges W/K
        =R112+R113+R114+R115

        Units: W/K
        """
        return (
            self.envelop_conductance_to_ambient_air_W_K
            + self.envelop_conductance_to_ground_W_K
            + self.envelope_convective_factor_W_K
            + self.envelope_radiative_factor_W_K
        )

    @property
    def envelop_conductance_to_ground_for_time_constant_W_K(self) -> float:
        """
        PHPP V10 | Cooling | R110

        Leitwert Erdreich f. Zeitkonstante W/K
        =IF(ISNUMBER(Ground!H119),Ground!H119,IF(ISNUMBER(Ground!H218),Ground!H218,R113))

        Units: W/K
        """
        if self.ground_solver.conductance_to_ground_W_K:
            return self.ground_solver.conductance_to_ground_W_K
        elif self.ground_solver.estimated.conductance_to_ground_W_K:
            return self.ground_solver.estimated.conductance_to_ground_W_K
        else:
            return self.phpp.areas.envelop_conductance_to_ground_W_K

    @property
    def average_ground_surface_temp_C(self) -> float:
        """The average ground surface temperature.

        PHPP V10 | Cooling | R111

        Temperatur EWÜ °C
        =Ground!$P$11

        Units: C
        """
        return self.ground_solver.average_ground_surface_temp_C

    @property
    def envelop_conductance_to_ambient_air_W_K(self) -> float:
        """The envelope conductive heat-loss to ambient air coefficient

        PHPP V10 | Cooling | R112

        Transmissionsleitwert außen W/K
        =SUMPRODUCT($G$16:$G$27,$I$16:$I$27,$K$16:$K$27)-R113

        Units: W/K
        """
        return self.phpp.areas.envelop_conductance_to_ambient_air_W_K

    @property
    def envelop_conductance_to_ground_W_K(self) -> float:
        """The envelope conductive heat-loss to ground coefficient

        PHPP V10 | Cooling | R113

        Transmissionsleitwert Erdreich W/K
        =SUMPRODUCT($G$16:$G$27,$I$16:$I$27,IF($F$16:$F$27="B",1,0))

        Units: W/K
        """
        return self.phpp.areas.envelop_conductance_to_ground_W_K

    @property
    def envelope_convective_factor_W_K(self) -> float:
        """The envelope convective heat-loss coefficient

        PHPP V10 | Cooling | R114

        Korrektur LW konvektiv W/K
        =Areas!BU35

        Units: W/K
        """
        return self.phpp.areas.envelope_convective_factor_W_K

    @property
    def envelope_radiative_factor_W_K(self) -> float:
        """The envelope radiation heat-loss coefficient.

        PHPP V10 | Cooling | R115

        LW radiativ W/K
        =Areas!BT35

        Units: W/K
        """
        return self.phpp.areas.envelope_radiative_factor_W_K

    @property
    def average_annual_internal_heat_gain_W(self) -> float:
        """The average annual internal heat gain rate.

        PHPP V10 | Cooling | R148

        Interne Last W
        =$K$77*$M$77

        Units: W
        """
        return self.phpp.ihg.average_annual_internal_heat_gain_W

    @property
    def specific_heat_capacity_Wh_m2K(self) -> float:
        """The specific heat capacity of the building.

        PHPP V10 | Cooling | R150

        spez. Kapazität Wh/(m²K)
        =IF(ISNUMBER(E11),IF(E11<10,10,IF(E11>500,500,E11)),10)

        Units: Wh/m2-K
        """
        return max(min(self.phpp.areas.specific_heat_capacity_Wh_m2K, 500), 10)

    # ------------------------------------------------------------------------------------------------------------------
    # -- Calculated Climate Values

    @property
    def outdoor_air_water_vapor_pressure_Pa(self) -> list[float]:
        """A list of each periopd's outdoor air water vapor pressure.

        PHPP V10 | Cooling | T131:AE131

        Wasserdampfdruck Außenluft Pa
        =611*EXP(0.000191275+0.07258*T90-0.0002939*T90^2+0.0000009841*T90^3-0.00000000192*T90^4)

        Units: Pa (pascals)
        """
        return [
            p.period_climate.outdoor_air_water_vapor_pressure_Pa for p in self.periods
        ]

    @property
    def outdoor_air_absolute_humidity_kg_kg(self) -> list[float]:
        """A list each period's of the outdoor air absolute humidity.

        PHPP V10 | Cooling | T132:AE132

        abs. Feuchte Außenluft kg/kg
        =0.6222*T131/(101300-T131)

        Units: kg/kg
        """
        return [
            p.period_climate.outdoor_air_absolute_humidity_kg_kg for p in self.periods
        ]

    @property
    def conductance_for_time_constant_W_K(self):
        """The total building conductive heat-loss coefficient for the time-constant calculation.

        PHPP V10 | Cooling | R149

        Leitwert Transmission für Zeitkonstante W/K
        =R112+R110+R114+R115

        Units: W/K
        """
        return sum(p.conductance_for_time_constant_W_K for p in self.periods) / len(
            self.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Balanced Mechanical Ventilation (HRV/ERV)

    @property
    def balanced_mech_vent_kilodegree_hours_ground_heat_exchanger(self) -> list[float]:
        """Temperature-time product for ground-coupled heat exchanger (EWU) systems.

        PHPP V10 | Cooling | T111:AE111

        Units: kKhr
        """
        return [
            p.balanced_mech_vent_kilodegree_hours_to_ground_kKhr
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_conductance_to_air_W_K(self) -> list[float]:
        """Thermal conductance of ventilation air flow for cooling calculations.

        PHPP V10 | Cooling | T125:AE125

        Leitwert Lüftung außen
        =IF(T124,$D$34,$D$35)+$D$39

        Units: W/K
        """

        return [
            p.balanced_mech_vent_conductance_to_air_W_K
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_conductance_to_soil_W_K(self) -> list[float]:
        """Thermal conductance of ventilation system ground coupling.

        PHPP V10 | Cooling | T126:AE126

        Leitwert Lüftung Erdreich
        =IF(T124,$D$36,$D$37)

        Units: W/K
        """

        return [
            p.balanced_mech_vent_conductance_to_soil_W_K
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_temperature_without_heat_recovery_C(
        self,
    ) -> list[float]:
        """Supply air temperature without heat recovery for this calculation period.

        PHPP V10 | Cooling | T116:AE116

        T_Zuluft ohne WRG
        =$D$43*$R$111+(1-$D$43)*T84

        Units: C
        """

        return [
            p.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_temperature_with_heat_recovery_C(
        self,
    ) -> list[float]:
        """Supply air temperature with heat recovery for this calculation period.

        PHPP V10 | Cooling | T121:AE121

        T_Zuluft mit WRG (bei Soll-Innenbedingungen) °C
        =T116+$D$41*($E$9-T116)

        Units: C
        """

        return [
            p.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C(
        self,
    ) -> list[float]:
        """Dew point temperature of supply air without heat recovery.

        PHPP V10 | Cooling | T117:AE117

        Taupunkttemp Zuluft ohne WRG
        =MIN(T90,T116)

        Units: C
        """

        return [
            p.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa(
        self,
    ) -> list[float]:
        """Water vapor pressure of supply air without heat recovery.

        PHPP V10 | Cooling | T118:AE118

        Wasserdampfdruck Zuluft ohne WRG Pa
        =611EXP(0.000191275+0.07258T117-0.0002939T117^2+0.0000009841T117^3-0.00000000192*T117^4)

        Units: Pa
        """

        return [
            p.balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg(
        self,
    ) -> list[float]:
        """Absolute humidity of supply air without heat recovery.

        PHPP V10 | Cooling | T119:AE119 (abs. Feuchte Zuluft ohne WRG kg/kg)

        abs. Feuchte Zuluft ohne WRG kg/kg
        =0.6222*T118/(101300-T118)

        Units: kg/kg
        """

        return [
            p.balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg(
        self,
    ) -> list[float]:
        """Absolute humidity of supply air with heat recovery at target indoor conditions.

        PHPP V10 | Cooling | T122:AE122

        abs. Feuchte Zuluft mit WRG (bei Soll-Innenbedingungen) kg/kg
        =T119+$D$42*($E$10/1000-T119)

        Units: kg/kg
        """

        return [
            p.balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_enthalpy_without_heat_recovery_kJ_kG(
        self,
    ) -> list[float]:
        """Enthalpy of supply air without heat recovery.

        PHPP V10 | Cooling | T120:AE120

        Enthalpie Zuluft ohne WRG kJ/kg tr. Luft
        =1.01T116 + T119(2501+1.86*T116)

        Units: kJ/kg
        """

        return [
            p.balanced_mech_vent_supply_air_enthalpy_without_heat_recovery_kJ_kG
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_enthalpy_with_heat_recovery_kJ_kg(
        self,
    ) -> list[float]:
        """Enthalpy of supply air with heat recovery.

        PHPP V10 | Cooling | T123:AE123

        Enthalpie Zuluft mit WRG
        =1.01T121 + T122(2501+1.86*T121)

        Units: kJ/kg
        """

        return [
            p.balanced_mech_vent_supply_air_enthalpy_with_heat_recovery_kJ_kg
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_is_supply_air_at_target_indoor_conditions(
        self,
    ) -> list[bool]:
        """Determines if supply air meets target indoor conditions after heat recovery.

        PHPP V10 | Cooling | T124:AE124

        WRG/FRG ein? (bei Soll-Innenbedingungen)
        =IF($O$35="x",FALSE,IF($O$36="x",T121<T116,IF($O$37="x",T123<T120,TRUE)))

        Units: Boolean
        """

        return [
            p.balanced_mech_vent_is_supply_air_at_target_indoor_conditions
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_supply_air_mass_flow_kg_hour(self) -> list[float]:
        """Mass flow rate of mechanical ventilation air for this calculation period.

        PHPP V10 | Cooling | T127:AE127

        Massenstrom Zuluft kg/h
        =$J$37*$O$9*1.18

        Units: kg/h
        """

        return [
            p.balanced_mech_vent_supply_air_mass_flow_kg_hour
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_heat_loss_to_ambient_air_kwh(self) -> list[float]:
        """Mechanical ventilation heat removal through ambient air exchange.

        PHPP V10 | Cooling | T129:AE129

        Lüftungsverlust außen
        =T125*T108

        Units: kwh
        """

        return [
            p.balanced_mech_vent_heat_loss_to_ambient_air_kwh
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_heat_loss_to_ground_kwh(self) -> list[float]:
        """Ground-coupled heat exchanger cooling effect for mechanical ventilation.

        PHPP V10 | Cooling | T130:AE130

        Lüftungsverlust EWÜ
        =T126*T111

        Units: kwh
        """

        return [
            p.balanced_mech_vent_heat_loss_to_ground_kwh
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def balanced_mech_vent_total_heat_loss_kwh(self) -> list[float]:
        """Total heat losses from mechanical ventilation system.
        Units: kwh
        """

        return [
            p.balanced_mech_vent_total_heat_loss_kwh
            for p in self.energy_demand.cooling_demand.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Exhaust Mechanical Ventilation

    @property
    def exhaust_mech_vent_time_constant(self) -> list[float]:
        """Time constant for summer ventilation operation during this period.

        PHPP V10 | Cooling | T133:AE133

        t_end Sommerlüftung konst
        =IF($O$41="x",IF($E$10*0.001>T132,6,-6),
        IF($E$9>=T84+$J$42+$J$34/2,6,IF($E$9<=T84+$J$42-$J$34/2,-6,12/PI()ASIN(($E$9-T84-$J$42)/$J$342))) )

        Units: hours
        """

        return [
            p.exhaust_mech_vent_time_constant
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def exhaust_mech_vent_average_temperature_C(self) -> list[float]:
        """Average temperature for summer ventilation during this period.

        PHPP V10 | Cooling | T134:AE134

        Atemp Sommlüft konst
        =IF(T133 > -5.99,T84-6*$J$34/(PI()*(T133+6))*COS(PI()*T133/12),T84-$J$34/2)+$J$42

        Units: °C
        """

        return [
            p.exhaust_mech_vent_average_temperature_C
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def exhaust_mech_vent_thermal_conductance_W_K(self) -> list[float]:
        """Thermal conductance for summer ventilation during this period.

        PHPP V10 | Cooling | T135:AE135

        Leitwert Sommlüft konst
        =IF($J$40>0,1/(1/($J$36*$J$40*$O$9)+1/(1.54.5$O$8)) * (T133+6)/12,0)

        Units: W/K
        """

        return [
            p.exhaust_mech_vent_thermal_conductance_W_K
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def exhaust_mech_vent_total_heat_loss_kwh(self) -> list[float]:
        """Additional summer ventilation cooling extraction (night purge ventilation).

        PHPP V10 | Cooling | T136:AE136

        Verlust Sommlüft konst
        =IF(Moni!AJ9,T135*($R$108-T134)T107/1000,T135(Moni!AK118-T134)*T107/1000)

        Units: kwh
        """

        return [
            p.exhaust_mech_vent_total_heat_loss_kwh
            for p in self.energy_demand.cooling_demand.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Envelope Ventilation (Windows and Air-Leakage)

    @property
    def envelope_vent_air_mass_flow_rate_kg_hour(self) -> list[float]:
        """Mass flow rate of passive ventilation air for this calculation period.

        PHPP V10 | Cooling | T127:AE127

        Massenstrom Zuluft kg/h
        =$J$37*$O$9*1.18

        Units: kg/h
        """

        return [
            p.envelope_vent_air_mass_flow_rate_kg_hour
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def envelope_vent_air_average_temperature_C(self) -> list[float]:
        """Average temperature for natural window ventilation during this period.

        PHPP V10 | Cooling | T137:AE137
        Atemp Fenstlüft
        =T84-2/PI()*$J$34/2

        Units: C
        """

        return [
            p.envelope_vent_air_average_temperature_C
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def envelope_vent_air_volume_flow_rate_m3_hour(self) -> list[float]:
        """Volume flow rate for natural window ventilation during this period.

        PHPP V10 | Cooling | T138:AE138

        Volumenstrom Fenstlüft m³/h
        =$J$39*$O$9*SQRT(ABS($E$9-T137))

        Units: m³/h
        """

        return [
            p.envelope_vent_air_volume_flow_rate_m3_hour
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def envelope_vent_window_achievable_thermal_conductance_W_K(self) -> list[float]:
        """Achievable thermal conductance for natural window ventilation during this period.

        PHPP V10 | Cooling | T139:AE139

        erreichbarer Leitwert Fenstlüft W/K
        =IF(T138>0,1/(1/($J$36*T138)+1/(1.5*4.5*$O$8))/2,0)

        Units: W/K
        """

        return [
            p.envelope_vent_window_achievable_thermal_conductance_W_K
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def envelope_vent_window_effective_thermal_conductance_W_K(self) -> list[float]:
        """Effective thermal conductance for natural window ventilation considering environmental conditions.

        PHPP V10 | Cooling | T140:AE140

        Leitwert Fenstlüft W/K
        =IF(AND(T137<$E$9,T132*1000<$E$10),T139,0)

        Units: W/K
        """

        return [
            p.envelope_vent_window_effective_thermal_conductance_W_K
            for p in self.energy_demand.cooling_demand.periods
        ]

    @property
    def envelope_vent_total_heat_loss_kwh(self) -> list[float]:
        """Total Heat losses through natural window ventilation.

        PHPP V10 | Cooling | T141:AE141

        Verlust Fenstlüft kwh
        =IF(Moni!AJ9,T140*($R$108-T137)T107/1000,T140(Moni!AK118-T137)*T107/1000)

        Units: kwh
        """

        return [
            p.envelope_vent_total_heat_loss_kwh
            for p in self.energy_demand.cooling_demand.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Losses

    @property
    def kilodegree_hours_ground_kK_hr(self) -> list[float]:
        """A list of each period's degree-hours to the ground.

        PHPP V10 | Cooling | T110:AE110

        HeizgrSt. Grund
        =IF($R$113>0,T113/$R$113,0)

        Units: K⋅h/1000
        """
        return [p.kilo_degree_hours_to_ground_kK_hr for p in self.periods]

    @property
    def conductive_heat_loss_to_ambient_air_kwh(self) -> list[float]:
        """A list of each period's transmission heat losses through building envelope to ambient air.

        PHPP V10 | Cooling | T112:AE112

        Transmissionsverluste außen
        =$R112*T108

        Units: kwh
        """
        return [p.conductive_heat_loss_to_ambient_air_kwh for p in self.periods]

    @property
    def conductive_heat_loss_to_ground_kwh(self) -> list[float]:
        """A list of each period's transmission heat losses through building envelope to ground.

        PHPP V10 | Cooling | T113:AE113

        Verluste Grund
        =Ground!E112*T107/1000

        Units: kwh
        """
        return [p.conductive_heat_loss_to_ground_kwh for p in self.periods]

    @property
    def convective_heat_loss_to_ambient_kwh(self) -> list[float]:
        """A list of each period's convective heat losses.

        PHPP V10 | Cooling | T114:AE114

        zus. Verlust außen konvektiv
        =$R114*T108

        Units: kwh
        """
        return [p.convective_heat_loss_to_ambient_kwh for p in self.periods]

    @property
    def radiative_heat_loss_to_sky_kwh(self) -> list[float]:
        """A list of each period's radiative heat losses.

        PHPP V10 | Cooling | T115:AE115

        zus. Verlust außen radiativ
        =$R115*T109

        Units: kwh
        """
        return [p.radiative_heat_loss_to_sky_kwh for p in self.periods]

    @property
    def total_heat_loss_kwh(self) -> list[float]:
        """A list of each period's total heat losses from all building systems and envelope components.

        PHPP V10 | Cooling | T149:AE149

        Summe Verl
        =T112+T113+T114+T115+T129+T130+T136+T141

        Units: kwh
        """
        return [p.total_heat_loss_kwh for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Heat Gains

    @property
    def solar_heat_gain_north_windows_kwh(self) -> list[float]:
        """A list of each period's solar heat gains through north-facing windows.

        PHPP V10 | Cooling | T142:AE142

        Solar Nord
        =$R142*T102

        Units: kwh
        """
        return [p.solar_heat_gain_north_windows_kwh for p in self.periods]

    @property
    def solar_heat_gain_east_windows_kwh(self) -> list[float]:
        """A list of each period's solar heat gains through east-facing windows.

        PHPP V10 | Cooling | T143:AE143

        Solar Ost
        =$R143*T103

        Units: kwh
        """
        return [p.solar_heat_gain_east_windows_kwh for p in self.periods]

    @property
    def solar_heat_gain_south_windows_kwh(self) -> list[float]:
        """A list of each period's solar heat gains through south-facing windows.

        PHPP V10 | Cooling | T144:AE144

        Solar Süd
        =$R144*T104

        Units: kwh
        """
        return [p.solar_heat_gain_south_windows_kwh for p in self.periods]

    @property
    def solar_heat_gain_west_windows_kwh(self) -> list[float]:
        """A list of each period's solar heat gains through west-facing windows.

        PHPP V10 | Cooling | T145:AE145

        Solar West
        =$R145*T105

        Units: kwh
        """
        return [p.solar_heat_gain_west_windows_kwh for p in self.periods]

    @property
    def solar_heat_gain_horizontal_windows_kwh(self) -> list[float]:
        """A list of each period's solar heat gains through horizontal glazing (skylights and roof windows).

        PHPP V10 | Cooling | T146:AE146

        Solar Hori
        =$R146*T106

        Units: kwh
        """
        return [p.solar_heat_gain_horizontal_windows_kwh for p in self.periods]

    @property
    def solar_heat_gain_opaque_kwh(self) -> list[float]:
        """A list of each period's solar heat gains through opaque building envelope elements.

        PHPP V10 | Cooling | T147:AE147

        Solar opak
        =Areas!CP10

        Units: kwh
        """
        return [p.solar_heat_gain_opaque_kwh for p in self.periods]

    @property
    def internal_heat_gain_kwh(self) -> list[float]:
        """A list of each period's internal heat gains.

        PHPP V10 | Cooling | T148:AE148

        Interne WQ
        =IF(Moni!AJ9,$R148*T107/1000,Moni!AK142*Cooling!$O$8*T107/1000)

        Units: kwh
        """
        return [p.internal_heat_gain_kwh for p in self.periods]

    @property
    def total_heat_gain_kwh(self) -> list[float]:
        """A list of each period's total heat gains from internal and solar.

        PHPP V10 | Cooling | T150:AE150

        Summe Ang
        =SUM(T142:T148)

        Units: kwh
        """
        return [p.total_heat_gain_kwh for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Energy Balance Calculations

    @property
    def time_constant(self) -> list[float]:
        """A list of each period's thermal-time-constant.

        PHPP V10 | Cooling | T151:AE151

        Zeitkonstante h
        =IF( $R$149+T125+T126=0, 0, $R$151/($R$149+T125+T126))

        Units: hours
        """
        return [p.time_constant for p in self.periods]

    @property
    def monthly_procedure_factor(self) -> list[float]:
        """A list of each period's heat-gain-utilization-factor.

        PHPP V10 | Cooling | T152:AE152

        a_Monatsverfahren
        =1+T151/16

        Units: Dimensionless factor (-)
        """
        return [p.monthly_procedure_factor for p in self.periods]

    @property
    def loss_to_gain_ratio(self) -> list[float]:
        """A list of each period's ratio of building heat losses to heat gains.

        PHPP V10 | Cooling | T153:AE153

        Verl/Ang
        =IF(ABS(T150)<0.01,0,T149/T150)

        Units: Dimensionless ratio (-)
        """
        return [p.loss_to_gain_ratio for p in self.periods]

    @property
    def utilization_factor(self) -> list[float]:
        """A list of each period's heat-loss-efficiency-factor.

        PHPP V10 | Cooling | T154:AE154

        Nutzungsgrad Wärmeverluste
        =IF(T153>0,IF(T153=1,T152/(T152+1),(1-T153^T152)/(1-T153^(T152+1))),1)

        Units: -
        """
        return [p.utilization_factor for p in self.periods]

    @property
    def cooling_demand_kwh(self) -> list[float]:
        """A list of each period's useful cooling demand.

        PHPP V10 | Cooling | T155:AE155

        Nutzkälte
        =MAX(0,T150-T154*T149)

        Units: kwh
        """
        return [p.cooling_demand_kwh for p in self.periods]

    @property
    def in_cooling_period(self) -> list[bool]:
        """Boolean indicator for periods requiring active cooling.

        PHPP V10 | Cooling | T156:AE156

        Kühlperiode?
        =AND(T82<>$AI$82,T155>$AG$155*0.001)

        Units: Boolean per period
        """
        return [p.in_cooling_period for p in self.periods]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Opaque Surface Radiation -------------------------------------------------------------------------------------

    @property
    def opaque_surface_radiation_south(self) -> list[list[float]]:
        """Solar radiation values for south-facing opaque surfaces by calculation period.

        PHPP V10 | Areas | CM41:CX140

        Data structure format:
        [
            period_1: [surface_1, surface_2, ...],
            period_2: [surface_1, surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.opaque_surface_radiation_south_kwh_m2
            for p in self.periods
        ]

    @property
    def opaque_surface_radiation_north(self) -> list[list[float]]:
        """Solar radiation values for north-facing opaque surfaces by calculation period.

        PHPP V10 | Areas | DB41:DL140

        Data structure format:
        [
            period_1: [surface_1, surface_2, ...],
            period_2: [surface_1, surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.opaque_surface_radiation_north_kwh_m2
            for p in self.periods
        ]

    @property
    def opaque_surface_radiation_west(self) -> list[list[float]]:
        """Solar radiation values for west-facing opaque surfaces by calculation period.

        PHPP V10 | Areas | DQ41:EB140

        Data structure format:
        [
            period_1: [surface_1, surface_2, ...],
            period_2: [surface_1, surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.opaque_surface_radiation_west_kwh_m2
            for p in self.periods
        ]

    @property
    def opaque_surface_radiation_east(self) -> list[list[float]]:
        """Solar radiation values for east-facing opaque surfaces by calculation period.

        PHPP V10 | Areas | EF41:EQ140

        Data structure format:
        [
            period_1: [surface_1, surface_2, ...],
            period_2: [surface_1, surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.opaque_surface_radiation_east_kwh_m2
            for p in self.periods
        ]

    @property
    def opaque_surface_radiation_total_effective(self) -> list[list[float]]:
        """Total effective solar radiation values for all opaque surfaces by calculation period.

        PHPP V10 | Areas | EU41:FF140

        Data structure format:
        [
            period_1: [surface_1_total, surface_2_total, ...],
            period_2: [surface_1_total, surface_2_total, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.opaque_surface_total_effective_radiation
            for p in self.periods
        ]

    @property
    def opaque_surface_radiation_total(self) -> list[float]:
        """Total solar heat gains through opaque building surfaces by calculation period.

        PHPP V10 | Areas | CP5:DA5

        Data structure format:
        [
            period_1_total_opaque_gains,
            period_2_total_opaque_gains,
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.opaque_surface_solar_heat_gain_kwh
            for p in self.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Window Surface Radiation -------------------------------------------------------------------------------------

    @property
    def window_surface_radiation_south(self) -> list[list[float]]:
        """Solar radiation values for south-facing window surfaces by calculation period.

        PHPP V10 | Windows | GF23:GQ174

        Data structure format:
        [
            period_1: [window_surface_1, window_surface_2, ...],
            period_2: [window_surface_1, window_surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.window_radiation_south_kwh for p in self.periods
        ]

    @property
    def window_surface_radiation_north(self) -> list[list[float]]:
        """Solar radiation values for north-facing window surfaces by calculation period.

        PHPP V10 | Windows | GX23:HI174

        Data structure format:
        [
            period_1: [window_surface_1, window_surface_2, ...],
            period_2: [window_surface_1, window_surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.window_radiation_north_kwh for p in self.periods
        ]

    @property
    def window_surface_radiation_west(self) -> list[list[float]]:
        """Solar radiation values for west-facing window surfaces by calculation period.

        PHPP V10 | Windows | HP23:IA174

        Data structure format:
        [
            period_1: [window_surface_1, window_surface_2, ...],
            period_2: [window_surface_1, window_surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.window_radiation_west_kwh for p in self.periods
        ]

    @property
    def window_surface_radiation_east(self) -> list[list[float]]:
        """Solar radiation values for east-facing window surfaces by calculation period.

        PHPP V10 | Windows | IH23:IS174

        Data structure format:
        [
            period_1: [window_surface_1, window_surface_2, ...],
            period_2: [window_surface_1, window_surface_2, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.window_radiation_east_kwh for p in self.periods
        ]

    @property
    def window_surface_radiation_total(self) -> list[list[float]]:
        """Total effective solar radiation values for all window surfaces by calculation period.

        PHPP V10 | Windows | IZ23:JK174

        Data structure format:
        [
            period_1: [window_surface_1_total, window_surface_2_total, ...],
            period_2: [window_surface_1_total, window_surface_2_total, ...],
            ...
        ]

        Units: ?
        """
        return [
            p.period_solar_radiation.window_total_effective_radiation_kwh
            for p in self.periods
        ]

    def window_surface_period_total_radiation_by_orientation(
        self, _orientation: enums.CardinalOrientation
    ) -> list[float]:
        """Total effective window radiation for each period by specified orientation.

        PHPP V10 | Windows | GF6:GQ10

        Units: ?
        """
        return [
            p.period_solar_radiation.get_window_surface_total_radiation_for_orientation(
                _orientation
            )
            for p in self.periods
        ]

    def window_surface_period_total_radiation_per_m2_by_orientation(
        self, _orientation: enums.CardinalOrientation
    ) -> list[float]:
        """Total effective window radiation per unit glazing area by orientation.

        PHPP V10 | Windows | GF6:GQ10

        Units: ?
        """
        return [
            p.period_solar_radiation.get_window_surface_total_radiation_per_m2_for_orientation(
                _orientation
            )
            for p in self.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Thermal Bridge Gains -----------------------------------------------------------------------------------------

    @property
    def total_thermal_bridge_solar_gain_by_period_kwh(self) -> list[float]:
        """Total solar heat gains through thermal bridge elements by calculation period.

        PHPP V10 | Areas | CP6:DA6 (Thermal Bridge Solar Gains - Wärmebrücken Solargewinne)

        Data structure format:
        [
            period_1_total_thermal_bridge_gains,
            period_2_total_thermal_bridge_gains,
            ...
        ]

        Units: kwh
        """
        return [
            p.period_solar_radiation.thermal_bridge_solar_heat_gain_kwh
            for p in self.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Window Frame Gains -------------------------------------------------------------------------------------------

    @property
    def total_window_frame_solar_gain_by_period_kwh(self) -> list[float]:
        """Total solar heat gains through window frame elements by calculation period.

        PHPP V10 | Areas | CP8:DA8 (Window Frame Solar Gains - Fensterrahmen Solargewinne)

        Data structure format:
        [
            period_1_total_frame_gains,
            period_2_total_frame_gains,
            ...
        ]

        Units: kwh
        """
        return [
            p.period_solar_radiation.window_frame_solar_heat_gain_kwh
            for p in self.periods
        ]

    # ------------------------------------------------------------------------------------------------------------------
    # --- Opaque Element Gains -----------------------------------------------------------------------------------------

    @property
    def total_opaque_element_solar_gain_by_period_kwh(self) -> list[float]:
        """Combined solar heat gains through all opaque building elements.

        PHPP V10 | Areas | CP10:DA10 (Total Opaque Element Gains - Gesamte undurchsichtige Elementgewinne)

        Data structure format:
        [
            period_1_total_opaque_element_gains,
            period_2_total_opaque_element_gains,
            ...
        ]

        Units: kwh
        """
        return [p.solar_heat_gain_opaque_kwh for p in self.periods]

    @property
    def total_annual_cooling_demand_kwh(self) -> float:
        """
        PHPP V10 | Cooling | AG155

        Nutzkälte
        =SUM(T155:AE155)-@INDEX(T155:AE155,$AI$82)+SUM(AK155:AN155)

        Units: kwh
        """
        return (
            sum(p.cooling_demand_kwh for p in self.periods)
            - self.peak_month.warmest_annual_calculation_period.cooling_demand_kwh
            + self.peak_month.peak_total_month.cooling_demand_kwh
        )
