# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Cooling Demand Warmest Month Nonsense."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

    from openph_demand.solvers import OpPhEnergyDemandSolver

from openph.model.enums import CardinalOrientation
from openph_solar.calc_periods import OpPhSolarRadiationCalcPeriod

from openph_demand.cooling_demand.calc_periods import OpPhCoolingDemandCalcPeriod
from openph_demand.cooling_demand.peak_month_climate_data import (
    EntireMonthClimateData,
    FourDayPeriodClimateData,
    RestOfMonthClimateData,
    SingleDayPeriodClimateData,
    TwelveDayClimateData,
)
from openph_demand.get_solvers import (
    get_openph_energy_demand_solver,
    get_openph_ground_solver,
)
from openph_demand.ground.results_period import OpPhGroundResultPeriod

# ----------------------------------------------------------------------------------------------------------------------
# -- Calculation Period Results [AK102:AO156]


class OpPhCoolingDemandPeakCalcPeriod(OpPhCoolingDemandCalcPeriod):
    """One of the 'typical' period solvers (single, 4-day, 12-day, 14-day)."""

    phpp: "OpPhPHPP"
    period_climate: (
        SingleDayPeriodClimateData
        | FourDayPeriodClimateData
        | TwelveDayClimateData
        | RestOfMonthClimateData
    )

    @property
    def kilo_degree_hours_ambient_air_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AK108:AN108

        =IF(Moni!$AJ9,AK$107*($R108-AK84)/1000,AK$107*(@INDEX(Moni!$AK$118:$AK$129,$AI$82)-$AI$84)/1000)

        Units: kKhr/period
        """
        return (
            self.period_climate.period_length_hours
            * (
                self.phpp.set_points.max_interior_temp_c
                - self.period_climate.temperature_air_c
            )
            / 1000
        )

    @property
    def kilo_degree_hours_to_sky_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AK109:AN109

        =AK$107*($R108-AK91)/1000

        Units: kKhr/period
        """
        return (
            self.period_climate.period_length_hours
            * (
                self.phpp.set_points.max_interior_temp_c
                - self.period_climate.temperature_sky_c
            )
            / 1000
        )

    @property
    def kilo_degree_hours_to_ground_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AK110:AN110

        =IF($R$113>0,AN113/$R$113,0)

        Units: kKhr/period
        """
        try:
            return (
                self.conductive_heat_loss_to_ground_kwh
                / self.energy_demand.cooling_demand.envelop_conductance_to_ground_W_K
            )
        except ZeroDivisionError:
            return 0.0

    @property
    def kilo_degree_hours_to_EWU_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AK111:AN111

        =AN$107*($R108-Ground!$P$11)/1000

        Units: kKhr/period
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
    def conductive_heat_loss_to_ground_kwh(self) -> float:
        """
        PHPP V10 | Cooling | AK113:AO113

        =$AI$113*AK83/$AI$83

        Units: kwh
        """

        return (
            self.energy_demand.cooling_demand.peak_month.heat_losses_to_ground_from_annual_calc
            * self.period_climate.period_length_days
            / self.energy_demand.cooling_demand.peak_month.length_days
        )

    @property
    def solar_heat_gain_opaque_kwh(self) -> float:
        """The solar heat gains through opaque building envelope elements.

        PHPP V10 | Cooling | AK147:AN147

        Solar opak
        =MIN(AK93,$AI147*$AL$98/$AI$83)*AK$83

        Units: kwh
        """
        a = self.period_climate.radiation_opaque_kwh_m2_day

        b = (
            self.energy_demand.cooling_demand.peak_month.radiation_opaque
            * self.energy_demand.cooling_demand.peak_month.solarzuschlagsfaktor_max
            / self.energy_demand.cooling_demand.peak_month.length_days
        )
        return min(a, b) * self.period_climate.period_length_days

    """Note: Calculation methods are the same as the base-class OpPhCoolingDemandCalcPeriod."""


class OpPhCoolingDemandPeakMonthCalcPeriod(OpPhCoolingDemandCalcPeriod):
    """The 'total' calculation result values for the Peak Month."""

    phpp: "OpPhPHPP"
    period_climate: EntireMonthClimateData

    @property
    def kilo_degree_hours_ambient_air_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AO108

        HeizgrSt.Außen
        =SUM(AK108:AN108)

        Units: kKhr/period
        """

        return sum(
            p.kilo_degree_hours_ambient_air_kK_hr
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def kilo_degree_hours_to_sky_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AO109

        HeizgrSt. Himmel
        =SUM(AK109:AN109)

        Units: kKhr/period
        """

        return sum(
            p.kilo_degree_hours_to_sky_kK_hr
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def kilo_degree_hours_to_ground_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AO110

        HeizgrSt. Grund
        =SUM(AK110:AN110)

        Units: kKhr/period
        """

        return sum(
            p.kilo_degree_hours_to_ground_kK_hr
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def kilo_degree_hours_to_EWU_kK_hr(self) -> float:
        """
        PHPP V10 | Cooling | AO111

        HeizgrSt. EWÜ
        =SUM(AK111:AN111)

        Units: kKhr/period
        """

        return sum(
            p.kilo_degree_hours_to_EWU_kK_hr
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Heat Loss Totals

    @property
    def conductive_heat_loss_to_ambient_air_kwh(self) -> float:
        """The transmission heat losses through building envelope to ambient air.

        PHPP V10 | Cooling | AO112

        Transmissionsverluste außen
        =SUM(AK112:AN112)

        Units: kwh
        """

        return sum(
            p.conductive_heat_loss_to_ambient_air_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def conductive_heat_loss_to_ground_kwh(self) -> float:
        """The transmission heat losses through building envelope to ground.

        PHPP V10 | Cooling | AO113

        Verluste Grund
        =SUM(AK113:AN113)

        Units: kwh
        """

        return sum(
            p.conductive_heat_loss_to_ground_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def convective_heat_loss_to_ambient_kwh(self) -> float:
        """The convective heat losses.

        PHPP V10 | Cooling | AO114

        zus. Verlust außen konvektiv
        =SUM(AK114:AN114)

        Units: kwh
        """

        return sum(
            p.convective_heat_loss_to_ambient_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def radiative_heat_loss_to_sky_kwh(self) -> float:
        """The radiative heat losses.

        PHPP V10 | Cooling | AO115

        zus. Verlust außen radiativ
        =SUM(AK115:AN115)

        Units: kwh
        """

        return sum(
            p.radiative_heat_loss_to_sky_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Balanced Mechanical Ventilation (HRV/ERV)

    @property
    def balanced_mech_vent_supply_air_temperature_with_heat_recovery_C(self) -> float:
        """Supply air temperature with heat recovery for this calculation period.

        PHPP V10 | Cooling | AO121

        T_Zuluft mit WRG (bei Soll-Innenbedingungen) °C
        =SUMPRODUCT(AK121:AN121,$AK$107:$AN$107)/$AO$107

        Units: C
        """

        sum_product_result = sum(
            p.balanced_mech_vent_supply_air_temperature_with_heat_recovery_C
            * p.period_climate.period_length_hours
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )
        return sum_product_result / self.period_climate.period_length_hours

    @property
    def balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg(
        self,
    ) -> float:
        """Absolute humidity of supply air with heat recovery at target indoor conditions.

        PHPP V10 | Cooling | AO122

        abs. Feuchte Zuluft mit WRG (bei Soll-Innenbedingungen) kg/kg
        =SUMPRODUCT(AK122:AN122,$AK$107:$AN$107)/$AO$107

        Units: kg/kg
        """

        sum_product_result = sum(
            p.balanced_mech_vent_supply_air_absolute_humidity_with_heat_recovery_kg_kg
            * p.period_climate.period_length_hours
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )
        return sum_product_result / self.period_climate.period_length_hours

    @property
    def balanced_mech_vent_conductance_to_air_W_K(self) -> float:
        """Thermal conductance of ventilation air flow for cooling calculations.

        PHPP V10 | Cooling | AO125

        Leitwert Lüftung außen
        =SUMPRODUCT(AK125:AN125,$AK$107:$AN$107)/$AO$107

        Units: W/K
        """

        sum_product_result = sum(
            p.balanced_mech_vent_conductance_to_air_W_K
            * p.period_climate.period_length_hours
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )
        return sum_product_result / self.period_climate.period_length_hours

    @property
    def balanced_mech_vent_conductance_to_soil_W_K(self) -> float:
        """Thermal conductance of ventilation system ground coupling.

        PHPP V10 | Cooling | AO126

        Leitwert Lüftung Erdreich
        =SUMPRODUCT(AK126:AN126,$AK$107:$AN$107)/$AO$107

        Units: W/K
        """

        sum_product_result = sum(
            p.balanced_mech_vent_conductance_to_soil_W_K
            * p.period_climate.period_length_hours
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )
        return sum_product_result / self.period_climate.period_length_hours

    @property
    def balanced_mech_vent_supply_air_mass_flow_kg_hour(self) -> float:
        """Mass flow rate of mechanical ventilation air for this calculation period.

        PHPP V10 | Cooling | AO127

        Massenstrom Zuluft kg/h
        =SUMPRODUCT(AK127:AN127,$AK$107:$AN$107)/$AO$107

        Units: kg/h
        """

        sum_product_result = sum(
            p.balanced_mech_vent_supply_air_mass_flow_kg_hour
            * p.period_climate.period_length_hours
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )
        return sum_product_result / self.period_climate.period_length_hours

    @property
    def balanced_mech_vent_heat_loss_to_ambient_air_kwh(self) -> float:
        """Mechanical ventilation heat removal through ambient air exchange.

        PHPP V10 | Cooling | T129:AE129

        Lüftungsverlust außen
        =SUM(AK129:AN129)

        Units: kwh
        """

        return sum(
            p.balanced_mech_vent_heat_loss_to_ambient_air_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def balanced_mech_vent_heat_loss_to_ground_kwh(self) -> float:
        """Ground-coupled heat exchanger cooling effect for mechanical ventilation.

        PHPP V10 | Cooling | AO130

        Lüftungsverlust EWÜ
        =SUM(AK130:AN130)

        Units: kwh
        """

        return sum(
            p.balanced_mech_vent_heat_loss_to_ground_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Exhaust Mechanical Ventilation

    @property
    def exhaust_mech_vent_total_heat_loss_kwh(self) -> float:
        """Additional summer ventilation cooling extraction (night purge ventilation).

        PHPP V10 | Cooling | AO136

        Verlust Sommlüft konst
        =SUM(AK136:AN136)

        Units: kwh
        """

        return sum(
            p.exhaust_mech_vent_total_heat_loss_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Envelope Ventilation (Windows and Air-Leakage)

    @property
    def envelope_vent_air_mass_flow_rate_kg_hour(self) -> float:
        """Mass flow rate of passive ventilation air for this calculation period.

        PHPP V10 | Cooling | AO128

        Massenstrom Zuluft kg/h
        =SUMPRODUCT(AK128:AN128,$AK$107:$AN$107)/$AO$107

        Units: kg/h
        """

        sum_product_result = sum(
            p.envelope_vent_air_mass_flow_rate_kg_hour
            * p.period_climate.period_length_hours
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )
        return sum_product_result / self.period_climate.period_length_hours

    @property
    def envelope_vent_total_heat_loss_kwh(self) -> float:
        """Manual and incidental natural window ventilation heat removal.

        PHPP V10 | Cooling | AO141

        Verlust Fenstlüft kwh
        =SUM(AK141:AN141)

        Units: kwh
        """

        return sum(
            p.envelope_vent_total_heat_loss_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Solar and Internal Heat Gains

    @property
    def solar_heat_gain_north_windows_kwh(self) -> float:
        """Solar heat gain through north-facing windows for this calculation period.

        PHPP V10 | Cooling | AO142

        Solar Nord
        =SUM(AK142:AN142)

        Units: kwh
        """

        return sum(
            p.solar_heat_gain_north_windows_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def solar_heat_gain_east_windows_kwh(self) -> float:
        """Solar heat gain through east-facing windows for this calculation period.

        PHPP V10 | Cooling | AO143

        Solar Ost
        =SUM(AK143:AN143)

        Units: kwh
        """

        return sum(
            p.solar_heat_gain_east_windows_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def solar_heat_gain_south_windows_kwh(self) -> float:
        """Solar heat gain through south-facing windows for this calculation period.

        PHPP V10 | Cooling | AO144

        Solar Süd
        =SUM(AK144:AN144)

        Units: kwh
        """

        return sum(
            p.solar_heat_gain_south_windows_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def solar_heat_gain_west_windows_kwh(self) -> float:
        """Solar heat gain through west-facing windows for this calculation period.

        PHPP V10 | Cooling | AO145

        Solar West
        =SUM(AK145:AN145)

        Units: kwh
        """

        return sum(
            p.solar_heat_gain_west_windows_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def solar_heat_gain_horizontal_windows_kwh(self) -> float:
        """Solar heat gain through horizontal windows (skylights) for this calculation period.

        PHPP V10 | Cooling | AO146

        Solar Hori
        =SUM(AK146:AN146)

        Units: kwh
        """

        return sum(
            p.solar_heat_gain_horizontal_windows_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def solar_heat_gain_opaque_kwh(self) -> float:
        """The solar heat gains through opaque building envelope elements.

        PHPP V10 | Cooling | AO147

        Solar opak
        =SUM(AK147:AN147)

        Units: kwh
        """

        return sum(
            p.solar_heat_gain_opaque_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def internal_heat_gain_kwh(self) -> float:
        """The internal heat gains from occupants, equipment, and lighting.

        PHPP V10 | Cooling | AO148

        Interne WQ
        ==SUM(AK148:AN148)

        Units: kwh
        """

        return sum(
            p.internal_heat_gain_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    # ------------------------------------------------------------------------------------------------------------------
    # --- Energy Balance Calculations

    @property
    def total_heat_loss_kwh(self) -> float:
        """The total heat losses from all building systems and envelope components.

        PHPP V10 | Cooling | AO149

        Summe Verl
        =SUM(AK149:AN149)

        Units: kwh
        """

        return sum(
            p.total_heat_loss_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def total_heat_gain_kwh(self) -> float:
        """The total heat gains from internal and solar.

        PHPP V10 | Cooling | T150:AE150

        Summe Ang
        =SUM(T142:T148)

        Units: kwh
        """

        return sum(
            p.total_heat_gain_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )

    @property
    def utilization_factor(self) -> float:
        """The heat-loss-efficiency-factor.

        PHPP V10 | Cooling | AO154

        Nutzungsgrad Wärmeverluste
        =IF(AO149=0,0,(AO150-AO155)/AO149)

        Units: Dimensionless efficiency factor (-)
        """

        try:
            return (
                self.total_heat_gain_kwh - self.cooling_demand_kwh
            ) / self.total_heat_loss_kwh
        except ZeroDivisionError:
            return 0.0

    @property
    def cooling_demand_kwh(self) -> float:
        """The useful cooling demand.

        PHPP V10 | Cooling | AO155

        Nutzkälte
        =SUM(AK155:AN155)

        Units: kwh per month
        """

        return sum(
            p.cooling_demand_kwh
            for p in self.energy_demand.cooling_demand.peak_month.periods
        )


# ----------------------------------------------------------------------------------------------------------------------
# -- Controller


@dataclass
class OpPhCoolingDemandPeakMonth:
    """Solver for Warmest Summer Month Calculations."""

    phpp: "OpPhPHPP"

    peak_single_day: OpPhCoolingDemandPeakCalcPeriod = field(init=False)
    peak_four_day: OpPhCoolingDemandPeakCalcPeriod = field(init=False)
    peak_twelve_day: OpPhCoolingDemandPeakCalcPeriod = field(init=False)
    peak_rest_of_month: OpPhCoolingDemandPeakCalcPeriod = field(init=False)
    peak_total_month: OpPhCoolingDemandPeakMonthCalcPeriod = field(init=False)

    def __post_init__(self) -> None:
        # -- Setup the Peak-Month climate periods
        single_day_climate_period = SingleDayPeriodClimateData(
            self.phpp, period_number=1, display_name="Cooling Peak Month - 1-Day"
        )
        four_day_climate_period = FourDayPeriodClimateData(
            self.phpp, period_number=1, display_name="Cooling Peak Month - 4-Day"
        )
        twelve_day_climate_period = TwelveDayClimateData(
            self.phpp, period_number=1, display_name="Cooling Peak Month - 12-Day"
        )
        rest_of_month_climate_period = RestOfMonthClimateData(
            self.phpp,
            period_number=1,
            display_name="Cooling Peak Month - Rest of Month",
        )
        entire_month_climate_period = EntireMonthClimateData(
            self.phpp, period_number=1, display_name="Cooling Peak Month - Entire Month"
        )

        # -- Initialize radiation values to avoid circular reference during calculate_radiation_factors()
        # Set default values for private radiation attributes so calculate_radiation_factors can work
        for period in [
            single_day_climate_period,
            four_day_climate_period,
            twelve_day_climate_period,
            rest_of_month_climate_period,
            entire_month_climate_period,
        ]:
            period._radiation_north_kwh_m2 = 0.0
            period._radiation_east_kwh_m2 = 0.0
            period._radiation_south_kwh_m2 = 0.0
            period._radiation_west_kwh_m2 = 0.0
            period._radiation_horizontal_kwh_m2 = 0.0

        # -- Calculate all the solar radiation factors
        single_day_climate_period.calculate_radiation_factors()
        four_day_climate_period.calculate_radiation_factors()
        twelve_day_climate_period.calculate_radiation_factors()
        rest_of_month_climate_period.calculate_radiation_factors()

        # -- Build the Calc-Periods
        self.peak_single_day = OpPhCoolingDemandPeakCalcPeriod(
            phpp=self.phpp,
            period_climate=single_day_climate_period,
            period_ground=OpPhGroundResultPeriod(
                phpp=self.phpp, period_climate=single_day_climate_period
            ),
            period_solar_radiation=OpPhSolarRadiationCalcPeriod(
                phpp=self.phpp, period_climate=single_day_climate_period
            ),
        )
        self.peak_four_day = OpPhCoolingDemandPeakCalcPeriod(
            phpp=self.phpp,
            period_climate=four_day_climate_period,
            period_ground=OpPhGroundResultPeriod(
                phpp=self.phpp, period_climate=four_day_climate_period
            ),
            period_solar_radiation=OpPhSolarRadiationCalcPeriod(
                phpp=self.phpp, period_climate=four_day_climate_period
            ),
        )
        self.peak_twelve_day = OpPhCoolingDemandPeakCalcPeriod(
            phpp=self.phpp,
            period_climate=twelve_day_climate_period,
            period_ground=OpPhGroundResultPeriod(
                phpp=self.phpp, period_climate=twelve_day_climate_period
            ),
            period_solar_radiation=OpPhSolarRadiationCalcPeriod(
                phpp=self.phpp, period_climate=twelve_day_climate_period
            ),
        )
        self.peak_rest_of_month = OpPhCoolingDemandPeakCalcPeriod(
            phpp=self.phpp,
            period_climate=rest_of_month_climate_period,
            period_ground=OpPhGroundResultPeriod(
                phpp=self.phpp, period_climate=rest_of_month_climate_period
            ),
            period_solar_radiation=OpPhSolarRadiationCalcPeriod(
                phpp=self.phpp, period_climate=rest_of_month_climate_period
            ),
        )
        self.peak_total_month = OpPhCoolingDemandPeakMonthCalcPeriod(
            phpp=self.phpp,
            period_climate=entire_month_climate_period,
            period_ground=OpPhGroundResultPeriod(
                phpp=self.phpp, period_climate=rest_of_month_climate_period
            ),
            period_solar_radiation=OpPhSolarRadiationCalcPeriod(
                phpp=self.phpp, period_climate=rest_of_month_climate_period
            ),
        )

    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    # ------------------------------------------------------------------------------------------------------------------
    # --- Peak-Month Input Properties from Climate

    @cached_property
    def solarzuschlagsfaktor_max(self) -> float:
        """solarzuschlagsfaktor_max
        PHPP V10 | Cooling | AL98

        =2

        Units: ?
        """
        return 2.0

    @cached_property
    def warmest_annual_calculation_period(self) -> OpPhCoolingDemandCalcPeriod:
        """Return the Annual Calc-Period with the highest outdoor air-temperature."""
        return max(
            self.energy_demand.cooling_demand.periods,
            key=lambda period: period.period_climate.temperature_air_c,
        )

    @cached_property
    def length_days(self) -> int:
        """
        PHPP V10 | Cooling | AI83

        =@INDEX(T83:AE83,$AI$82)

        Units: days
        """
        return self.warmest_annual_calculation_period.length_days

    @cached_property
    def length_hours(self):
        """
        PHPP V10 | Cooling | AI107

        =@INDEX(T107:AE107,$AI$82)

        Units: hours
        """
        return self.length_days * 24

    @cached_property
    def temperature_air_c(self) -> float:
        """
        PHPP V10 | Cooling | AI84

        =@INDEX(T84:AE84,$AI$82)

        Units: C
        """
        return self.warmest_annual_calculation_period.temperature_air_c

    @cached_property
    def temperature_dewpoint_C(self) -> float:
        """Taupunkt
        PHPP V10 | Cooling | AI90

        =@INDEX(T90:AE90,$AI$82)

        Units: C
        """
        return self.warmest_annual_calculation_period.temperature_dewpoint_C

    @cached_property
    def temperature_sky_c(self) -> float:
        """Thimm
        PHPP V10 | Cooling | AI91

        =@INDEX(T92:AE92,$AI$82)

        Units: C
        """
        return self.warmest_annual_calculation_period.temperature_sky_c

    @cached_property
    def temperature_ground_c(self) -> float:
        """BodenTemp
        PHPP V10 | Cooling | AI92

        =@INDEX(T92:AE92,$AI$82)

        Units: C
        """
        return self.warmest_annual_calculation_period.temperature_ground_c

    @cached_property
    def radiation_north(self) -> float:
        """
        PHPP V10 | Cooling | AI102

        =@INDEX(T102:AE102,$AI$82)

        Units: ?
        """
        radiation = self.warmest_annual_calculation_period.period_solar_radiation
        return radiation.get_window_surface_total_radiation_per_m2_for_orientation(
            CardinalOrientation.NORTH
        )

    @cached_property
    def radiation_east(self) -> float:
        """
        PHPP V10 | Cooling | AI103

        =@INDEX(T103:AE103,$AI$82)

        Units: ?
        """
        radiation = self.warmest_annual_calculation_period.period_solar_radiation
        return radiation.get_window_surface_total_radiation_per_m2_for_orientation(
            CardinalOrientation.EAST
        )

    @cached_property
    def radiation_south(self) -> float:
        """
        PHPP V10 | Cooling | AI104

        =@INDEX(T104:AE104,$AI$82)

        Units: ?
        """
        radiation = self.warmest_annual_calculation_period.period_solar_radiation
        return radiation.get_window_surface_total_radiation_per_m2_for_orientation(
            CardinalOrientation.SOUTH
        )

    @cached_property
    def radiation_west(self) -> float:
        """
        PHPP V10 | Cooling | AI105

        =@INDEX(T105:AE105,$AI$82)

        Units: ?
        """
        radiation = self.warmest_annual_calculation_period.period_solar_radiation
        return radiation.get_window_surface_total_radiation_per_m2_for_orientation(
            CardinalOrientation.WEST
        )

    @cached_property
    def radiation_horizontal(self) -> float:
        """
        PHPP V10 | Cooling | AI106

        =@INDEX(T106:AE106,$AI$82)

        Units: ?
        """
        radiation = self.warmest_annual_calculation_period.period_solar_radiation
        return radiation.get_window_surface_total_radiation_per_m2_for_orientation(
            CardinalOrientation.HORIZONTAL
        )

    @cached_property
    def radiation_opaque(self):
        """
        PHPP V10 | Cooling | AI147

        =@INDEX(T147:AE147,$AI$82)

        Units: ?
        """
        return self.warmest_annual_calculation_period.solar_heat_gain_opaque_kwh

    @cached_property
    def heat_losses_to_ground_from_annual_calc(self) -> float:
        """
        PHPP V10 | Cooling | AI113

        =@INDEX(T113:AE113,$AI$82)

        Units: kwh ?
        """
        return self.warmest_annual_calculation_period.conductive_heat_loss_to_ground_kwh

    # ------------------------------------------------------------------------------------------------------------------
    # -- Calculated Values

    @cached_property
    def periods(self) -> list[OpPhCoolingDemandPeakCalcPeriod]:
        """A list of the Peak-Month calc-periods."""
        return [
            self.peak_single_day,
            self.peak_four_day,
            self.peak_twelve_day,
            self.peak_rest_of_month,
        ]

    @cached_property
    def periods_with_total_monthly(
        self,
    ) -> list[OpPhCoolingDemandPeakCalcPeriod | OpPhCoolingDemandPeakMonthCalcPeriod]:
        """A list of the Peak-Month calc-periods, plus the total month period."""
        return [
            self.peak_single_day,
            self.peak_four_day,
            self.peak_twelve_day,
            self.peak_rest_of_month,
            self.peak_total_month,
        ]
