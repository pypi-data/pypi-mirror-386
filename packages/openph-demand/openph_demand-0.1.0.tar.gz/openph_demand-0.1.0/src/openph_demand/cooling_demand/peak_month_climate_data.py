# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Cooling Demand Peak Month Climate-Data Input Classes."""

from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

    from openph_demand.solvers import OpPhEnergyDemandSolver

from openph.model.climate import OpPhClimateCalcPeriod
from openph.model.enums import CardinalOrientation

from openph_demand.get_solvers import get_openph_energy_demand_solver

# ----------------------------------------------------------------------------------------------------------------------
# -- Input / Climate Data [AK82:AN93] for the Calculation Periods
# -- Each of the periods does the calculation slightly differently, so we use a distinct class for each one.


class SingleDayPeriodClimateData(OpPhClimateCalcPeriod):
    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def temperature_difference_C(self) -> float:
        """
        PHPP V10 | Cooling | AK82

        =AK84-AI84

        Units: C
        """

        return (
            self.temperature_air_c
            - self.energy_demand.cooling_demand.peak_month.temperature_air_c
        )

    @property
    def period_length_days(self) -> int:
        """
        PHPP V10 | Cooling | AK83

        =1

        Units: Number-of-Days
        """
        return 1

    @property
    def period_length_hours(self) -> int:
        """
        PHPP V10 | Cooling | AK107:AN107

        =$R107*AK$83

        Units: Number-of-Hours
        """
        return self.period_length_days * 24

    @period_length_hours.setter
    def period_length_hours(self, _input: int) -> None:
        self._period_length_hours = _input

    @property
    def temperature_air_c(self) -> float:
        """
        PHPP V10 | Cooling | AK84

        =IF(ISNUMBER(Climate!S26),Climate!S26,AI84+6)

        Units: C
        """
        if self.phpp.climate.peak_cooling_1.temperature_air_c:
            return self.phpp.climate.peak_cooling_1.temperature_air_c
        else:
            return self.energy_demand.cooling_demand.peak_month.temperature_air_c + 6

    @temperature_air_c.setter
    def temperature_air_c(self, _input) -> None:
        return None

    @property
    def temperature_dewpoint_c(self) -> float:
        """
        PHPP V10 | Cooling | AK90

        =IF(ISNUMBER(Climate!S32),Climate!S32,IF(ISNUMBER(AI90),AI90,0))

        Units: C
        """
        if self.phpp.climate.peak_cooling_1.temperature_dewpoint_c:
            return self.phpp.climate.peak_cooling_1.temperature_dewpoint_c
        else:
            if self.energy_demand.cooling_demand.peak_month.temperature_dewpoint_C:
                return (
                    self.energy_demand.cooling_demand.peak_month.temperature_dewpoint_C
                )
            else:
                return 0.0

    @temperature_dewpoint_c.setter
    def temperature_dewpoint_c(self, _input) -> None:
        return None

    @property
    def temperature_sky_c(self) -> float:
        """
        PHPP V10 | Cooling | AK91

        =IF(ISNUMBER(Climate!S33),Climate!S33,$AI91+AK$82)

        Units: C
        """
        if self.phpp.climate.peak_cooling_1.temperature_sky_c:
            return self.phpp.climate.peak_cooling_1.temperature_sky_c
        else:
            return (
                self.energy_demand.cooling_demand.peak_month.temperature_sky_c
                + self.temperature_difference_C
            )

    @temperature_sky_c.setter
    def temperature_sky_c(self, _input) -> None:
        return None

    @property
    def temperature_ground_c(self) -> float:
        """
        PHPP V10 | Cooling | AK92

        =$AI$92

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_ground_c

    @temperature_ground_c.setter
    def temperature_ground_c(self, _input) -> None:
        return None

    @property
    def radiation_opaque_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AK93

        =Areas!$DB$10*0.024

        Units: kwh/day
        """

        return (
            self.energy_demand.cooling_demand.solar_radiation.peak_cooling_load_1.all_opaque_elements_solar_heat_gain_kwh
            * 0.024
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation Per-Day

    @property
    def radiation_north_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AK85

        =MIN(IF(ISNUMBER(Windows!GT6),Windows!GT6*0.024,10000000000),AI102*$AL$98*$AK$83/$AI$83)

        Units: kwh/m2-day
        """

        a = (
            self.energy_demand.cooling_demand.solar_radiation.peak_cooling_load_1.get_window_surface_period_total_radiation_per_m2_for_orientation(
                CardinalOrientation.NORTH
            )[
                0
            ]
            * 0.024
        )
        b = (
            self.energy_demand.cooling_demand.peak_month.radiation_north
            * self.energy_demand.cooling_demand.peak_month.solarzuschlagsfaktor_max
            * self.period_length_days
            / self.energy_demand.cooling_demand.peak_month.length_days
        )
        return min(a, b)

    @property
    def radiation_east_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AK86

        =MIN(IF(ISNUMBER(Windows!GT7),Windows!GT7*0.024,10000000000),AI103*$AL$98*$AK$83/$AI$83)

        Units: kwh/m2-day
        """

        a = (
            self.energy_demand.cooling_demand.solar_radiation.peak_cooling_load_1.get_window_surface_period_total_radiation_per_m2_for_orientation(
                CardinalOrientation.EAST
            )[
                0
            ]
            * 0.024
        )
        b = (
            self.energy_demand.cooling_demand.peak_month.radiation_east
            * self.energy_demand.cooling_demand.peak_month.solarzuschlagsfaktor_max
            * self.period_length_days
            / self.energy_demand.cooling_demand.peak_month.length_days
        )
        return min(a, b)

    @property
    def radiation_south_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AK87

        =MIN(IF(ISNUMBER(Windows!GT8),Windows!GT8*0.024,10000000000),AI104*$AL$98*$AK$83/$AI$83)

        Units: kwh/m2-day
        """

        a = (
            self.energy_demand.cooling_demand.solar_radiation.peak_cooling_load_1.get_window_surface_period_total_radiation_per_m2_for_orientation(
                CardinalOrientation.SOUTH
            )[
                0
            ]
            * 0.024
        )
        b = (
            self.energy_demand.cooling_demand.peak_month.radiation_south
            * self.energy_demand.cooling_demand.peak_month.solarzuschlagsfaktor_max
            * self.period_length_days
            / self.energy_demand.cooling_demand.peak_month.length_days
        )
        return min(a, b)

    @property
    def radiation_west_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AK88

        =MIN(IF(ISNUMBER(Windows!GT9),Windows!GT9*0.024,10000000000),AI105*$AL$98*$AK$83/$AI$83)

        Units: kwh/m2-day
        """

        a = (
            self.energy_demand.cooling_demand.solar_radiation.peak_cooling_load_1.get_window_surface_period_total_radiation_per_m2_for_orientation(
                CardinalOrientation.WEST
            )[
                0
            ]
            * 0.024
        )
        b = (
            self.energy_demand.cooling_demand.peak_month.radiation_west
            * self.energy_demand.cooling_demand.peak_month.solarzuschlagsfaktor_max
            * self.period_length_days
            / self.energy_demand.cooling_demand.peak_month.length_days
        )
        return min(a, b)

    @property
    def radiation_horizontal_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AK89

        =MIN(IF(ISNUMBER(Windows!GT10),Windows!GT10*0.024,10000000000),AI106*$AL$98*$AK$83/$AI$83)

        Units: kwh/m2-day
        """

        a = (
            self.energy_demand.cooling_demand.solar_radiation.peak_cooling_load_1.get_window_surface_period_total_radiation_per_m2_for_orientation(
                CardinalOrientation.HORIZONTAL
            )[
                0
            ]
            * 0.024
        )
        b = (
            self.energy_demand.cooling_demand.peak_month.radiation_horizontal
            * self.energy_demand.cooling_demand.peak_month.solarzuschlagsfaktor_max
            * self.period_length_days
            / self.energy_demand.cooling_demand.peak_month.length_days
        )
        return min(a, b)

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation For Entire Period

    @property
    def radiation_north_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK102:AN102

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_north_kwh_m2_day * self.period_length_days

    @radiation_north_kwh_m2.setter
    def radiation_north_kwh_m2(self, _input) -> None:
        self._radiation_north_kwh_m2 = _input

    @property
    def radiation_east_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK103:AN103

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_east_kwh_m2_day * self.period_length_days

    @radiation_east_kwh_m2.setter
    def radiation_east_kwh_m2(self, _input) -> None:
        self._radiation_east_kwh_m2 = _input

    @property
    def radiation_south_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK104:AN104

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_south_kwh_m2_day * self.period_length_days

    @radiation_south_kwh_m2.setter
    def radiation_south_kwh_m2(self, _input) -> None:
        self._radiation_south_kwh_m2 = _input

    @property
    def radiation_west_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK105:AN15

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_west_kwh_m2_day * self.period_length_days

    @radiation_west_kwh_m2.setter
    def radiation_west_kwh_m2(self, _input) -> None:
        self._radiation_west_kwh_m2 = _input

    @property
    def radiation_horizontal_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK106:AN106

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_horizontal_kwh_m2_day * self.period_length_days

    @radiation_horizontal_kwh_m2.setter
    def radiation_horizontal_kwh_m2(self, _input) -> None:
        self._radiation_horizontal_kwh_m2 = _input


class FourDayPeriodClimateData(OpPhClimateCalcPeriod):
    phpp: "OpPhPHPP"

    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def temperature_difference_C(self) -> float:
        """
        PHPP V10 | Cooling | AL82

        =0.5*AK82

        Units: C
        """

        return (
            0.5
            * self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.temperature_difference_C
        )

    @property
    def period_length_days(self) -> int:
        """
        PHPP V10 | Cooling | AL83

        =4

        Units: number-of-days
        """
        return 4

    @property
    def period_length_hours(self) -> int:
        """
        PHPP V10 | Cooling | AK107:AN107

        =$R107*AK$83

        Units: Number-of-Hours
        """
        return self.period_length_days * 24

    @period_length_hours.setter
    def period_length_hours(self, _input: int) -> None:
        self._period_length_hours = _input

    @property
    def temperature_air_c(self) -> float:
        """
        PHPP V10 | Cooling | AL84

        =$AI84+AL$82

        Units: C
        """

        return (
            self.energy_demand.cooling_demand.peak_month.temperature_air_c
            + self.temperature_difference_C
        )

    @temperature_air_c.setter
    def temperature_air_c(self, _input) -> None:
        return None

    @property
    def temperature_dewpoint_c(self) -> float:
        """
        PHPP V10 | Cooling | AL90

        =$AI$90

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_dewpoint_C

    @temperature_dewpoint_c.setter
    def temperature_dewpoint_c(self, _input) -> None:
        return None

    @property
    def temperature_sky_c(self) -> float:
        """
        PHPP V10 | Cooling | AL91

        =$AI91+AL$82

        Units: C
        """

        return (
            self.energy_demand.cooling_demand.peak_month.temperature_sky_c
            + self.temperature_difference_C
        )

    @temperature_sky_c.setter
    def temperature_sky_c(self, _input) -> None:
        return None

    @property
    def temperature_ground_c(self) -> float:
        """
        PHPP V10 | Cooling | AL92

        =$AI$92

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_ground_c

    @temperature_ground_c.setter
    def temperature_ground_c(self, _input) -> None:
        return None

    @property
    def radiation_opaque_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AL93

        =$AI147/$AI$83+(AK93-$AI147/$AI$83)*0.5

        Units: kwh/day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_opaque
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_opaque_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_opaque
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation Per-Day

    @property
    def radiation_north_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AL85

        =$AI102/$AI$83+(AK85-$AI102/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_north
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_north_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_north
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_east_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AL86

        =$AI103/$AI$83+(AK86-$AI103/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_east
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_east_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_east
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_south_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AL87

        =$AI104/$AI$83+(AK87-$AI104/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_south
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_south_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_south
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_west_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AL88

        =$AI105/$AI$83+(AK88-$AI105/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_west
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_west_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_west
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_horizontal_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AL89

        =$AI106/$AI$83+(AK89-$AI106/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_horizontal
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_horizontal_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_horizontal
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation For Entire Period

    @property
    def radiation_north_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK102:AN102

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_north_kwh_m2_day * self.period_length_days

    @radiation_north_kwh_m2.setter
    def radiation_north_kwh_m2(self, _input) -> None:
        self._radiation_north_kwh_m2 = _input

    @property
    def radiation_east_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK103:AN103

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_east_kwh_m2_day * self.period_length_days

    @radiation_east_kwh_m2.setter
    def radiation_east_kwh_m2(self, _input) -> None:
        self._radiation_east_kwh_m2 = _input

    @property
    def radiation_south_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK104:AN104

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_south_kwh_m2_day * self.period_length_days

    @radiation_south_kwh_m2.setter
    def radiation_south_kwh_m2(self, _input) -> None:
        self._radiation_south_kwh_m2 = _input

    @property
    def radiation_west_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK105:AN15

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_west_kwh_m2_day * self.period_length_days

    @radiation_west_kwh_m2.setter
    def radiation_west_kwh_m2(self, _input) -> None:
        self._radiation_west_kwh_m2 = _input

    @property
    def radiation_horizontal_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK106:AN106

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_horizontal_kwh_m2_day * self.period_length_days

    @radiation_horizontal_kwh_m2.setter
    def radiation_horizontal_kwh_m2(self, _input) -> None:
        self._radiation_horizontal_kwh_m2 = _input


class TwelveDayClimateData(OpPhClimateCalcPeriod):
    phpp: "OpPhPHPP"

    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def temperature_difference_C(self) -> float:
        """
        PHPP V10 | Cooling | AM82

        =0.5*AL82

        Units: C
        """

        return (
            0.5
            * self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.temperature_difference_C
        )

    @property
    def period_length_days(self) -> int:
        """
        PHPP V10 | Cooling | AM83

        =12

        Units: number-of-days
        """
        return 12

    @property
    def period_length_hours(self) -> int:
        """
        PHPP V10 | Cooling | AK107:AN107

        =$R107*AK$83

        Units: Number-of-Hours
        """
        return self.period_length_days * 24

    @period_length_hours.setter
    def period_length_hours(self, _input: int) -> None:
        self._period_length_hours = _input

    @property
    def temperature_air_c(self) -> float:
        """
        PHPP V10 | Cooling | AM84

        =$AI84+AM$82

        Units: C
        """

        return (
            self.energy_demand.cooling_demand.peak_month.temperature_air_c
            + self.temperature_difference_C
        )

    @temperature_air_c.setter
    def temperature_air_c(self, _input) -> None:
        return None

    @property
    def temperature_dewpoint_c(self) -> float:
        """
        PHPP V10 | Cooling | AM90

        =$AI$90

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_dewpoint_C

    @temperature_dewpoint_c.setter
    def temperature_dewpoint_c(self, _input) -> None:
        return None

    @property
    def temperature_sky_c(self) -> float:
        """
        PHPP V10 | Cooling | AM91

        =$AI91+AM$82

        Units: C
        """

        return (
            self.energy_demand.cooling_demand.peak_month.temperature_sky_c
            + self.temperature_difference_C
        )

    @temperature_sky_c.setter
    def temperature_sky_c(self, _input) -> None:
        return None

    @property
    def temperature_ground_c(self) -> float:
        """
        PHPP V10 | Cooling | AM92

        =$AI$92

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_ground_c

    @temperature_ground_c.setter
    def temperature_ground_c(self, _input) -> None:
        return None

    @property
    def radiation_opaque_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AM93

        =$AI147/$AI$83+(AL93-$AI147/$AI$83)*0.5

        Units: kwh/day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_opaque
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_opaque_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_opaque
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation Per-Day
    @property
    def radiation_north_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AM85

        =$AI102/$AI$83+(AL85-$AI102/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_north
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_north_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_north
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_east_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AM86

        =$AI103/$AI$83+(AL86-$AI103/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_east
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_east_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_east
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_south_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AM87

        =$AI104/$AI$83+(AL87-$AI104/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_south
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_south_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_south
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_west_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AM88

        =$AI105/$AI$83+(AL88-$AI105/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_west
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_west_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_west
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    @property
    def radiation_horizontal_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AM89

        =$AI106/$AI$83+(AL89-$AI106/$AI$83)*0.5

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_horizontal
            / self.energy_demand.cooling_demand.peak_month.length_days
            + (
                self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_horizontal_kwh_m2_day
                - self.energy_demand.cooling_demand.peak_month.radiation_horizontal
                / self.energy_demand.cooling_demand.peak_month.length_days
            )
            * 0.5
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation For Entire Period

    @property
    def radiation_north_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK102:AN102

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_north_kwh_m2_day * self.period_length_days

    @radiation_north_kwh_m2.setter
    def radiation_north_kwh_m2(self, _input) -> None:
        self._radiation_north_kwh_m2 = _input

    @property
    def radiation_east_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK103:AN103

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_east_kwh_m2_day * self.period_length_days

    @radiation_east_kwh_m2.setter
    def radiation_east_kwh_m2(self, _input) -> None:
        self._radiation_east_kwh_m2 = _input

    @property
    def radiation_south_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK104:AN104

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_south_kwh_m2_day * self.period_length_days

    @radiation_south_kwh_m2.setter
    def radiation_south_kwh_m2(self, _input) -> None:
        self._radiation_south_kwh_m2 = _input

    @property
    def radiation_west_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK105:AN15

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_west_kwh_m2_day * self.period_length_days

    @radiation_west_kwh_m2.setter
    def radiation_west_kwh_m2(self, _input) -> None:
        self._radiation_west_kwh_m2 = _input

    @property
    def radiation_horizontal_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AK106:AN106

        =AK85*AK$83

        Units: kwh/m2-period
        """
        return self.radiation_horizontal_kwh_m2_day * self.period_length_days

    @radiation_horizontal_kwh_m2.setter
    def radiation_horizontal_kwh_m2(self, _input) -> None:
        self._radiation_horizontal_kwh_m2 = _input


class RestOfMonthClimateData(OpPhClimateCalcPeriod):
    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def temperature_difference_C(self) -> float:
        """
        PHPP V10 | Cooling | AN82

        Units: -
        """
        return 0.0

    @property
    def period_length_days(self) -> int:
        """
        PHPP V10 | Cooling | AN83

        =AI83-SUM(AK83:AM83)

        Units: number-of-days
        """

        return self.energy_demand.cooling_demand.peak_month.length_days - (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.period_length_days
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.period_length_days
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.period_length_days
        )

    @property
    def period_length_hours(self) -> int:
        """
        PHPP V10 | Cooling | AK107:AN107

        =$R107*AK$83

        Units: Number-of-Hours
        """
        return self.period_length_days * 24

    @period_length_hours.setter
    def period_length_hours(self, _input: int) -> None:
        self._period_length_hours = _input

    @property
    def temperature_air_c(self) -> float:
        """
        PHPP V10 | Cooling | AN84

        =($AI84*$AI$107-SUMPRODUCT($AK$107:$AM$107,AK84:AM84))/$AN$107

        Units: C
        """

        sum_product_result = sum(
            a * b
            for a, b in zip(
                [
                    self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.temperature_air_c,
                    self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.temperature_air_c,
                    self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.temperature_air_c,
                ],
                [
                    self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.period_length_hours,
                    self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.period_length_hours,
                    self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.period_length_hours,
                ],
            )
        )
        return (
            self.energy_demand.cooling_demand.peak_month.temperature_air_c
            * self.energy_demand.cooling_demand.peak_month.length_hours
            - sum_product_result
        ) / self.period_length_hours

    @temperature_air_c.setter
    def temperature_air_c(self, _input) -> None:
        return None

    @property
    def temperature_dewpoint_c(self) -> float:
        """
        PHPP V10 | Cooling | AN90

        =$AI$90

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_dewpoint_C

    @temperature_dewpoint_c.setter
    def temperature_dewpoint_c(self, _input) -> None:
        return None

    @property
    def temperature_sky_c(self) -> float:
        """
        PHPP V10 | Cooling | AN91

        =($AI91*$AI$107-SUMPRODUCT($AK$107:$AM$107,AK91:AM91))/$AN$107

        Units: C
        """

        sum_product_result = sum(
            a * b
            for a, b in zip(
                [
                    self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.temperature_sky_c,
                    self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.temperature_sky_c,
                    self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.temperature_sky_c,
                ],
                [
                    self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.period_length_hours,
                    self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.period_length_hours,
                    self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.period_length_hours,
                ],
            )
        )
        return (
            self.energy_demand.cooling_demand.peak_month.temperature_sky_c
            * self.energy_demand.cooling_demand.peak_month.length_hours
            - sum_product_result
        ) / self.period_length_hours

    @temperature_sky_c.setter
    def temperature_sky_c(self, _input) -> None:
        return None

    @property
    def temperature_ground_c(self) -> float:
        """
        PHPP V10 | Cooling | AN92

        =$AI$92

        Units: C
        """

        return self.energy_demand.cooling_demand.peak_month.temperature_ground_c

    @temperature_ground_c.setter
    def temperature_ground_c(self, _input) -> None:
        return None

    @property
    def radiation_opaque_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AN93

        Units: kwh/m2-day
        """

        return (
            self.energy_demand.cooling_demand.peak_month.radiation_opaque
            - (
                self.energy_demand.cooling_demand.peak_month.peak_single_day.solar_heat_gain_opaque_kwh
                + self.energy_demand.cooling_demand.peak_month.peak_four_day.solar_heat_gain_opaque_kwh
                + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.solar_heat_gain_opaque_kwh
            )
        ) / self.period_length_days

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation Per-Day

    @property
    def radiation_north_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AN85

        Units: -
        """
        return 0.0

    @property
    def radiation_east_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AN86

        Units: -
        """
        return 0.0

    @property
    def radiation_south_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AN87

        Units: -
        """
        return 0.0

    @property
    def radiation_west_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AN88

        Units: -
        """
        return 0.0

    @property
    def radiation_horizontal_kwh_m2_day(self) -> float:
        """
        PHPP V10 | Cooling | AN89

        Units: -
        """
        return 0.0

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation For Entire Period

    @property
    def radiation_north_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AN102

        =$AI102-SUM(AK102:AM102)

        Units: kwh/m2-period
        """

        return self.energy_demand.cooling_demand.peak_month.radiation_north - (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_north_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_north_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_north_kwh_m2
        )

    @radiation_north_kwh_m2.setter
    def radiation_north_kwh_m2(self, _input) -> None:
        self._radiation_north_kwh_m2 = _input

    @property
    def radiation_east_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AN103

        =$AI103-SUM(AK103:AM103)

        Units: kwh/m2-period
        """

        return self.energy_demand.cooling_demand.peak_month.radiation_east - (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_east_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_east_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_east_kwh_m2
        )

    @radiation_east_kwh_m2.setter
    def radiation_east_kwh_m2(self, _input) -> None:
        self._radiation_east_kwh_m2 = _input

    @property
    def radiation_south_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AN104

        =$AI104-SUM(AK104:AM104)

        Units: kwh/m2-period
        """

        return self.energy_demand.cooling_demand.peak_month.radiation_south - (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_south_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_south_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_south_kwh_m2
        )

    @radiation_south_kwh_m2.setter
    def radiation_south_kwh_m2(self, _input) -> None:
        self._radiation_south_kwh_m2 = _input

    @property
    def radiation_west_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AN105

        =$AI105-SUM(AK105:AM105)

        Units: kwh/m2-period
        """

        return self.energy_demand.cooling_demand.peak_month.radiation_west - (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_west_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_west_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_west_kwh_m2
        )

    @radiation_west_kwh_m2.setter
    def radiation_west_kwh_m2(self, _input) -> None:
        self._radiation_west_kwh_m2 = _input

    @property
    def radiation_horizontal_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AN106

        ==$AI106-SUM(AK106:AM106)

        Units: kwh/m2-period
        """

        return self.energy_demand.cooling_demand.peak_month.radiation_horizontal - (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_horizontal_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_horizontal_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_horizontal_kwh_m2
        )

    @radiation_horizontal_kwh_m2.setter
    def radiation_horizontal_kwh_m2(self, _input) -> None:
        self._radiation_horizontal_kwh_m2 = _input


class EntireMonthClimateData(OpPhClimateCalcPeriod):
    @cached_property
    def energy_demand(self) -> "OpPhEnergyDemandSolver":
        return get_openph_energy_demand_solver(self.phpp)

    @property
    def period_length_days(self) -> int:
        """
        PHPP V10 | Cooling | AO83

        Units: Number-of-days
        """

        return (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.period_length_days
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.period_length_days
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.period_length_days
            + self.energy_demand.cooling_demand.peak_month.peak_rest_of_month.period_climate.period_length_days
        )

    @property
    def period_length_hours(self) -> int:
        """
        PHPP V10 | Cooling | AO107

        =$R107*AO$83

        Units: Number-of-Hours
        """
        return self.period_length_days * 24

    @period_length_hours.setter
    def period_length_hours(self, _input: int) -> None:
        self._period_length_hours = _input

    # ------------------------------------------------------------------------------------------------------------------
    # -- Radiation For Entire Period

    @property
    def radiation_north_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AO102

        =SUM(AK102:AN102)

        Units: kwh/m2-period
        """

        return (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_north_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_north_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_north_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_rest_of_month.period_climate.radiation_north_kwh_m2
        )

    @radiation_north_kwh_m2.setter
    def radiation_north_kwh_m2(self, _input) -> None:
        self._radiation_north_kwh_m2 = _input

    @property
    def radiation_east_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AO103

        =SUM(AK103:AN103)

        Units: kwh/m2-period
        """

        return (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_east_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_east_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_east_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_rest_of_month.period_climate.radiation_east_kwh_m2
        )

    @radiation_east_kwh_m2.setter
    def radiation_east_kwh_m2(self, _input) -> None:
        self._radiation_east_kwh_m2 = _input

    @property
    def radiation_south_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AO104

        =SUM(AK104:AN104)

        Units: kwh/m2-period
        """

        return (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_south_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_south_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_south_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_rest_of_month.period_climate.radiation_south_kwh_m2
        )

    @radiation_south_kwh_m2.setter
    def radiation_south_kwh_m2(self, _input) -> None:
        self._radiation_south_kwh_m2 = _input

    @property
    def radiation_west_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AO105

        =SUM(AK105:AN105)

        Units: kwh/m2-period
        """

        return (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_west_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_west_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_west_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_rest_of_month.period_climate.radiation_west_kwh_m2
        )

    @radiation_west_kwh_m2.setter
    def radiation_west_kwh_m2(self, _input) -> None:
        self._radiation_west_kwh_m2 = _input

    @property
    def radiation_horizontal_kwh_m2(self) -> float:
        """
        PHPP V10 | Cooling | AO106

        =SUM(AK106:AN106)

        Units: kwh/m2-period
        """

        return (
            self.energy_demand.cooling_demand.peak_month.peak_single_day.period_climate.radiation_horizontal_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_four_day.period_climate.radiation_horizontal_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_twelve_day.period_climate.radiation_horizontal_kwh_m2
            + self.energy_demand.cooling_demand.peak_month.peak_rest_of_month.period_climate.radiation_horizontal_kwh_m2
        )

    @radiation_horizontal_kwh_m2.setter
    def radiation_horizontal_kwh_m2(self, _input) -> None:
        self._radiation_horizontal_kwh_m2 = _input
