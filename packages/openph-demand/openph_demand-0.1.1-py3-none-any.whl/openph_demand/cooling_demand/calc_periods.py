# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Calculation Period class and with methods for: PHPP | Cooling."""

import math
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

    from openph_demand.solvers import OpPhEnergyDemandSolver

from openph.model.climate import OpPhClimateCalcPeriod
from openph.model.hvac.ventilation_system import (
    OpPhAdditionalVentEquipmentControl,
    OpPhBasicVentEquipmentControl,
)
from openph_solar.calc_periods import OpPhSolarRadiationCalcPeriod

from openph_demand.get_solvers import (
    get_openph_energy_demand_solver,
    get_openph_ground_solver,
)
from openph_demand.ground.results_period import OpPhGroundResultPeriod


@dataclass(frozen=True)
class OpPhCoolingDemandCalcPeriod:
    """A single calculation-period (month) of the PHPP Cooling worksheet."""

    # -- PHPP Model Data
    phpp: "OpPhPHPP"

    # -- Calc Periods
    period_climate: OpPhClimateCalcPeriod
    period_ground: OpPhGroundResultPeriod
    period_solar_radiation: OpPhSolarRadiationCalcPeriod

    # ------------------------------------------------------------------------------------------------------------------
    # -- Basic Properties
    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def length_days(self) -> int:
        """
        PHPP V10 | Cooling | T83:AE83

        = N/A

        Units: Days
        """
        return int(self.period_climate.period_length_hours / 24)

    @property
    def conductance_for_time_constant_W_K(self):
        """
        PHPP V10 | Cooling | R149

        =R112+R110+R114+R115

        Units: W/K
        """

        return (
            self.phpp.areas.envelop_conductance_to_ambient_air_W_K
            + self.energy_demand.cooling_demand.envelop_conductance_to_ground_for_time_constant_W_K
            + self.phpp.areas.envelope_convective_factor_W_K
            + self.phpp.areas.envelope_radiative_factor_W_K
        )

    @property
    def summer_heat_supply_to_ground_W(self) -> float:
        """
        PHPP V10 | Ground | E124:P124

        =SUM(Cooling!T142:T147)/Cooling!T107*1000+IF(Verification!$AD$21=2,'IHG non-res'!$AF$8,IHG!$AA$8)

        Units: W
        """
        return (
            self.total_solar_heat_gain_kwh
            / self.period_climate.period_length_hours
            * 1000
            + self.phpp.ihg.average_annual_internal_heat_gain_W
        )

    @property
    def temperature_air_c(self) -> float:
        """
        PHPP V10 | Cooling | T84:AE84

        =IF(ISNUMBER(Climate!E26),Climate!E26,"")

        Units: C
        """
        return self.period_climate.temperature_air_c

    @property
    def temperature_dewpoint_C(self) -> float:
        """
        PHPP V10 | Cooling | T90:AE90

        =IF(ISNUMBER(Climate!$E$32),Climate!E32,0)

        Units: C
        """
        return self.period_climate.temperature_dewpoint_c

    @property
    def temperature_sky_c(self) -> float:
        """
        PHPP V10 | Cooling | T91:AE91

        =Climate!E33

        Units: C
        """
        return self.period_climate.temperature_sky_c

    @property
    def temperature_ground_c(self) -> float:
        """
        PHPP V10 | Cooling | T92:AE92

        =IF($R$113>0,$E$9-T113*1000/($R$113*T107),Ground!$P$11)

        Units: C
        """
        ground_solver = get_openph_ground_solver(self.phpp)
        if self.phpp.areas.envelop_conductance_to_ground_W_K > 0:
            result = (
                self.phpp.set_points.max_interior_temp_c
                - self.conductive_heat_loss_to_ground_kwh
                * 1000
                / (
                    self.phpp.areas.envelop_conductance_to_ground_W_K
                    * self.period_climate.period_length_hours
                )
            )
            return result
        else:
            return ground_solver.average_ground_surface_temp_C

    # ------------------------------------------------------------------------------------------------------------------
    # -- Balanced Mechanical Ventilation (HRV/ERV)
    """....."""

    @property
    def balanced_mech_vent_kilodegree_hours_to_ground_kKhr(self) -> float:
        """Temperature differential for ground-coupled heat exchanger (Earth-to-Water Heat Exchanger).

        PHPP V10 | Cooling | T111:AE111 (Kilo-degree hours EWU)

        HeizgrSt. EWÜ
        =IF(Moni!AJ9,T$107*($R$108-$R$111)/1000,T$107*(Moni!AK118-$R$111)/1000)

        Units: kKhr
        """
        ground_solver = get_openph_ground_solver(self.phpp)
        return (
            self.period_climate.period_length_hours
            * (
                self.phpp.set_points.max_interior_temp_c
                - ground_solver.average_ground_surface_temp_C
            )
            / 1000
        )

    @property
    def balanced_mech_vent_supply_air_temperature_without_heat_recovery_C(
        self,
    ) -> float:
        """Supply air temperature without heat recovery for this calculation period.

        PHPP V10 | Cooling | T116:AE116

        T_Zuluft ohne WRG
        =$D$43*$R$111+(1-$D$43)*T84
        D43=Ventilation!Q34

        Units: C
        """
        ground_solver = get_openph_ground_solver(self.phpp)
        return (
            self.phpp.hvac.ventilation_system.effective_subsoil_heat_recovery
            * ground_solver.average_ground_surface_temp_C
            + (1 - self.phpp.hvac.ventilation_system.effective_subsoil_heat_recovery)
            * self.period_climate.temperature_air_c
        )

    @property
    def balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C(
        self,
    ) -> float:
        """Dew point temperature of supply air without heat recovery.

        PHPP V10 | Cooling | T117:AE117

        Taupunkttemp Zuluft ohne WRG
        =MIN(T90,T116)

        Units: C
        """
        return min(
            self.period_climate.temperature_dewpoint_c,
            self.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C,
        )

    @property
    def balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa(
        self,
    ) -> float:
        """Water vapor pressure of supply air without heat recovery.

        PHPP V10 | Cooling | T118:AE118

        Wasserdampfdruck Zuluft ohne WRG Pa
        =611*EXP(0.000191275+0.07258*T117-0.0002939*T117^2+0.0000009841*T117^3-0.00000000192*T117^4)

        Units: Pa
        """
        return 611 * math.exp(
            0.000191275
            + 0.07258
            * self.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C
            - 0.0002939
            * self.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C
            ** 2
            + 0.0000009841
            * self.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C
            ** 3
            - 0.00000000192
            * self.balanced_mech_vent_supply_air_dew_point_temperature_without_heat_recovery_C
            ** 4
        )

    @property
    def balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg(
        self,
    ) -> float:
        """Absolute humidity of supply air without heat recovery.

        PHPP V10 | Cooling | T119:AE119 (abs. Feuchte Zuluft ohne WRG kg/kg)

        abs. Feuchte Zuluft ohne WRG kg/kg
        =0.6222*T118/(101300-T118)

        Units: kg/kg
        """
        return (
            0.622
            * self.balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa
            / (
                101_300
                - self.balanced_mech_vent_supply_air_water_vapor_pressure_without_heat_recovery_Pa
            )
        )

    @property
    def balanced_mech_vent_supply_air_enthalpy_without_heat_recovery_kJ_kG(
        self,
    ) -> float:
        """Enthalpy of supply air without heat recovery.

        PHPP V10 | Cooling | T120:AE120

        Enthalpie Zuluft ohne WRG kJ/kg tr. Luft
        =1.01*T116 + T119*(2501+1.86*T116)

        Units: kJ/kg
        """
        return (
            1.01
            * self.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
            + self.balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg
            * (
                2501
                + 1.86
                * self.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
            )
        )

    @property
    def balanced_mech_vent_supply_air_temperature_with_heat_recovery_C(self) -> float:
        """Supply air temperature with heat recovery for this calculation period.

        PHPP V10 | Cooling | T121:AE121

        T_Zuluft mit WRG (bei Soll-Innenbedingungen) °C
        =T116+$D$41*($E$9-T116)
        D41=IF(ISNUMBER(Ventilation!L32),IF(COUNTIF(Cooling!T84:AE84,">"&Cooling!T8)>=2,Ventilation!N34,Ventilation!L32),0)

        Units: C
        """
        return (
            self.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
            + self.phpp.hvac.ventilation_system.effective_heat_recovery
            * (
                self.phpp.set_points.max_interior_temp_c
                - self.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
            )
        )

    @property
    def balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg(
        self,
    ) -> float:
        """Absolute humidity of supply air with heat recovery at target indoor conditions.

        PHPP V10 | Cooling | T122:AE122

        abs. Feuchte Zuluft mit WRG (bei Soll-Innenbedingungen) kg/kg
        =T119+$D$42*($E$10/1000-T119)
        D42==IF(ISNUMBER(Ventilation!M32),Ventilation!M32,0)

        Units: kg/kg
        """
        return (
            self.balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg
            + self.phpp.hvac.ventilation_system.effective_moisture_recovery
            * (
                self.phpp.set_points.max_absolute_humidity
                / (
                    1000
                    - self.balanced_mech_vent_supply_air_absolute_humidity_without_heat_recovery_kg_kg
                )
            )
        )

    @property
    def balanced_mech_vent_supply_air_enthalpy_with_heat_recovery_kJ_kg(self) -> float:
        """Enthalpy of supply air with heat recovery.

        PHPP V10 | Cooling | T123:AE123

        Enthalpie Zuluft mit WRG
        =1.01*T121 + T122*(2501+1.86*T121)

        Units: kJ/kg
        """
        return (
            1.01 * self.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C
            + self.balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg
            * (
                2501
                + 1.86
                * self.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C
            )
        )

    @property
    def balanced_mech_vent_is_supply_air_at_target_indoor_conditions(self) -> bool:
        """Determines if supply air meets target indoor conditions after heat recovery.

        PHPP V10 | Cooling | T124:AE124

        WRG/FRG ein?  (bei Soll-Innenbedingungen)
        =IF($O$35="x",FALSE,IF($O$36="x",T121<T116,IF($O$37="x",T123<T120,TRUE)))

        Units: Boolean
        """
        if (
            self.phpp.hvac.ventilation_system.summer.basic_vent_equipment_control
            is OpPhBasicVentEquipmentControl.NO_CONTROL
        ):
            return False
        elif (
            self.phpp.hvac.ventilation_system.summer.basic_vent_equipment_control
            is OpPhBasicVentEquipmentControl.TEMPERATURE_CONTROLLED
        ):
            return (
                self.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C
                < self.balanced_mech_vent_supply_air_temperature_without_heat_recovery_C
            )
        elif (
            self.phpp.hvac.ventilation_system.summer.basic_vent_equipment_control
            is OpPhBasicVentEquipmentControl.ENTHALPY_CONTROLLED
        ):
            return (
                self.balanced_mech_vent_supply_air_enthalpy_with_heat_recovery_kJ_kg
                < self.balanced_mech_vent_supply_air_enthalpy_without_heat_recovery_kJ_kG
            )
        else:
            return True

    @property
    def balanced_mech_vent_conductance_to_air_W_K(self) -> float:
        """Thermal conductance of ventilation air flow for cooling calculations.

        PHPP V10 | Cooling | T125:AE125

        Leitwert Lüftung außen
        =IF(T124,$D$34,$D$35)+$D$39

        Units: W/K
        """
        if self.balanced_mech_vent_is_supply_air_at_target_indoor_conditions:
            return (
                self.phpp.hvac.ventilation_system.summer.ventilation_conductance_air_with_heat_recovery_w_k
                + self.phpp.hvac.ventilation_system.summer.ventilation_conductance_other_w_k
            )
        else:
            return (
                self.phpp.hvac.ventilation_system.summer.ventilation_conductance_air_without_heat_recovery_w_k
                + self.phpp.hvac.ventilation_system.summer.ventilation_conductance_other_w_k
            )

    @property
    def balanced_mech_vent_conductance_to_soil_W_K(self) -> float:
        """Thermal conductance of ventilation system ground coupling.

        PHPP V10 | Cooling | T126:AE126

        Leitwert Lüftung Erdreich
        =IF(T124,$D$36,$D$37)

        Units: W/K
        """
        if self.balanced_mech_vent_is_supply_air_at_target_indoor_conditions:
            return (
                self.phpp.hvac.ventilation_system.summer.ventilation_conductance_ground_with_heat_recovery_w_k
            )
        else:
            return (
                self.phpp.hvac.ventilation_system.summer.ventilation_conductance_ground_without_heat_recovery_w_k
            )

    @property
    def balanced_mech_vent_supply_air_mass_flow_kg_hour(self) -> float:
        """Mass flow rate of mechanical ventilation air for this calculation period.

        PHPP V10 | Cooling | T127:AE127

        Massenstrom Zuluft kg/h
        =$J$37*$O$9*1.18

        Units: kg/h
        """
        return (
            self.phpp.hvac.ventilation_system.summer.air_change_rate_basic_mech
            * self.phpp.rooms.total_ventilated_volume_m3
            * 1.18
        )

    @property
    def balanced_mech_vent_heat_loss_to_ambient_air_kwh(self) -> float:
        """Mechanical ventilation heat removal through ambient air exchange.

        PHPP V10 | Cooling | T129:AE129

        Lüftungsverlust außen
        =T125*T108

        Units: kwh
        """
        return (
            self.period_climate.cooling.kilo_degree_hours_ambient_air
            * self.balanced_mech_vent_conductance_to_air_W_K
        )

    @property
    def balanced_mech_vent_heat_loss_to_ground_kwh(self) -> float:
        """Ground-coupled heat exchanger cooling effect for mechanical ventilation.

        PHPP V10 | Cooling | T130:AE130

        Lüftungsverlust EWÜ
        =T126*T111

        Units: kwh
        """
        return (
            self.balanced_mech_vent_conductance_to_soil_W_K
            * self.balanced_mech_vent_kilodegree_hours_to_ground_kKhr
        )

    @property
    def balanced_mech_vent_total_heat_loss_kwh(self) -> float:
        """Total mechanical ventilation cooling extraction."""
        return (
            self.balanced_mech_vent_heat_loss_to_ambient_air_kwh
            + self.balanced_mech_vent_heat_loss_to_ground_kwh
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Exhaust Mechanical Ventilation
    """....."""

    @property
    def exhaust_mech_vent_time_constant(self) -> float:
        """Time constant for summer ventilation operation during this period.

        PHPP V10 | Cooling | T133:AE133

        t_end Sommerlüftung konst
        =IF($O$41="x",
            IF($E$10*0.001>T132,6,-6),
            IF($E$9>=T84+$J$42+$J$34/2,6,IF($E$9<=T84+$J$42-$J$34/2,-6,12/PI()*ASIN(($E$9-T84-$J$42)/$J$34*2)))
        )

        Units: hours
        """
        if (
            self.phpp.hvac.ventilation_system.summer.additional_vent_equipment_control
            is OpPhAdditionalVentEquipmentControl.HUMIDITY_CONTROLLED
        ):
            if (
                self.phpp.set_points.max_absolute_humidity * 0.001
                > self.period_climate.outdoor_air_absolute_humidity_kg_kg
            ):
                return 6
            else:
                return -6
        else:
            if (
                self.phpp.set_points.max_interior_temp_c
                >= self.period_climate.temperature_air_c
                + self.phpp.hvac.ventilation_system.summer.temperature_increase
                + self.phpp.climate.summer_daily_temperature_fluctuation / 2
            ):
                return 6
            elif (
                self.phpp.set_points.max_interior_temp_c
                <= self.period_climate.temperature_air_c
                + self.phpp.hvac.ventilation_system.summer.temperature_increase
                - self.phpp.climate.summer_daily_temperature_fluctuation / 2
            ):
                return -6
            else:
                return (
                    12
                    / math.pi
                    * math.asin(
                        (
                            self.phpp.set_points.max_interior_temp_c
                            - self.period_climate.temperature_air_c
                            - self.phpp.hvac.ventilation_system.summer.temperature_increase
                        )
                        / self.phpp.climate.summer_daily_temperature_fluctuation
                        * 2
                    )
                )

    @property
    def exhaust_mech_vent_average_temperature_C(self) -> float:
        """Average temperature for summer ventilation during this period.

        PHPP V10 | Cooling | T134:AE134

        Atemp Sommlüft konst
        =IF(T133 > -5.99,T84-6*$J$34/(PI()*(T133+6))*COS(PI()*T133/12),T84-$J$34/2)+$J$42

        Units: °C
        """
        if self.exhaust_mech_vent_time_constant > -5.99:
            return (
                self.period_climate.temperature_air_c
                - 6
                * self.phpp.climate.summer_daily_temperature_fluctuation
                / (math.pi * (self.exhaust_mech_vent_time_constant + 6))
                * math.cos(math.pi * self.exhaust_mech_vent_time_constant / 12)
            ) + self.phpp.hvac.ventilation_system.summer.temperature_increase
        else:
            return (
                self.period_climate.temperature_air_c
                - self.phpp.climate.summer_daily_temperature_fluctuation / 2
            ) + self.phpp.hvac.ventilation_system.summer.temperature_increase

    @property
    def exhaust_mech_vent_thermal_conductance_W_K(self) -> float:
        """Thermal conductance for summer ventilation during this period.

        PHPP V10 | Cooling | T135:AE135

        Leitwert Sommlüft konst
        =IF($J$40>0,1/(1/($J$36*$J$40*$O$9)+1/(1.5*4.5*$O$8)) * (T133+6)/12,0)

        Units: W/K
        """
        if (
            self.phpp.hvac.ventilation_system.summer.additional_extract_system_nighttime_ach
            > 0.0
        ):
            return (
                1
                / (
                    1
                    / (
                        self.phpp.constants.c_air
                        * self.phpp.hvac.ventilation_system.summer.additional_extract_system_nighttime_ach
                        * self.phpp.rooms.total_ventilated_volume_m3
                    )
                    + 1 / (1.5 * 4.5 * self.phpp.rooms.total_weighted_floor_area_m2)
                )
                * (self.exhaust_mech_vent_time_constant + 6)
                / 12
            )
        else:
            return 0.0

    @property
    def exhaust_mech_vent_total_heat_loss_kwh(self) -> float:
        """Additional summer ventilation cooling extraction (night purge ventilation).

        PHPP V10 | Cooling | T136:AE136

        Verlust Sommlüft konst
        =IF(Moni!AJ9,T135*($R$108-T134)*T107/1000,T135*(Moni!AK118-T134)*T107/1000)

        Units: kwh
        """
        return (
            self.exhaust_mech_vent_thermal_conductance_W_K
            * (
                self.phpp.set_points.max_interior_temp_c
                - self.exhaust_mech_vent_average_temperature_C
            )
            * self.period_climate.period_length_hours
            / 1000
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Envelope Ventilation (Windows and Air-Leakage)
    """Window and air-infiltration ventilation air calculations for a single calculation period.
    PHPP V10 | Cooling | Rows 128-141 (passive ventilation calculations).
    """

    @property
    def envelope_vent_air_mass_flow_rate_kg_hour(self) -> float:
        """Mass flow rate of passive ventilation air for this calculation period.

        PHPP V10 | Cooling | T128:AE128

        Massenstrom Zuluft kg/h
        =$J$37*$O$9*1.18

        Units: kg/h
        """
        return (
            self.phpp.hvac.ventilation_system.summer.ventilation_ach_other
            * self.phpp.rooms.total_ventilated_volume_m3
            * 1.18
        )

    @property
    def envelope_vent_air_average_temperature_C(self) -> float:
        """Average temperature for natural window ventilation during this period.

        PHPP V10 | Cooling | T137:AE137
        Atemp Fenstlüft
        =T84-2/PI()*$J$34/2

        Units: C
        """
        return (
            self.period_climate.temperature_air_c
            - 2 / math.pi * self.phpp.climate.summer_daily_temperature_fluctuation / 2
        )

    @property
    def envelope_vent_air_volume_flow_rate_m3_hour(self) -> float:
        """Volume flow rate for natural window ventilation during this period.

        PHPP V10 | Cooling | T138:AE138

        Volumenstrom Fenstlüft m³/h
        =$J$39*$O$9*SQRT(ABS($E$9-T137))

        Units: m³/h
        """
        return (
            self.phpp.hvac.ventilation_system.summer.window_nighttime_ach
            * self.phpp.rooms.total_ventilated_volume_m3
            * math.sqrt(
                abs(
                    self.phpp.set_points.max_interior_temp_c
                    - self.envelope_vent_air_average_temperature_C
                )
            )
        )

    @property
    def envelope_vent_window_achievable_thermal_conductance_W_K(self) -> float:
        """Achievable thermal conductance for natural window ventilation during this period.

        PHPP V10 | Cooling | T139:AE139

        erreichbarer Leitwert Fenstlüft W/K
        =IF(T138>0,1/(1/($J$36*T138)+1/(1.5*4.5*$O$8))/2,0)

        Units: W/K
        """
        if self.envelope_vent_air_volume_flow_rate_m3_hour > 0:
            return (
                1
                / (
                    1
                    / (
                        self.phpp.constants.c_air
                        * self.envelope_vent_air_volume_flow_rate_m3_hour
                    )
                    + 1 / (1.5 * 4.5 * self.phpp.rooms.total_weighted_floor_area_m2)
                )
                / 2
            )
        else:
            return 0.0

    @property
    def envelope_vent_window_effective_thermal_conductance_W_K(self) -> float:
        """Effective thermal conductance for natural window ventilation considering environmental conditions.

        PHPP V10 | Cooling | T140:AE140

        Leitwert Fenstlüft W/K
        =IF(AND(T137<$E$9,T132*1000<$E$10),T139,0)

        Units: W/K
        """
        if (
            self.envelope_vent_air_average_temperature_C
            < self.phpp.set_points.max_interior_temp_c
            and self.period_climate.outdoor_air_absolute_humidity_kg_kg * 1000
            < self.phpp.set_points.max_absolute_humidity
        ):
            return self.envelope_vent_window_achievable_thermal_conductance_W_K
        else:
            return 0.0

    @property
    def envelope_vent_total_heat_loss_kwh(self) -> float:
        """Manual and incidental natural window ventilation heat removal.

        PHPP V10 | Cooling | T141:AE141

        Verlust Fenstlüft kwh
        =IF(Moni!AJ9,T140*($R$108-T137)*T107/1000,T140*(Moni!AK118-T137)*T107/1000)

        Units: kwh
        """
        return (
            self.envelope_vent_window_effective_thermal_conductance_W_K
            * (
                self.phpp.set_points.max_interior_temp_c
                - self.envelope_vent_air_average_temperature_C
            )
            * self.period_climate.period_length_hours
            / 1000
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Losses

    @property
    def kilo_degree_hours_to_ground_kK_hr(self) -> float:
        """The degree-hours to the ground.

        PHPP V10 | Cooling | T110:AE110

        HeizgrSt. Grund
        =IF($R$113>0,T113/$R$113,0)

        Units: K⋅h/1000
        """
        try:
            return (
                self.conductive_heat_loss_to_ground_kwh
                / self.phpp.areas.envelop_conductance_to_ground_W_K
            )
        except ZeroDivisionError:
            return 0.0

    @property
    def conductive_heat_loss_to_ambient_air_kwh(self) -> float:
        """The transmission heat losses through building envelope to ambient air.

        PHPP V10 | Cooling | T112:AE112

        Transmissionsverluste außen
        =$R112*T108

        Units: kwh
        """
        return (
            self.period_climate.cooling.kilo_degree_hours_ambient_air
            * self.phpp.areas.envelop_conductance_to_ambient_air_W_K
        )

    @property
    def conductive_heat_loss_to_ground_kwh(self) -> float:
        """The transmission heat losses through building envelope to ground.

        PHPP V10 | Cooling | T113:AE113

        Verluste Grund
        =Ground!E112*T107/1000

        Units: kwh
        """
        return (
            self.period_ground.total_heat_flow_to_ground_w
            * self.period_climate.period_length_hours
        ) / 1_000

    @property
    def convective_heat_loss_to_ambient_kwh(self) -> float:
        """The convective heat losses.

        PHPP V10 | Cooling | T114:AE114

        zus. Verlust außen konvektiv
        =$R114*T108

        Units: kwh
        """
        return (
            self.period_climate.cooling.kilo_degree_hours_ambient_air
            * self.phpp.areas.envelope_convective_factor_W_K
        )

    @property
    def radiative_heat_loss_to_sky_kwh(self) -> float:
        """The radiative heat losses.

        PHPP V10 | Cooling | T115:AE115

        zus. Verlust außen radiativ
        =$R115*T109

        Units: kwh
        """
        return (
            self.period_climate.cooling.kilo_degree_hours_sky
            * self.phpp.areas.envelope_radiative_factor_W_K
        )

    @property
    def total_heat_loss_kwh(self) -> float:
        """The total heat losses from all building systems and envelope components.

        PHPP V10 | Cooling | T149:AE149

        Summe Verl
        =T112+T113+T114+T115+T129+T130+T136+T141

        Units: kwh
        """
        return (
            self.conductive_heat_loss_to_ambient_air_kwh
            + self.conductive_heat_loss_to_ground_kwh
            + self.convective_heat_loss_to_ambient_kwh
            + self.radiative_heat_loss_to_sky_kwh
            + self.balanced_mech_vent_total_heat_loss_kwh
            + self.exhaust_mech_vent_total_heat_loss_kwh
            + self.envelope_vent_total_heat_loss_kwh
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Gains

    @property
    def solar_heat_gain_north_windows_kwh(self) -> float:
        """Solar heat gain through north-facing windows for this calculation period.

        PHPP V10 | Cooling | T142:AE142

        Solar Nord
        =$R142*T102

        Units: kwh
        """
        return (
            self.period_climate.radiation_north_kwh_m2
            * self.phpp.areas.windows.north.summer_eff_solar_gain_area_m2
        )

    @property
    def solar_heat_gain_east_windows_kwh(self) -> float:
        """Solar heat gain through east-facing windows for this calculation period.

        PHPP V10 | Cooling | T143:AE143

        Solar Ost
        =$R143*T103

        Units: kwh
        """
        return (
            self.period_climate.radiation_east_kwh_m2
            * self.phpp.areas.windows.east.summer_eff_solar_gain_area_m2
        )

    @property
    def solar_heat_gain_south_windows_kwh(self) -> float:
        """Solar heat gain through south-facing windows for this calculation period.

        PHPP V10 | Cooling | T144:AE144

        Solar Süd
        =$R144*T104

        Units: kwh
        """
        return (
            self.period_climate.radiation_south_kwh_m2
            * self.phpp.areas.windows.south.summer_eff_solar_gain_area_m2
        )

    @property
    def solar_heat_gain_west_windows_kwh(self) -> float:
        """Solar heat gain through west-facing windows for this calculation period.

        PHPP V10 | Cooling | T145:AE145

        Solar West
        =$R145*T105

        Units: kwh
        """
        return (
            self.period_climate.radiation_west_kwh_m2
            * self.phpp.areas.windows.west.summer_eff_solar_gain_area_m2
        )

    @property
    def solar_heat_gain_horizontal_windows_kwh(self) -> float:
        """Solar heat gain through horizontal windows (skylights) for this calculation period.

        PHPP V10 | Cooling | T146:AE146

        Solar Hori
        =$R146*T106

        Units: kwh
        """
        return (
            self.period_climate.radiation_horizontal_kwh_m2
            * self.phpp.areas.windows.horizontal.summer_eff_solar_gain_area_m2
        )

    @property
    def solar_heat_gain_opaque_kwh(self) -> float:
        """The solar heat gains through opaque building envelope elements.

        PHPP V10 | Cooling | T147:AE147

        Solar opak
        =Areas!CP10

        Units: kwh
        """
        return (
            self.period_solar_radiation.opaque_surface_solar_heat_gain_kwh
            + self.period_solar_radiation.thermal_bridge_solar_heat_gain_kwh
            + self.period_solar_radiation.window_frame_solar_heat_gain_kwh
        )

    @property
    def total_solar_heat_gain_kwh(self) -> float:
        """The total solar heat gains from solar.

        PHPP V10 | Cooling | T1142:AE147

        Units: kwh
        """
        return (
            self.solar_heat_gain_north_windows_kwh
            + self.solar_heat_gain_east_windows_kwh
            + self.solar_heat_gain_south_windows_kwh
            + self.solar_heat_gain_west_windows_kwh
            + self.solar_heat_gain_horizontal_windows_kwh
            + self.solar_heat_gain_opaque_kwh
        )

    @property
    def internal_heat_gain_kwh(self) -> float:
        """The internal heat gains from occupants, equipment, and lighting.

        PHPP V10 | Cooling | T148:AE148

        Interne WQ
        =IF(Moni!AJ9,$R148*T107/1000,Moni!AK142*Cooling!$O$8*T107/1000)

        Units: kwh
        """
        return (
            self.phpp.ihg.average_annual_internal_heat_gain_W
            * self.period_climate.period_length_hours
        ) / 1_000

    @property
    def total_heat_gain_kwh(self) -> float:
        """The total heat gains from internal and solar.

        PHPP V10 | Cooling | T150:AE150

        Summe Ang
        =SUM(T142:T148)

        Units: kwh
        """
        return self.total_solar_heat_gain_kwh + self.internal_heat_gain_kwh

    # ------------------------------------------------------------------------------------------------------------------
    # --- Energy Balance Calculations

    @property
    def time_constant(self) -> float:
        """The thermal-time-constant.

        PHPP V10 | Cooling | T151:AE151

        Zeitkonstante h
        =IF( $R$149+T125+T126=0, 0, $R$151/($R$149+T125+T126))

        Units: hours
        """
        if (
            self.conductance_for_time_constant_W_K
            + self.balanced_mech_vent_conductance_to_air_W_K
            + self.balanced_mech_vent_conductance_to_soil_W_K
            == 0
        ):
            return 0.0
        else:
            try:
                return self.phpp.areas.heat_capacity_Wh_K / (
                    self.conductance_for_time_constant_W_K
                    + self.balanced_mech_vent_conductance_to_air_W_K
                    + self.balanced_mech_vent_conductance_to_soil_W_K
                )
            except ZeroDivisionError:
                return 0.0

    @property
    def monthly_procedure_factor(self) -> float:
        """The heat-gain-utilization-factor.

        PHPP V10 | Cooling | T152:AE152

        a_Monatsverfahren
        =1+T151/16

        Units: Dimensionless factor (-)
        """
        return 1 + self.time_constant / 16

    @property
    def loss_to_gain_ratio(self) -> float:
        """The ratio of building heat losses to heat gains.

        PHPP V10 | Cooling | T153:AE153

        Verl/Ang
        =IF(ABS(T150)<0.01,0,T149/T150)

        Units: Dimensionless ratio (-)
        """
        try:
            return self.total_heat_loss_kwh / self.total_heat_gain_kwh
        except ZeroDivisionError:
            return 0.0

    @property
    def utilization_factor(self) -> float:
        """The heat-loss-efficiency-factor.

        PHPP V10 | Cooling | T154:AE154

        Nutzungsgrad Wärmeverluste
        =IF(T153>0,IF(T153=1,T152/(T152+1),(1-T153^T152)/(1-T153^(T152+1))),1)

        Units: Dimensionless efficiency factor (-)
        """
        if self.loss_to_gain_ratio > 0:
            if self.loss_to_gain_ratio == 1:
                efficiency = self.monthly_procedure_factor / (
                    self.monthly_procedure_factor + 1
                )
            else:
                try:
                    efficiency = (
                        1 - self.loss_to_gain_ratio**self.monthly_procedure_factor
                    ) / (
                        1
                        - self.loss_to_gain_ratio ** (self.monthly_procedure_factor + 1)
                    )
                except (ZeroDivisionError, OverflowError):
                    efficiency = 0.0
        else:
            efficiency = 1.0

        return max(0.0, min(1.0, efficiency))  # Clamp between 0 and 1

    @property
    def cooling_demand_kwh(self) -> float:
        """The useful cooling demand.

        PHPP V10 | Cooling | T155:AE155

        Nutzkälte
        =MAX(0,T150-T154*T149)

        Units: kwh per month
        """
        cooling_demand = self.total_heat_gain_kwh - (
            self.utilization_factor * self.total_heat_loss_kwh
        )
        return max(0.0, cooling_demand)  # Cooling demand cannot be negative

    @property
    def in_cooling_period(self) -> bool:
        """Boolean indicator for periods requiring active cooling.

        PHPP V10 | Cooling | T156:AE156

        Kühlperiode?
        =AND(T82<>$AI$82,T155>$AG$155*0.001)

        Units: Boolean per period
        """
        # threshold=1 Wh to avoid floating point issues

        return (
            self.cooling_demand_kwh
            > self.energy_demand.cooling_demand.total_annual_cooling_demand_kwh * 0.001
        )
