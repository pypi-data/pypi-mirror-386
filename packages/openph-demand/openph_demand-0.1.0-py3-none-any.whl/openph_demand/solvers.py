# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""....."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.phpp import OpPhPHPP

from openph.model.enums import Hemisphere

from openph_demand.cooling_demand.cooling_demand import OpPhCoolingDemand
from openph_demand.ground.calc_periods import OpPhCalculationIteration
from openph_demand.ground.heat_flow_iterative_solvers import (
    solve_for_iteration_heat_flows,
    solve_for_iteration_temperatures,
)
from openph_demand.ground.heat_flow_step_1_solvers import (
    solve_for_step_1_heat_flows,
    solve_for_step_1_temperatures,
)
from openph_demand.ground.results_period import (
    OpPhGroundEstimate,
    OpPhGroundResultPeriod,
)
from openph_demand.heating_demand.heating_demand import OpPhHeatingDemand


@dataclass
class OpPhEnergyDemandSolver:
    phpp: "OpPhPHPP"

    cooling_demand: OpPhCoolingDemand = field(init=False)
    heating_demand: OpPhHeatingDemand = field(init=False)

    def __post_init__(self):
        self.cooling_demand = OpPhCoolingDemand(self.phpp)
        self.heating_demand = OpPhHeatingDemand(self.phpp)


@dataclass
class OpPhGroundSolver:
    phpp: "OpPhPHPP"
    _periods: list[OpPhGroundResultPeriod] = field(default_factory=list)
    _iterations: list[OpPhCalculationIteration] = field(default_factory=list)
    estimated: OpPhGroundEstimate = field(init=False)
    _calculation_complete: bool = False

    def __post_init__(self):
        """Setup all of the calculation-periods."""
        for p in self.phpp.climate.periods:
            self._periods.append(OpPhGroundResultPeriod(self.phpp, p))
        self.estimated = OpPhGroundEstimate(self.phpp)

    @cached_property
    def iterations(self) -> list[OpPhCalculationIteration]:
        """Lazily calculate ground heat flow on first access.

        This property calculates and caches the iterative ground heat flow
        solution. It only runs once, when first accessed.
        """
        if not self._calculation_complete:
            self._calculate_ground_heat_flow()
        return self._iterations or []

    @property
    def periods(self) -> list[OpPhGroundResultPeriod]:
        return self._periods

    # ------------------------------------------------------------------------------------------------------------------
    # -- Climate Properties
    @property
    def min_interior_temp_c(self):
        """
        PHPP V10 | Ground | P9

        ='Annual heating'!O6

        Units: C
        """
        return self.phpp.set_points.min_interior_temp_c

    @property
    def max_interior_temp_c(self):
        """
        PHPP V10 | Ground | P10

        =Verification!N28

        Units: C
        """
        return self.phpp.set_points.max_interior_temp_c

    @property
    def average_ground_surface_temp_C(self) -> float:
        """
        PHPP V10 | Ground | P11

        =IF(ISNUMBER(Climate!AE29),Climate!AE29+1,"")

        Units: C
        """
        return self.phpp.climate.average_annual_air_temp_C + 1.0

    @property
    def amplitude_theta_e_m_deg_C(self) -> float:
        """
        PHPP V10 | Ground | P12

        =(MAX(Climate!E26:P26)-MIN(Climate!E26:P26))/2

        Units: C
        """
        return (
            max(self.phpp.climate.temperature_air_c)
            - min(self.phpp.climate.temperature_air_c)
        ) / 2

    @property
    def phase_shift_theta_e_Months(self) -> float:
        """
        PHPP V10 | Ground | P13

        =IF(Climate!$X$25,Climate!AE32,Climate!AE32+6)

        Units: C
        """
        if self.phpp.climate.hemisphere == Hemisphere.NORTH:
            return self.phpp.climate.ClimateAE32
        else:
            return self.phpp.climate.ClimateAE32 + 6

    @property
    def heating_period_length(self) -> float:
        """
        PHPP V10 | Ground | P14

        =IF(ISNUMBER(Climate!K9),Climate!K9*12/365,6)

        Units: Int (Months)
        """
        if self.phpp.climate.heating_period_days:
            return self.phpp.climate.heating_period_days * 12 / 365
        else:
            return 6

    @property
    def heating_degree_hours(self) -> float:
        """
        PHPP V10 | Ground | P15

        =IF(ISNUMBER('Annual heating'!M12),'Annual heating'!M12,0)
        --> =IF(ISNUMBER(Climate!K10),Climate!K10+('Annual heating'!O6-20)*'Annual heating'!I61*0.024,"")

        Units: kKhrs / year
        """
        return (
            self.phpp.climate.heating_degree_hours
            + (self.phpp.set_points.min_interior_temp_c - 20)
            * self.phpp.climate.heating_period_days
            * 0.024
        )

    # ------------------------------------------------------------------------------------------------------------------
    # -- Building / Foundation Properties
    @property
    def conductance_to_ground_W_K(self):
        """PHPP V10 | Ground | H119

        =IF(H100,H102,H218)

        Units: W/K
        """
        if False:  # TODO: Implement actual test (Need user Foundation inputs)
            return 0.0
        else:
            return self.estimated.conductance_to_ground_W_K

    @property
    def outer_harmonic_conductance(self) -> float:
        """
        PHPP V10 | Ground | H120

        =IF(H100,H103,H219)

        Units: C
        """
        if False:  # TODO: Implement actual test
            return 0.0
        else:
            return self.estimated.outer_harmonic_conductance

    @property
    def outer_phase_shift(self) -> float:
        """
        PHPP V10 | Ground | H121

        =IF(H100,H104,H220)

        Units: Months
        """
        if False:  # TODO: Implement actual test
            return 0.0
        else:
            return self.estimated.outer_phase_shift

    @property
    def conductance_of_building(self):
        """PHPP V10 | Ground | P119

        =IF(H100,P102,P218)

        Units: W/K
        """
        if False:  # TODO: Implement actual test
            return 0.0
        else:
            return self.estimated.conductivity_of_building_W_K

    @property
    def inner_harmonic_conductance(self) -> float:
        """
        PHPP V10 | Ground | P120

        =IF(H100,P103,H221)

        Units: C
        """
        if False:  # TODO: Implement actual test
            return 0.0
        else:
            return self.estimated.inner_harmonic_conductance

    @property
    def inner_phase_shift(self) -> float:
        """
        PHPP V10 | Ground | P121

        =IF(H100,P104,H222)

        Units: Months
        """
        if False:  # TODO: Implement actual test
            return 0.0
        else:
            return self.estimated.inner_phase_shift

    @property
    def total_heat_flow_to_ground_w(self) -> list[float]:
        """
        PHPP V10 | Ground | E112:P112

        =E200

        Units: W
        """
        # Accessing self.iterations triggers calculation if needed
        _ = self.iterations
        return [p.total_heat_flow_to_ground_w for p in self._periods]

    @cached_property
    def peak_heat_load_design_ground_temp(self) -> float:
        """Calculate ground temperature for peak heating load.

        PHPP V10 | Ground | J114

        Excel Formula:
        =IF($P$119>0,P9-@INDEX(E200:P200,E202)/$P$119,P9)

        Where:
        - P9 = self.min_interior_temp_c
        - $P$119 = total_thermal_conductance (W/K)
        - E200:P200 = total_heat_flow_to_ground_w for each period
        - E202 = period index for peak heating

        Units: C
        """
        _ = self.iterations  # Accessing self.iterations triggers calculation if needed
        return self._calculate_peak_heating_temp()

    @cached_property
    def peak_cooling_load_design_ground_temp(self) -> float:
        """Calculate ground temperature for peak cooling load.

        PHPP V10 | Ground | P114

        Excel Formula:
        =IF($P$119>0,P10-@INDEX(E200:P200,I202)/$P$119,P10)

        Where:
        - P10 = self.max_interior_temp_c
        - $P$119 = total_thermal_conductance (W/K)
        - E200:P200 = total_heat_flow_to_ground_w for each period
        - I202 = period index for peak cooling

        Units: C
        """
        _ = self.iterations  # Accessing self.iterations triggers calculation if needed
        return self._calculate_peak_cooling_temp()

    # ------------------------------------------------------------------------------------------------------------------
    # ---- Calc

    def _calculate_ground_heat_flow(self):
        """Internal method to perform the iterative ground heat flow calculation.

        This is called automatically by the `iterations` property on first access.
        It can also be called explicitly if needed.
        """
        if self._calculation_complete:
            return  # Already calculated

        iterations_list = []

        # Setup the starting iteration
        current_iteration = OpPhCalculationIteration()
        solve_for_step_1_temperatures(current_iteration, self.phpp)
        solve_for_step_1_heat_flows(current_iteration, self.phpp)
        iterations_list.append(current_iteration)

        # Walk through 9 more iterations
        for i in range(9):
            new_iteration = OpPhCalculationIteration()
            solve_for_iteration_temperatures(
                current_iteration, new_iteration, self.phpp
            )
            solve_for_iteration_heat_flows(current_iteration, new_iteration, self.phpp)
            iterations_list.append(new_iteration)
            current_iteration = new_iteration

        # TODO: test for convergence, raise error if not met.

        for p1, p2 in zip(iterations_list[-1].periods, self._periods):
            p2.total_heat_flow_to_ground_w = p1.q_ges

        # Store iterations BEFORE updating climate (important!)
        self._iterations = iterations_list
        self._calculation_complete = True

        # Update climate ground temperatures AFTER calculation is marked complete
        self._update_climate_ground_temperatures()

    def _update_climate_ground_temperatures(self) -> None:
        """Update the climate peak load ground temperatures after ground calculations complete.

        This method is called internally after ground heat flow calculations finish.
        """
        # IMPORTANT: Don't use cached_property accessors here - use internal calculation
        # Update peak heating periods
        peak_heating_temp = self._calculate_peak_heating_temp()
        self.phpp.climate.peak_heating_1.temperature_ground_c = peak_heating_temp
        self.phpp.climate.peak_heating_2.temperature_ground_c = peak_heating_temp

        # Update peak cooling periods
        peak_cooling_temp = self._calculate_peak_cooling_temp()
        self.phpp.climate.peak_cooling_1.temperature_ground_c = peak_cooling_temp
        self.phpp.climate.peak_cooling_2.temperature_ground_c = peak_cooling_temp

    def _calculate_peak_heating_temp(self) -> float:
        """Internal calculation method for peak heating ground temperature.

        Called during ground heat flow calculation. Does NOT access cached properties.
        """
        if self.conductance_of_building <= 0:
            return self.min_interior_temp_c

        # Get peak heating period index
        peak_heating_period_idx = self._get_peak_heating_period_index()

        # Access the raw _periods data, not through properties
        heat_flow = self._periods[peak_heating_period_idx].total_heat_flow_to_ground_w

        return self.min_interior_temp_c - heat_flow / self.conductance_of_building

    def _calculate_peak_cooling_temp(self) -> float:
        """Internal calculation method for peak cooling ground temperature.

        Called during ground heat flow calculation. Does NOT access cached properties.
        """
        if self.conductance_of_building <= 0:
            return self.max_interior_temp_c

        # Get peak cooling period index
        peak_cooling_period_idx = self._get_peak_cooling_period_index()

        # Access the raw _periods data, not through properties
        heat_flow = self._periods[peak_cooling_period_idx].total_heat_flow_to_ground_w

        return self.max_interior_temp_c - heat_flow / self.conductance_of_building

    def _get_peak_heating_period_index(self) -> int:
        """Get the period index corresponding to peak heating conditions.

        PHPP V10 | Ground | E202
        """
        # TODO: Implement based on PHPP logic
        # For now, return winter month (January = 0)
        return 0

    def _get_peak_cooling_period_index(self) -> int:
        """Get the period index corresponding to peak cooling conditions.

        PHPP V10 | Ground | I202
        """
        # TODO: Implement based on PHPP logic
        # For now, return summer month (July = 6)
        return 6
